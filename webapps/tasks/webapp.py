from fabric.tasks import Task
from fabric.decorators import task
from fabric.api import env, put, run
from ..models import Webapp, ServerEnvironment

def getWebapp(branch=None):
    server = ServerEnvironment(env.webapps_root)
    return Webapp(server, env.app_name, env.repository, branch)

class WebappTask(Task):
    branch = None

    def run(self, branch=None):
        self.branch = branch
        self.initWebapp()
        self.perform()

    def initWebapp(self):
        self.webapp = getWebapp(self.branch)


class DeployWebappTask(WebappTask):
    """ Deploys the latest version of a Django project from a GIT repository
    """
    name = "deploy"
    def perform(self):
        self.webapp.pull_or_clone()
        self.webapp.switch_branch(self.branch)
        self.webapp.init_and_update_submodules()
        self.webapp.prepare_paths()
        self.webapp.install_requirements()
        self.webapp.install()
        self.webapp.migrate_db()
        #self.webapp.collect_staticfiles()
        self.webapp.reload_or_launch()

@task
def site(operation):
    webapp = getWebapp()
    webapp.site_operation(operation)

class ConfigTask(WebappTask):
    """
    Sets environment config variables
    """
    name = "config"
    def run(self):
        pass

class UploadSettingsTask(WebappTask):
    """
    Uploads file arguments to local settings directory
    """
    name = "upload_settings"
    def run(self, install_name, *args):
        self.initWebapp()
        for f in args:
            put(f, self.webapp.get_settings_dir("local"))
        self.webapp.trigger_reload()

class WatchLogTask(WebappTask):
    """
    Watch the webapp's log
    """
    name = "watch_log"

    def perform(self):
        run("tail -f %s/var/log/webapp.log" % self.webapp.path)
