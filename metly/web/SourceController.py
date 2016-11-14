import os
import cherrypy
import sqlalchemy
from formencode import Schema
from formencode import Invalid
from formencode import validators
from genshi.filters import HTMLFormFiller

import template
from Controller import Controller
from metly.model.Device import Device
from metly.model.Network import Network
from metly.model.Collector import Collector
from metly.model.LogSource import LogSource
from metly.model.LogSourceType import LogSourceType
from metly.model.LogSourceParameter import LogSourceParameter

class LogSourceValidator(Schema):
    name = validators.UnicodeString(not_empty=True)
    collector_id = validators.Int(not_empty=True)
    log_source_type = validators.UnicodeString(not_empty=True)
    allow_extra_fields=True


class SyslogLogSourceValidator(LogSourceValidator):
    port = validators.Int(not_empty=True)
    protocol = validators.OneOf(["udp", "tcp"])


class FilesystemLogSourceValidator(LogSourceValidator):
    path = validators.UnicodeString(not_empty=True)
    format = validators.UnicodeString(not_empty=True)


class LogFormatValidator(Schema):
    allow_extra_fields=True

class DeviceLogFormatValidator(LogFormatValidator):
    ip_address = validators.UnicodeString(if_missing=None)
    fqdn = validators.UnicodeString(if_missing=None)
    # must specifiy either or
    chained_validators = [ \
            validators.RequireIfMissing("ip_address", missing="fqdn"),
            validators.RequireIfMissing("fqdn", missing="ip_address")
    ]


class SquidLogFormatValidator(DeviceLogFormatValidator):
    custom_format = validators.UnicodeString(if_missing=None)


class Format(object):
    def __init__(self, name, short_name, validator):
        self.name = name
        self.short_name = short_name
        self.validator = validator


class SourceController(Controller):

    TYPE_VALIDATORS = {
            "syslog": SyslogLogSourceValidator,
            "filesystem": FilesystemLogSourceValidator
    }

    FORMATS = {
            "squid": Format("Squid", "squid", SquidLogFormatValidator)
    }

    def __init__(self, server_rpc):
        Controller.__init__(self, server_rpc)


    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPRedirect("/src/list")



    @cherrypy.expose
    @template.output("new_source.html")
    def new(self, **data):
        errors = {}
        self.session = self.Session()

        # the default type to choose if none has been submitted yet
        log_source_type_name = "syslog"
        # format is only chosen for specific types, such as filesystem
        log_source_format_name = None

        try:

            if cherrypy.request.method == "POST":

                try:
                    validator = self.TYPE_VALIDATORS[data["log_source_type"]]
                    form_data = validator.to_python(data)
                    user = cherrypy.session["user"]

                    # find the log source type
                    short_name = form_data["log_source_type"]
                    log_source_type = self.session.query(LogSourceType)\
                            .filter(LogSourceType.short_name==short_name).one()

                    collector = self.session.query(Collector)\
                            .filter(Collector.id==form_data["collector_id"]).one()

                    # ensure that the user is dealing with their own collector
                    if collector.customer_id != user.customer_id:
                        return "Security error"

                    log_source = LogSource()
                    log_source.customer_id = user.customer_id
                    log_source.name = form_data["name"]
                    log_source.log_source_type_id = log_source_type.id
                    log_source.collector_id = collector.id
                    log_source.collector = collector

                    add_attr_fn = self.add_attr_fn(form_data["log_source_type"])
                    add_attr_fn(log_source, form_data)

                    if "format" in form_data:
                        log_source_format_name = form_data["format"]
                        format_validator = self.FORMATS[data["format"]].validator
                        format_form_data = format_validator.to_python(data)
                        add_attr_fn = self.add_attr_fn(log_source_format_name)
                        add_attr_fn(log_source, format_form_data)

                    self.session.add(log_source)
                    self.session.commit()

                    self.server_rpc.json_rpc("update_log_source", \
                            id=log_source.id, collector_uuid=collector.uuid)

                    raise cherrypy.HTTPRedirect("/src/list")

                except Invalid, ex:
                    errors = ex.error_dict
                    print errors

            collectors = self.session.query(Collector).all()
            log_source_types = self.session.query(LogSourceType).all()

        finally:
            self.session.close()

        # see if a format has been specified yet. If so, include it in the
        # response
        if "format" in data and len(data["format"]) != 0:
            format_form_path = self.get_format_form_path(data["format"])
        else:
            format_form_path = None

        if "log_source_type" in data:
            log_source_type_name = data["log_source_type"]
        type_form_path = self.get_type_form_path(log_source_type_name)

        return template.render(errors=errors, collectors=collectors, \
                log_source_types=log_source_types, \
                formats=self.FORMATS.values(), \
                type_form_path=type_form_path, \
                format_form_path=format_form_path) | HTMLFormFiller(data=data)

    @cherrypy.expose
    def delete(self, log_source_id):
        session = self.Session()

        try:
            log_source = session.query(LogSource)\
                    .filter(LogSource.id==log_source_id).one()

            #ensure that they own the log source
            user = cherrypy.session["user"]
            if log_source.customer_id != user.customer_id:
                raise Exception("Security exception")

            session.delete(log_source)
            session.commit()
        finally:
            session.close()


    def get_type_form_path(self, short_name):
        # check the validity of the data
        if short_name not in self.TYPE_VALIDATORS.keys():
            raise Exception("Security exception")

        return os.path.join("source_type_forms", \
                "%s.html" % short_name) #self.SOURCE_TEMPLATES[short_name])

    def get_format_form_path(self, short_name):
        # check the validity of the data
        if short_name not in self.FORMATS.keys():
            raise Exception("Security exception")

        return os.path.join("source_format_forms", \
                "%s.html" % short_name) #self.FORMAT_TEMPLATES[short_name])

    @cherrypy.expose
    def type_forms(self, short_name):
        session = self.Session()
        try:
            html_file = self.get_type_form_path(short_name)
            tmpl = template.loader.load(html_file)
            return tmpl.generate(errors={}, formats=self.FORMATS.values())\
                    .render("html", doctype="html")
        finally:
            session.close()

    @cherrypy.expose
    def format_forms(self, short_name):
        html_file = self.get_format_form_path(short_name)
        tmpl = template.loader.load(html_file)
        return tmpl.generate(errors={}).render("html", doctype="html")

