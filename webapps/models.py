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
    
    def var_path(self, path):
        with hide('stdout', 'running'):
            var_root = self.site_operation("path VAR_ROOT")
            return "%s/%s" % (var_root, path)
        
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
            "%s/html" % self.path,
            ])
        run("chmod -R +rwX %s/.ssh" % self.path)
        self.make_virtualenv()

    def make_virtualenv(self):
        if not files.exists("%s/bin/activate" % self.path):
            run("virtualenv %s" % self.path)

            #Symlink these libs for PIL to work
            if files.exists("/usr/lib/x86_64-linux-gnu/libfreetype.so"):
                prefix = "/usr/lib/x86_64-linux-gnu"
            else:
                prefix = "/usr/lib/i386-linux-gnu"
                
            for lib in ['libfreetype', 'libz', 'libjpeg']:
                run("ln -s %s/%s.so %s/lib/" % (prefix, lib, self.path))

    def install_requirements(self):
        with cd(self.src_path):
            with hide("stdout"):
                self.virtualenv_run('yes w | pip install -r requirements.txt')

    def install_app(self):
        with cd(self.path):
            self.virtualenv_run("pip install -e %s --force-reinstall" % self.src_path)

    def migrate_db(self):
        self.manage("syncdb --migrate --noinput")
    
    def reload_or_launch(self):
        try:
            int(self.supervisor("pid"))
        except:
            # Did not return a pid
            self.supervisor("--daemonize")
            
        self.supervisor("reload")
    
    def reinstall(self, package):
        with cd(self.src_path):
            self.virtualenv_run('pip install --ignore-installed --no-download %s' % package)
        self.reload_or_launch()
        
    def site_operation(self, operation):
        with cd(self.path):
            return self.virtualenv_run("bin/site.py %s" % operation)
    
    def collectstatic(self):
        self.site_operation("bundlestatic")
        self.manage("collectstatic", stdin="yes yes")
        
    def make_bucket_pulic(self):
        self.site_operation("make_bucket_public")
    
    def upload_server_key(self, local_key):
        put(local_key, "%s/server.key" % self.conf_path)
        
    def upload_server_cert(self, local_cert):
        put(local_cert, "%s/server.crt" % self.conf_path)