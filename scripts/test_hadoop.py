#!/usr/bin/env python

import sys
import random
import datetime
import jaydebeapi

class TestHadoop(object):

    def __init__(self):
        self.test_multi_tenant()

    def connect(self, tenant_id=None):
        uri = "jdbc:phoenix:localhost"

        if tenant_id != None:
            uri = "%s;TenantId=%s" % (uri, tenant_id)

        print uri

        self.conn = jaydebeapi.connect("org.apache.phoenix.jdbc.PhoenixDriver",\
                [uri], "/usr/local/phoenix/phoenix-4.4.0-HBase-0.98-client.jar")

    def test_multi_tenant(self):
        self.connect()
        cursor = self.conn.cursor()

        drop = False

        if drop == True:
            try:
                sql = "DROP TABLE g.events"
                print sql
                cursor.execute(sql)
            except:
                pass

        cursor = self.conn.cursor()

        sql = ("CREATE TABLE if not exists iinet.events ("
                "tenant_id VARCHAR not null, "
                "event_id BIGINT not null, "
                "raw varchar(255), "
                "constraint ik primary key (tenant_id, event_id)) "
                "MULTI_TENANT=true")

        print sql
        cursor.execute(sql)
        self.conn.commit()
        self.conn.close()

        self.test_tenant("iinet")
        self.test_tenant("telstra")

    def test_tenant(self, name):
        self.connect(tenant_id=name)
        cursor = self.conn.cursor()

        sql = ("UPSERT INTO g.events(tenant_id, event_id, raw) VALUES "
                "(?, ?, ?)")
#        sql = ("UPSERT INTO g.events(event_id, raw) VALUES "
#                "(?, ?)")
        print sql
        cursor.execute(sql, ("iinet", random.randint(1,1000), \
                    "hello event for %s" % name))
        self.conn.commit()

        sql = "SELECT * from g.events" 
        print sql
        cursor.execute(sql)
        print "%s rows" % name
        for row in cursor.fetchall():
            print row

        self.conn.close()

    def select_events(self):
        self.connect()
        cursor = self.conn.cursor()

        cursor.execute("select * from g.events")
        for event in cursor.fetchall():
            print str(event[0]),
            print str(event[1])

    def test_event_table(self):
        self.connect()
        cursor = self.conn.cursor()

        customer_short_name = "testisp"
        cursor.execute("drop table %s_events" % customer_short_name)
        sql = ( "create table %s_events " \
                "(id integer not null primary key, " \
                "raw varbinary, " \
                "create_dt timestamp, " \
                "device_dt timestamp, " \
                "device_id unsigned_int, " \
                "collector_id unsigned_int)") % \
                customer_short_name

        cursor.execute(sql)

        params = (1, u'<13>Jul 14 22:44:00 karma root: hello', \
                datetime.datetime(2015, 7, 14, 22, 44, 0, 927555).strftime("%Y-%m-%d %H:%M:%S.%f"), \
                None, 1, 2)

        sql = ( \
                "upsert into %s_events(id, raw, create_dt, device_dt, " \
                "device_id, collector_id) values (?, ?, ?, ?, ?, ?)") % \
                customer_short_name

        cursor.execute(sql, params)
        conn.commit()

if __name__ == "__main__":
    TestHadoop()
