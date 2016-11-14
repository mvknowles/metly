import datetime

class Parser(object):

    def __init__(self, customer, log_writer):
        self.customer = customer
        self.customer_short_name = customer.get_safe_short_name()
        self.log_writer = log_writer

    @staticmethod
    def parse_unix_timestamp(unparsed_value, dest_field, event):
        dt = datetime.datetime.fromtimestamp(float(unparsed_value))
        setattr(event, dest_field, dt)

    @staticmethod
    def parse_string(unparsed_value, dest_field, event):
        setattr(event, dest_field, unparsed_value)
        
    parse_int = parse_string
    parse_ip = parse_string
    parse_uri = parse_string
