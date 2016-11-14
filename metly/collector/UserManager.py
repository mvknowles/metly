from metly.client.execute import execute

class UserManager(object):

    def add_user(self, json_user):
        cmd = ["useradd", "-s", "/usr/bin/rssh"]
        execute(cmd)


    def del_user(self, username):
        cmd = ["userdel", "-f", "-r"]
