import binascii

class FileUploader(object):

    CHUNK_SIZE = 1024 * 1024 * 10

    def __init__(self, mc):
        self.mc = mc


#    def resume(self):
#        json_data = self.mc.json_rpc("get_unfinished_uploads")



    def upload(self, path):
        fh = open(path, "rb")

        # move the file to the processing folder
        #TODO
        processing_path = path

        # get the file metadata
        json_data = self.mc.json_rpc("upload_start", original_path=path)
        upload_id = json_data["upload_id"]
        print upload_id

        crc = None
        part_number = 0
        while True:
            buf = fh.read(self.CHUNK_SIZE)

            if len(buf) == 0:
                break

            if crc == None:
                crc = binascii.crc32(buf)
            else:
                crc = binascii.crc32(buf, crc)

            self.mc.post_binary_part(upload_id, part_number, buf)
            part_number += 1
                
        print crc
        json_data = self.mc.json_rpc("upload_finish", upload_id=upload_id, \
                crc=crc)
