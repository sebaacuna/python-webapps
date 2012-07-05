from fabric.api import *

class SshAgentRunner(object):
    """
    Note:: Fabric (and paramiko) can't forward your SSH agent.
    This helper uses your system's ssh to do so.
    """
    def __init__(self, user, host, port):
        self.host = host
        self.port = port

    def run(self, cmd):
        wrapped_cmd = _prefix_commands(_prefix_env_vars(cmd), 'remote')
        cmd_parts = {
                "user": self.user,
                "host" : self.host,
                "port" : self.port,
                "cmd" : wrapped_cmd
            }
        main_template = "ssh -p %(port)s -A %(user)s@%(host)s '%(cmd)s'"
        alt_template = "ssh -A %(user)s@%(host)s:%(port)s '%(cmd)s'"

        try:
            return local(main_template % cmd_parts)
        except ValueError:
            return local(alt_template % cmd_parts)
