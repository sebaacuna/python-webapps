from fabric.api import *
from fabric.contrib import files
from os import path


class Webapp(object):
    def __init__(self, name, repository):
        self.name = name
        self.repository = repository
        self.project_name, ext = path.splitext(path.basename(repository))

    # ------------------------
    # Helper methods
    # ------------------------
    @property
    def path(self):
        return path.join(env.deploy_root, self.name)
        
    @property
    def src_path(self):
        return "%s/src/%s" % (self.path, self.project_name)

    @property
    def conf_path(self):
        return "%s/conf" % self.path
        
    def virtualenv_run(self, cmd):
        return run('source %s/bin/activate && %s' % (self.path, cmd))

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

    def mkdir(self, path):
        run("mkdir -p %s" % path)
        
    # ------------------------
    # Actual webapp operations
    # ------------------------
    def pull_or_clone(self):
        if files.exists(self.src_path):
            with cd(self.src_path):
                self.run_git("pull")
        else:
            self.run_git("clone %s %s" % (self.repository, self.src_path) )
    
    def switch_branch(self, branch):
        with cd(self.src_path):
            self.run_git("checkout %s" % branch)

    def init_and_update_submodules(self):
        with cd(self.src_path):
            self.run_git("submodule init")
            self.run_git("submodule update")

    def prepare_paths(self):
        map(self.mkdir, [
            self.src_path,
            self.conf_path,
            "%s/.ssh" % self.path,
            "%s/var/log" % self.path,
            ])
        run("chmod -R +rwX %s/.ssh" % self.path)
        if not files.exists("%s/bin/activate" % self.path):
            run("virtualenv %s" % self.path)

    def install_requirements(self):
        with cd(self.src_path):
            with hide("stdout"):
                self.virtualenv_run('yes w | pip install -r requirements.txt')

    def install_app(self):
        with cd(self.path):
            self.virtualenv_run("pip install -e %s --force-reinstall" % self.src_path)

    def migrate_db(self):
        self.manage("syncdb --migrate")
    
    def reload_or_launch(self):
        try:
            self.supervisor("--daemonize")
        except:
            pass
        self.supervisor("reload")
        
    def site_operation(self, operation):
        with cd(self.path):
            self.virtualenv_run("bin/site.py %s" % operation)
    
    def collectstatic(self):
        self.manage("collectstatic", stdin="yes yes")