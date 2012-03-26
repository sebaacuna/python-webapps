from fabric.api import *
from fabric.contrib import files
from os import path
from ..util import virtualenv_run


class Webapp(object):
    def __init__(self, server, name, repository, branch):
        self.server = server
        self.name = name
        self.repository = repository
        self.project_name = self.extract_project_name(repository)
        self.branch = None

    @property
    def path(self):
        return path.join(self.server.root_dir, self.server.name+"."+self.name)

    def extract_project_name(self, repository):
        project_name, ext = path.splitext(path.basename(repository))
        return project_name

    def prepare_paths(self):
        map(self.mkdir, [
            self.get_src_path(),
            self.get_conf_path(),
            "%s/.ssh" % self.path,
            "%s/var/{media,log}" % self.path,
            ])
        run("chmod -R +rwX %s/.ssh" % self.path)
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

    def switch_branch(self, branch):
        self.branch = branch
        if self.branch is not None:
            with cd(self.get_src_path()):
                self.run_git("checkout %s" % self.branch)

    def run_git(self, cmd):
        run("git %s" % (cmd) )

    def install_requirements(self):
        with cd(self.path):
            pip_file = path.join(self.get_src_path(), "requirements.pip")
            with hide("stdout"):
                virtualenv_run('yes w | pip install -r %s' % pip_file)

    def install(self):
        self.prepare_paths()
        with cd(self.path):
            virtualenv_run("pip install -e %s" % self.get_src_path())
        self.customize_server_configs()

    def init_local_settings(self):
        local_dir = self.get_settings_dir("local")
        dev_dir = self.get_settings_dir("dev")
        settings = [
            ("%s/settings.py" % local_dir,
                "%s/settings.py" % dev_dir),
            ("%s/api_settings.py" % local_dir,
                "%s/api_settings.py" % dev_dir),
            ("%s/db_settings.py" % local_dir,
                "%s/db_settings.py" % dev_dir),
            ("%s/db_settings_test.py" % local_dir,
                "%s/db_settings_test.py" % dev_dir)
        ]
        for (local_settings, dev_settings) in settings:
            if not files.exists(local_settings):
                copy_cmd = "cp %s %s" % (dev_settings, local_settings)
                run(copy_cmd)
        run("touch %s/__init__.py" % self.get_settings_dir("local"))

    def get_settings_dir(self, context):
        path = "%s/%s/conf/%s"
        return path % (self.get_src_path(), self.name, context)

    def customize_server_configs(self):
        self.init_local_settings()
        replacements = {
                "SERVER_NAME": self.server.name,
                "WEBAPP_PATH": self.path,
                "WEBAPP_NAME": self.name,
            }

        for conf_name in [ 'apache.conf', 'django.wsgi' ]:
            #TODO: The hardcoded /dev/ below is ugly
            source_path = "%s/server_configs/dev/%s.tmpl"
            source_path %= (self.get_src_path(),conf_name)

            target_path = "%s/%s"
            target_path %= (self.get_conf_path(), conf_name)

            run("cp -f %s %s" % (source_path, target_path))

            for param, value in replacements.iteritems():
                files.sed(target_path, param, value)

    def deploy_vhost(self):
        symlink_cmd = "ln -sf %s/apache.conf %s/.conf/%s.conf"
        symlink_cmd %= (self.get_conf_path(), self.server.root_dir, path.basename(self.path))
        run(symlink_cmd)

    def trigger_reload(self):
        run("touch %s/django.wsgi" % self.get_conf_path())

    def collect_staticfiles(self):
        with cd(self.path):
            with hide("stdout"):
                virtualenv_run("yes yes| bin/manage.py collectstatic")

    def fetch_configuration(self):
        pass


    def apply_migrations(self):
        with cd(self.path):
            virtualenv_run("bin/manage.py migrate")


    def get_src_path(self):
        return "%s/src/%s" % (self.path, self.project_name)

    def get_conf_path(self):
        return "%s/conf" % self.path


class ServerEnvironment(object):
    def __init__(self, root_dir, name):
        self.root_dir = root_dir
        self.name = name

    def install_dependencies(self):
        #TODO: Install/verify dependencies
        #       For now, assume all dependencies have been installed
        pass

    def get_key_path(self):
        return "~/.ssh/%s" % self.get_key_name()

    def get_key_name(self):
        return "deploy-%s.key" % self.name

    def install_key(self):
        self.upload_key()

    def upload_key(self):
        run("mkdir -p ~/.ssh")
        run("chmod 0700 ~/.ssh")
        put(self.get_key_name(), self.get_key_path())
        run("chmod 0600 %s" % self.get_key_path())
