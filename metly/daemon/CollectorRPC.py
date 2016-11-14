import os
import json
import time
import uuid
import binascii
import sqlalchemy
from twisted.web.resource import Resource

from db import db
from JSONRPCServer import JSONRPCServer
#from rpc.FilesystemLogSourceRPC import FilesystemLogSourceRPC

from metly.util.log import log
from metly.util import constants
from metly.model.Upload import Upload
from metly.model.Collector import Collector
from metly.model.LogSource import LogSource
from metly.exception.CollectorNotRegisteredException \
         import CollectorNotRegisteredException

from metly.exception.UploadCorruptedException import UploadCorruptedException
from metly.exception.UploadOutOfOrderException import UploadOutOfOrderException

class CollectorRPC(JSONRPCServer):

    ISSUED_EXTENSIONS = "client"
    CN_SUFFIX = constants.COLLECTOR_CERT_CN_SUFFIX

    def __init__(self, ca, root_ca_cert_path, log_manager, command_and_control):
        JSONRPCServer.__init__(self, ca, root_ca_cert_path)
        self.log_manager = log_manager
        self.command_and_control = command_and_control
        self.authorized_collectors = {}

        #self.modules["fs_logsource"] = FilesystemLogSourceRPC()

    def json_cc_loop(self, request):
        uuid = self.cn_to_uuid(self.peer_cert.get_subject().commonName)
        return self.command_and_control.get_next_command(request, uuid)

    def json_shutdown(self, request):
        uuid = self.cn_to_uuid(self.peer_cert.get_subject().commonName)
        self.command_and_control.queue_command(uuid, "shutdown")


    def json_register(self, request):
        uuid = self.cn_to_uuid(self.peer_cert.get_subject().commonName)
        print "Register.  UUID: %s" % (uuid)
        session = db.Session()

        try:
            try:
                session.query(Collector).filter(Collector.uuid==uuid).one()
            except sqlalchemy.orm.exc.NoResultFound:
                # create a database object for the collector
                collector = Collector()
                collector.uuid = uuid
                session.add(collector)
                session.commit()
        finally:
            session.close()

        return json.dumps({"uuid": uuid})


    def json_get_sources_config(self, request):
        session = db.Session()

        try:
            uuid = self.cn_to_uuid(self.peer_cert.get_subject().commonName)
            collector = session.query(Collector)\
                    .filter(Collector.uuid==uuid).one()

            log_sources = session.query(LogSource)\
                    .filter(LogSource.collector_id==collector.id)

            json_log_sources = []
            for log_source in log_sources:
                json_log_source = {"name": log_source.name, \
                        "id": log_source.id, \
                        "log_source_type": log_source.log_source_type.short_name}

                json_params = {}
                for param_name, param in log_source.parameters.items():
                    json_params[param_name] = param.value

                json_log_source["parameters"] = json_params

                json_log_sources.append(json_log_source)

            print json.dumps(json_log_sources, indent=4)
            return json.dumps(json_log_sources, indent=4)


        finally:
            session.close()


    def json_log(self, request):
        try:
#            event = request.json["event"]
#            host = request.json["host"]
            collector_cn = self.peer_cert.get_subject().commonName
            collector_uuid = self.cn_to_uuid(collector_cn)
            self.log_manager.log(request.json, collector_uuid)
        except CollectorNotRegisteredException:
            print "RAISED CNRE"
            return json.dumps({"error": "CollectorNotRegisteredException"})

        return ""


    def get_collector(self):
        collector_cn = self.peer_cert.get_subject().commonName
        collector_uuid = self.cn_to_uuid(collector_cn)
        return self.session.query(Collector)\
                .filter(Collector.uuid==collector_uuid).one()


    def json_upload_start(self, request):

        self.session = db.Session()

        try:
            collector = self.get_collector()

            upload = Upload()
            upload.original_path = request.json["original_path"]
            upload.collector_id = collector.id

            # commit so we can get upload.id
            self.session.add(upload)
            self.session.commit()

            upload.path = os.path.join(self.log_path, \
                    upload.collector.customer.get_safe_short_name(), \
                    "upload", "%d.ul" % (upload.id))
            upload_dir = os.path.dirname(upload.path)
            if os.path.exists(upload_dir) == False:
                os.makedirs(upload_dir)

            self.session.commit()

            return json.dumps({"upload_id": upload.id})

        finally:
            self.session.close()


    def post_binary_part(self, request, field_storage):

        #TODO: we really need to cache the upload object

        json_data = json.loads(field_storage["json_data"].file.read())
        data = field_storage["file"].file.read()

        session = db.Session()

        try:
            upload = session.query(Upload)\
                     .filter(Upload.id==int(json_data["upload_id"])).one()

            # make sure segments are in order
            if upload.parts != int(json_data["part_number"]):
                raise UploadOutOfOrderException(
                        "Expected part number %d" % (upload.parts))

            upload.parts += 1

            if upload.crc == None:
                upload.crc = binascii.crc32(data)
            else:
                upload.crc = binascii.crc32(data, upload.crc)

            fh = open(upload.path, "ab")
            fh.write(data)
            fh.close()

            session.add(upload)
            session.commit()

        finally:
            session.close()

        request.send_headers(200)
        request.end_headers()
        request.wfile.write(json.dumps({}))


    def json_upload_finish(self, request):
        session = db.Session()

        try:
            upload_id = int(request.json["upload_id"])
            upload = session.query(Upload).filter(Upload.id==upload_id).one()
            upload.finished = True
            expected_crc = request.json["crc"]

            if upload.crc != expected_crc:
                raise UploadCorruptException("Wrong CRC")

            print upload.crc

            session.add(upload)
            session.commit()

        finally:
            self.session.close()


#    def json_get_unfinished_uploads(self, request):
#        session = db.Session()
#
#        try:
#            uploads = session.query(Upload).filter(Upload.finished==False).all()
#
#
#            for upload in uploads:
#                json_upload = {"path": upload.original_path}
#                json_data

    def is_authorized(self, collector_uuid):

        collector = None

        if collector_uuid in self.authorized_collectors.keys():
            collector = self.authorized_collectors[collector_uuid]
        else:
            self.refresh_authorized_collectors()
            if collector_uuid in self.authorized_collectors.keys():
                collector = self.authorized_collectors[collector_uuid]

        if collector == None:
            return False

        if collector.customer_id == None:
            return False
        else:
            return True

    def refresh_authorized_collectors(self):
        log("Populating authorized collector uuids, uuid follow", 5)
        try:
            session = db.Session()
            collectors = session.query(Collector)\
                    .filter(Collector.customer_id!=None).all()

            for collector in collectors:
                self.authorized_collectors[collector.uuid] = collector
                log(collector.uuid, 5)

            log("EOL", 5)
        finally:
            session.close()

