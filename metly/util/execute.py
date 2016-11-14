import subprocess

def execute(cmd):
        cmd = ["service", "sshd", "start"]

        proc = subprocess.Popen(cmd, cwd=self.ca_path, \
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, \
                stdin=subprocess.PIPE)  
        stdout_data, stderr_data = proc.communicate()

        retcode = proc.wait()
        if retcode != 0:
            raise Exception("Command %s returned non-zero: %s" % \
                    (" ".join(cmd), stderr_data))
