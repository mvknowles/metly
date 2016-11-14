from metly.model.Event import Event

class DatabaseLogWriter(LogWriter):

    def impl_insert_row(self, customer_shortname, host, log_source_name, \
            event_dict, dt):

        event = Event()
        event.__tablename__ == "testtablename"

        for key, value in event_dict.items():
            if not hasattr(event, key):
                raise Exception("Invalid event field found in dictionary: %s" \
                        % key)

            setattr(event, key, value)

        session = db.Session()

        try:
            session.add(event)
            session.commit()

        finally:
            session.close()
