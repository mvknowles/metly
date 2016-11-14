import os
import glob
import json
import datetime
 
class LogReader(object):
    def __init__(self, log_path, customer_short_name, start_dt=None, \
            finish_dt=None):

        self.log_path = log_path
        self.customer_short_name = customer_short_name
        self.start_dt = start_dt
        self.finish_dt = finish_dt
        self.cache = {}
        self.fhs = []

        first_dt, last_dt = self.find_date_extremeties()

        if self.start_dt == None:
            self.start_dt = first_dt

        if self.finish_dt == None:
            self.finish_dt = last_dt

        print "LogReader init, start_dt=%s, finish_dt=%s" % (start_dt, finish_dt)

        self.current_dt = None


    def next(self):
        if len(self.cache.keys()) == 0:
            # we've run out of logs for the current hour, load the next batch
            for fh in self.fhs:
                fh.close()

            # load in a batch of new file handles
            while True:
                if self.current_dt == None:
                    self.current_dt = self.start_dt
                else:
                    self.current_dt = self.current_dt + \
                            datetime.timedelta(hours=1)

                    if self.eof() == True:
                        return None

                self.fhs = self.open_logs(self.current_dt)

                if len(self.fhs) != 0:
                    break

            for fh in self.fhs:
                json_dict = json.loads(self.read_line(fh))
                self.cache[fh] = json_dict

        min_dt = None
        min_fh = None
        for fh, json_dict in self.cache.items():
            if min_dt == None or json_dict["create_dt"] < min_dt:
                min_dt = json_dict["create_dt"]
                min_fh = fh


        event = self.cache[min_fh]

        next_line = self.read_line(min_fh)
        if next_line == None:
            del self.cache[min_fh]
        else:
            data = json.loads(next_line)
            self.cache[min_fh] = data

        return event

    def eof(self):
        return self.current_dt > self.finish_dt


    def read_line(self, fh):
        for line in fh:
            return line


    def open_logs(self, dt):
#        self.current_dt = self.current_dt + datetime.timedelta(hours=1)

        date_comp = datetime.datetime.strftime(dt, "%Y-%m-%d")
        date_dir = os.path.join(self.log_path, self.customer_short_name, \
                "logs", date_comp)

        hour_comp = datetime.datetime.strftime(dt, "%H")

        fhs = []
        print "Opening logs for dt=%s dir=%s/%s.*" % \
                (str(dt), date_dir, hour_comp)
        for log_file in glob.glob("%s/*/%s.*" % (date_dir, hour_comp)):
            print "Found log file %s" % log_file
            fh = open(log_file, "r")
            fhs.append(fh)

        print "opened %d files" % len(fhs)
        return fhs 


    def find_date_extremeties(self):
        logs_dir = os.path.join(self.log_path, self.customer_short_name, \
                "logs")

        first_dt = None
        last_dt = None
        for date_dir in os.listdir(logs_dir):
            parsed_dt = datetime.datetime.strptime(date_dir, "%Y-%m-%d")

            if last_dt == None or parsed_dt > last_dt:
                # we add a day to ensure we get the full 24 hours of the day
                last_dt = parsed_dt + datetime.timedelta(days=1)

            if first_dt == None or parsed_dt < first_dt:
                first_dt = parsed_dt

        return first_dt, last_dt


if __name__ == "__main__":
    lr = LogReader("/tmp/logs", "iinet", None, datetime.datetime(2015, 9, 4))
    while True:
        line = lr.next()
        if line == None:
            break

        print line
