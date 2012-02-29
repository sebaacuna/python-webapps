from fabric.tasks import Task
from fabric.api import env, put, run
from ..models import Webapp, ServerEnvironment


class WebappTask(Task):
    branch = None

    def run(self, environment_name, install_name, branch=None):
        self.branch = branch
        self.initWebapp(environment_name, install_name)
        self.perform()

    def initWebapp(self, environment_name, install_name):
        server = ServerEnvironment(env.webapps_root, environment_name)
        self.webapp = Webapp(server, install_name, env.repository, self.branch)


class DeployWebappTask(WebappTask):
    """ Deploys a Django project from a GIT repository
    """
    name = "deploy"
    def perform(self):
        self.webapp.pull_or_clone()
        self.webapp.switch_branch(self.branch)
        self.webapp.install_requirements()
        self.webapp.install()
        #webapp.collect_staticfiles()
        #webapp.fetch_configuration()

class UpdateWebappTask(WebappTask):
    """ Updates a deployed django project"""
    name = "update"

    def perform(self):
        self.webapp.pull_or_clone()
        self.webapp.switch_branch(self.branch)


class ConfigureWebappTask(WebappTask):
    """
    Installs server configs
    """
    name = "config"

    def perform(self):
        self.webapp.customize_server_configs()
        self.webapp.deploy_vhost()

class UploadSettingsTask(WebappTask):
    """
    Uploads file arguments to local settings directory
    """
    name = "upload_settings"
    def run(self, environment_name, install_name, *args):
        self.initWebapp(environment_name, install_name)
        for f in args:
            put(f, self.webapp.get_settings_dir("local"))

class WatchLogTask(WebappTask):
    """
    Watch the webapp's log
    """
    name = "watch_log"

    def perform(self):
        run("tail -f %s/var/log/webapp.log" % self.webapp.path)
