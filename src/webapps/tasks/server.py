from fabric.api import env
from fabric.tasks import Task
from ..models import ServerEnvironment


class PrepareEnvironmentTask(Task):
    """Prepares a named environment on a server
    """
    name = "prepare"

    def run(self, environment_name):
        """Prepares a server for use in the given environment"""
        server = ServerEnvironment(env.webapps_root, environment_name)
        #server.install_dependencies()
        #server.install_key()
