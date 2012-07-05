from fabric.api import *
from fabric.contrib import files
from os import path
from db_driver import init_db_selective


class Webapp(object):
    def __init__(self, server, name, repository, branch):
        self.server = server
        self.name = name
        self.repository = repository
        self.project_name = self.extract_project_name(repository)
        self.branch = None

    @property
    def path(self):
        return path.join(self.server.root_dir, self.name)
        
    def virtualenv_run(self, cmd):
        return run('source %s/bin/activate && %s' % (self.path, cmd))

    def extract_project_name(self, repository):
        project_name, ext = path.splitext(path.basename(repository))
        return project_name

    def prepare_paths(self):
        map(self.mkdir, [
            self.get_src_path(),
            self.get_conf_path(),
            "%s/.ssh" % self.path,
            "%s/var/log" % self.path,
            ])
        run("chmod -R +rwX %s/.ssh" % self.path)
        if not files.exists("%s/bin/activate" % self.path):
            run("virtualenv %s" % self.path)

    def mkdir(self, path):
        run("mkdir -p %s" % path)

    def copy_server_key(self, server):
        with cd("%s/.ssh" % self.path):
            source = server.get_key_path()
            server_key = self.get_server_key()
            run("cp %s %s" % (source, server_key))
            run("chmod 0600 %s" % server_key)

    def get_server_key(self):
        return "%s/.ssh/server_key" % self.path

    def pull_or_clone(self):
        if files.exists(self.get_src_path()):
            with cd(self.get_src_path()):
                self.run_git("pull")
        else:
            self.run_git("clone %s %s" % (self.repository, self.get_src_path()) )
    
    def init_and_update_submodules(self):
        with cd(self.get_src_path()):
            self.run_git("submodule init")
            self.run_git("submodule update")

    def switch_branch(self, branch):
        self.branch = branch
        if self.branch is not None:
            with cd(self.get_src_path()):
                self.run_git("checkout %s" % self.branch)

    def install_requirements(self):
        with cd(self.get_src_path()):
            with hide("stdout"):
                self.virtualenv_run('yes w | pip install -r requirements.txt')

    def install(self):
        self.prepare_paths()
        with cd(self.path):
            self.virtualenv_run("pip install -e %s --force-reinstall" % self.get_src_path())

    def init_db(self):
        """Create db user and database if needed, based on settings file
        """
        try:
            # show python where to look
            import sys
            sys.path.append(path.join(self.get_src_path(), self.name))
            settings_module = __import__("conf.settings")
            settings = settings_module.DATABASES['default']
            init_db_selective(settings)
        except ImportError, e:
            print("DB initialization failed: settings not found")
            raise e
        except KeyError, e:
            print("DB initialization failed: settings incomplete")
            raise e

    def migrate_db(self):
        self.manage("syncdb --migrate")
                    
    def collect_staticfiles(self):
        with hide("stdout"):
            self.manage("collectstatic", stdin="yes yes")
    
    def reload_or_launch(self):
        try:
            self.supervisor("--daemonize")
        except:
            pass
        self.supervisor("reload")
            
    def manage(self, command, stdin=None):
        if stdin is None:
            stdin = ""
        else:
            stdin = stdin + "|"
            
        with cd(self.path):
            return self.virtualenv_run("%s bin/manage.py %s" % (stdin, command))

    def run_git(self, cmd):
        run("git %s" % (cmd) )

    def supervisor(self, command):
        return self.manage("supervisor --project-dir=bin %s" % command)
        
    def site_operation(self, operation):
        with cd(self.path):
            self.virtualenv_run("bin/site.py %s" % operation)
    
    def fetch_configuration(self):
        pass

    def get_src_path(self):
        return "%s/src/%s" % (self.path, self.project_name)

    def get_conf_path(self):
        return "%s/conf" % self.path


class ServerEnvironment(object):
    def __init__(self, root_dir):
        self.root_dir = root_dir

    def install_dependencies(self):
        pass