import datetime
from Parser import Parser
from LineParser import LineParser

class SquidParser(LineParser):

    SUPPORTED_FORMATS = ["squid"]

    NATIVE_FORMAT = ("time elapsed remotehost code/status bytes method URL " \
            "rfc931 peerstatus/peerhost type")

    #TODO: do the end_time field

    def parse_line(self, data):
        line = data["event"]["raw"]
        log_source_name = data["log_source_name"]

        fields = line.split()
        i = 0
        event = Event()
        for field_name in self.NATIVE_FORMAT:
            parse_fn, dest_field = self.FIELD_PARSERS[field_name]
            parse_fn(field[i], dest_field, event)
            i += 1

        self.log_writer.insert_row(self.customer_short_name, \
                self.event.device_hostname, log_source_name, \
                self.event.to_dict())

    @staticmethod
    def parse_code_status(unparsed_value, dest_field, event):
        event.code, event.status = unparsed_value.split("/")

    @staticmethod
    def parse_bytes(unparsed_value, dest_field, event):
        event.bytes_in = unparsed_value
        events.bytes_out = unparsed_value

    FIELD_PARSERS = { \
            "time": (Parser.parse_unix_timestamp, "start_time"), \
            "elapsed": (Parser.parse_int, "duration"), \
            "remotehost": (Parser.parse_ip, "source_ip"), \
            "code/status": (parse_code_status, None), \
            "bytes": (parse_bytes, None), \
            "method": (Parser.parse_string, "method"), \
            "URL": (Parser.parse_uri, "destination_uri"), \
            "rfc931": (Parser.parse_string, "source_username"), \
            "peerstatus": (Parser.parse_string, "extra_0"), \
            "type": (Parser.parse_string, "content_type")
    }
