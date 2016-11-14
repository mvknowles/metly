import re
import sys
import jpype
#import jaydebeapi
import traceback
import phoenixdb
import sqlalchemy

from metly.util import hash
from metly.util.log import log
from metly.model.Base import Base
from metly.model.User import User
from metly.model.Customer import Customer
from metly.model.Requestor import Requestor
from metly.model.WebServer import WebServer
from metly.model.ServiceRequest import ServiceRequest



class Database(object):

    PHOENIX_JAR_PATH = "/usr/local/phoenix/phoenix-4.4.0-HBase-0.98-client.jar"
    PHOENIX_QUERY_SERVER = "http://localhost:8765/"

    def init(self, drop=False, drop_phoenix=False):
        log("Starting db.init", 2)
        self.init_defaults(drop)
        self.init_phoenix_jsonrpc()
        self.init_tables(drop_phoenix)
        log("Finished db.init", 2)

    def init_defaults(self, drop):
        log("Initialising defaults", 3)
        if drop == True:
            log("Dropping database", 3)
            Base.metadata.drop_all(db.engine)

        Base.metadata.create_all(db.engine)

        session = db.Session()
        # make sure all our constants exist etc
        if session.query(Requestor).first() != None:
            log("Defaults already initialised", 3)
            session.close()
            return

        session.add(Requestor("customer"))
        session.add(Requestor("AFP (Australian Federal Police)"))
        session.add(Requestor("NSW Police"))
        session.add(Requestor("Victorian Police"))
        session.add(Requestor("ACC (Australian Crime Comission)"))
        session.add(Requestor("ASIO"))
        session.add(Requestor("DSD"))

        customer = Customer("iinet", "iinet")
        session.add(customer)
        session.add(Customer("internode", "internode"))
        session.add(Customer("telstra", "telstra"))

        user = User()
        user.username = "mark"
        user.firstname = "Mark"
        user.lastname = "Knowles"
        user.email = "mark@mknowles.com.au"
        user.su = True
        user.customer = customer
        user.enabled = True
        user.salt = hash.new_salt()
        user.password = hash.hash_password("test", user.salt)

        session.add(user)

        session.commit()
        session.close()

        log("Done initialising defaults", 3)


    def init_phoenix_jsonrpc(self):

        self.p_conn = phoenixdb.connect(self.PHOENIX_QUERY_SERVER, \
                autocommit=True)

    def init_phoenix_jdbc(self, drop=False):
        log("Initializing Phoenix", 2)
        self.p_conn = jaydebeapi.connect(
                "org.apache.phoenix.jdbc.PhoenixDriver",
                ["jdbc:phoenix:localhost"], self.PHOENIX_JAR_PATH)

        log("Finished initializing Phoenix", 2)

    def init_tables(self, drop_phoenix):
        cursor = self.p_conn.cursor()
        if drop_phoenix == True:
            # TODO: we need to list the customer tables and
            # delete them instead of hardcoding
            try:
                print "dropping phoenix tables"
                cursor.execute("drop table iinet_events")
                cursor.execute("drop sequence iinet_events_sequence")
            except:
                pass

            print "creating tables"
            self.create_event_table("iinet")



    def insert_event(self, event, customer_uuid, customer_short_name):

        # VERY IMPORTANT: jpype needs to be initialized for threads.
        # If we don't do this, we start getting mystery segfaults
        if type(self.p_conn) != phoenixdb.connection.Connection:
            if not jpype.isThreadAttachedToJVM():
                log("Configured jpype for threading", 6)
                jpype.attachThreadToJVM()

        cursor = self.p_conn.cursor()

        if re.search("^\w+$", customer_short_name) == None:
            raise Exception(( \
                    "Invalid customer short name: %s.  " \
                    "Avoiding SQL injection") % customer_short_name)

#        sql = ( "UPSERT INTO %s_events(id, tenant_id, raw, receiptTime, " \
#                "startTime, device_id, collector_id) VALUES ( " \
#                "NEXT VALUE FOR %s_events_sequence, ?, ?, ?, ?, ?, ?)")  % \
#                (customer_short_name, customer_short_name)

#        params = (customer_uuid, event.raw, event.create_dt, event.create_dt, \
#                event.device_id, event.collector_id)

        sql = ( "UPSERT INTO %s_events(id, tenant_id, raw, startTime, " \
                "device_id, collector_id) VALUES ( " \
                "NEXT VALUE FOR %s_events_sequence, ?, ?, to_date(?, 'yyyy-mm-dd'), ?, ?)")  % \
                (customer_short_name, customer_short_name)

        params = (customer_uuid, event.raw,  str(event.create_dt.date()), \
                event.device_id, event.collector_id)

        log("Tables exist, logging normally", 5)
        cursor.execute(sql, params)
        self.p_conn.commit()
        log("Done", 5)

        # JDBC exception handling
#        except jaydebeapi.DatabaseError, ex:
#            if ex.args[0].JAVACLASSNAME == \
#                    "org.apache.phoenix.schema.TableNotFoundException":
#                log("Hadoop table doesn't exist, creating", 4)
#                self.create_event_table(customer_short_name)
#                log("Created table %s_events" % customer_short_name, 4)
#                log("Re-logging event", 4)
#
#                cursor.execute(sql, params)
#                self.p_conn.commit()
#                log("Success", 4)
#
#            else:
#                tb = traceback.format_tb()
#                sys.stderr.write("%s\n" % tb)



    def create_event_table(self, customer_short_name):

        # Even though we're making this multi-tenant, we still keep the
        # various customers seperated by namespace.  It's for security
        # reasons that we use multi-tenant as it isolates the current
        # tenant when querying from the web frontend (using the TenantID
        # JDBC param

        # TODO: figure out where we put this
        fh = open("/Users/mark/Documents/SCM/metly/data/create_event_table.sql", "r")

        sql_lines = []
        for line in fh:
            line = line.strip()
            if line.startswith("#") or len(line) == 0:
                continue

            sql_lines.append(line)

        sql = "\n".join(sql_lines)

        sql = sql% customer_short_name

        log("Create SQL:\n%s" % sql, 5)
        cursor = self.p_conn.cursor()
        cursor.execute(sql)

        sql = "CREATE SEQUENCE %s_events_sequence" % customer_short_name
        log("Sequence SQL: %s" % sql, 5)
        cursor.execute(sql)
        self.p_conn.commit()

    def create_results_table(self):

        # Even though we're making this multi-tenant, we still keep the
        # various customers seperated by namespace.  It's for security
        # reasons that we use multi-tenant as it isolates the current
        # tenant when querying from the web frontend (using the TenantID
        # JDBC param

        # TODO: figure out where we put this
        fh = open("/Users/mark/Documents/SCM/metly/data/create_results_table.sql", "r")

        sql_lines = []
        for line in fh:
            line = line.strip()
            if line.startswith("#") or len(line) == 0:
                continue

            sql_lines.append(line)

        sql = "\n".join(sql_lines)

        log("Create SQL:\n%s" % sql, 5)
        cursor = self.p_conn.cursor()
        cursor.execute(sql)

#        sql = "CREATE SEQUENCE %s_events_sequence" % customer_short_name
#        log("Sequence SQL: %s" % sql, 5)
#        cursor.execute(sql)
#        self.p_conn.commit()


db = Database()


