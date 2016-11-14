import os
import shutil
import subprocess

class CertUtil(object):

    @staticmethod
    def create_csr(subject, key_file):
        #TODO: Security: check that subject gets escaped properly
        openssl_cmd = ["openssl", "req", "-new", "-nodes", "-subj", subject, \
                "-keyout", key_file]

        openssl_proc = subprocess.Popen(openssl_cmd, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        stdout_data, stderr_data = openssl_proc.communicate()

        retcode = openssl_proc.wait()
        if retcode != 0:
            raise Exception("Openssl returned non-zero: " + stderr_data)

        return stdout_data


    @staticmethod
    def create_self_signed_cert(subject, key_file, cert_file):
        #TODO: Security: check that subject gets escaped properly
        openssl_cmd = ["openssl", "req", "-new", "-nodes", "-subj", subject, \
                "-keyout", key_file]
        openssl_cmd = ["openssl", "req", "-x509", "-newkey", "rsa:2048", \
                "-keyout", key_file, "-out", cert_file, "-days", "99999", \
                "-nodes", "-subj", subject]

        openssl_proc = subprocess.Popen(openssl_cmd, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        stdout_data, stderr_data = openssl_proc.communicate()

        retcode = openssl_proc.wait()
        if retcode != 0:
            raise Exception("Openssl returned non-zero: " + stderr_data)

