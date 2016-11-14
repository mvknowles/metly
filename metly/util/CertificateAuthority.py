import os
import shutil
import subprocess

class CertificateAuthority(object):

    def __init__(self, ca_path, ca_skel_path):
        self.ca_path = ca_path
        self.ca_key_path = os.path.join(ca_path, "private/ca.key")
        self.ca_cert_path = os.path.join(ca_path, "certs/ca.crt")
        self.ca_skel_path = ca_skel_path

    def create_ca(self, subject):
        if os.path.exists(self.ca_path):
            raise Exception("That directory already exists.")

        shutil.copytree(self.ca_skel_path, self.ca_path)
        openssl_cmd = ["openssl", "req", "-nodes", "-new", "-x509", "-subj", \
                subject, "-extensions", "v3_ca", "-keyout", "private/ca.key", \
                "-out", "certs/ca.crt", "-days", "9999", "-config", \
                "openssl.cnf"]

        openssl_proc = subprocess.Popen(openssl_cmd, cwd=self.ca_path, \
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_data, stderr_data = openssl_proc.communicate()

        retcode = openssl_proc.wait()
        if retcode != 0:
            raise Exception("Openssl returned non-zero: " + stderr_data)

    def sign_csr(self, csr, extensions=None):
        #TODO:
        #Look for this error, it signifies two conflicting CNs
        #We should implement database lookups to ensure non-conflicts
        #failed to update database
        #TXT_DB error number 2

        openssl_cmd = ["openssl", "ca", "-batch"]

        if extensions != None:
            openssl_cmd.append("-extensions")
            openssl_cmd.append(extensions)

        openssl_cmd.extend(["-config", "openssl.cnf", "-in", "/dev/stdin"])
        print openssl_cmd

        openssl_proc = subprocess.Popen(openssl_cmd, cwd=self.ca_path, \
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, \
                stdin=subprocess.PIPE)
        stdout_data, stderr_data = openssl_proc.communicate(csr)


        retcode = openssl_proc.wait()
        if retcode != 0:
            raise Exception("Openssl returned non-zero: " + stderr_data)

        return stdout_data