#    @cherrypy.expose
#    def edit(self, collector_id):
#        collector_id = int(collector_id)
#
#        # look up the collector
#        session = self.Session()
#
#        try:
#            user = cherrypy.session["user"]
#            session.add(user)
#            collector = session.query(Collector)\
#                    .filter(Collector.id==collector_id).one()
#
#            # ensure that the user "owns" the collector
#            if collector.customer_id != user.customer_id:
#                raise Exception("Attack detected")
#
#            cherrypy.session["collector"] = collector
#        
#        finally:
#            session.close()
#
#        raise cherrypy.HTTPRedirect("/col/new")


    @cherrypy.expose
    @template.output("sources.html")
    def list(self):
        session = self.Session()

        try:
            user = cherrypy.session["user"]
            session.add(user)
            log_sources = session.query(LogSource)\
                    .filter(LogSource.customer_id==user.customer_id)

            return template.render(log_sources=log_sources, url=cherrypy.url)

        finally:
            session.close()

    def add_attr_fn(self, name):
        return getattr(self, "add_%s_attrs" % name)

    def add_syslog_attrs(self, log_source, form_data):
        log_source.parameters["port"] = \
                LogSourceParameter("port", str(form_data["port"]))
        log_source.parameters["protocol"] = \
                LogSourceParameter("protocol", str(form_data["protocol"]))
        log_source.parameters["format"] = \
                LogSourceParameter("format", "syslog")

    def add_filesystem_attrs(self, log_source, form_data):
        log_source.parameters["path"] = \
                LogSourceParameter("path", form_data["path"])
        log_source.parameters["format"] = \
                LogSourceParameter("format", form_data["format"])

    def add_squid_attrs(self, log_source, form_data):
        log_source.parameters["ip_address"] = \
                LogSourceParameter("ip_address", form_data["ip_address"])
        log_source.parameters["fqdn"] = \
                LogSourceParameter("fqdn", form_data["fqdn"])

        device = Device()
        device.ip_address = form_data["ip_address"]
        device.fqdn = form_data["fqdn"]

        collector = log_source.collector

        # TODO: enable multiple network support once we need it
        network = self.session.query(Network)\
                .filter(Network.customer_id==collector.customer_id)\
                .filter(Network.name=="Default").one()

        device.network = network
        self.session.add(device)
