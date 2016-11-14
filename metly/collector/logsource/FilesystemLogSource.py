from LogSource import LogSource

import os
import bz2
import glob
import json
import hashlib
import mimetypes

class FilesystemLogSource(LogSource):

    NAME = "filesystem"

    def __init__(self, *args, **kwargs):
        LogSource.__init__(self, *args, **kwargs)
        self.glob = None

    def run(self):
        while self.is_running() == True:
            print "Filesystem log source checking for files"
            self.sleep(60)


    def get_file_infos(self):
        file_infos = []

        for path in glob.glob(self.glob):
            file_info = self.get_file_info(path)
            file_infos.append(file_info)

        return file_infos

    def get_file_info(self, path):
        return FileInfo(path)


class FileInfo(object):


    def __init__(self, path):
        # I thought about simply storing the stat, but it doesn't serialize
        # easily due to being a type that's initialized from a struct
        s = os.stat(path)
        self.inode = s.st_ino
        self.size = s.st_size
        self.mod_time = s.st_mtime
        self.access_time = s.st_atime
        self.digest = None

#    def from_json(self, data):
#        , inode, size, mod_time, upload_id, digest):
#
#
#        self.path = data["path"]
#        self.inode = int(inode)
#        self.size = int(size)
#        self.mod_time = float(mod_time)
#        self.upload_id = int(upload_id)
#        self.digest = digest


class Peanut():

    def open(self):
        mt = mimetypes.guess_type(self.path)

        if mt == (None, "gzip"):
            self.fh = gzip.GzipFile(self.path, "r")
        elif mt == (None, "bzip2"):
            self.fh = bz2.BZ2File(self.path, "r")
        elif mt == ("text/plain", None):
            self.fh = open(self.path, "r")
        else:
            raise Exception("Unknown mime type")


    def content_has_changed(self):
        s = os.stat(path)
        
        if s.ino == self.inode:
            return True

        if s.st_size != self.size:
            return True

#        if s.st_mtime != self.mod_time:
#            return True

        return False


    def file_has_moved(self):
        s = os.stat(path)

        return s.ino != self.inode


if __name__ == "__main__":
    fi = FilesystemLogSource(None, None)
    fi.glob = "/var/log/system.log*"
    fis = fi.get_file_infos()

    print json.dumps(fis)
