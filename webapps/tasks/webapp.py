from fabric.tasks import Task
from fabric.decorators import task
from fabric.api import env, put, run, get, prompt
from fabric.contrib import files
from ..models import Webapp

webapp = Webapp(env.app_name, env.repository)

@task
def deploy(branch=None, conf=None):
    webapp.pull_or_clone()
    if branch is not None:
        webapp.switch_branch(branch)
    webapp.init_and_update_submodules()
    webapp.prepare_paths()
    webapp.install_requirements()
    webapp.install_app()
    if conf:
        config("push", conf)
    webapp.migrate_db()
    webapp.reload_or_launch()

@task
def site(operation):
    webapp.site_operation(operation)

@task
def reload():
    webapp.reload_or_launch()
    
@task 
def collectstatic():
    webapp.collectstatic()
    #webapp.make_bucket_public()

@task
def server_key(keyfile):
    webapp.upload_server_key(keyfile)

@task
def server_cert(certfile):
    webapp.upload_server_cert(certfile)
    
@task
def ssl(mode):
    webapp.site_operation("ssl %s" % mode)

@task
def param(*args, **kwargs):
    if len(args) >0:
        args = map(lambda x: x[1:], filter(lambda x: x[0] == "-", args))
        webapp.site_operation("unset %s" % " ".join(args))
    if len(kwargs):
        keyvals = ["%s=%s" % (key,val) for key,val in kwargs.items()]
        webapp.site_operation("set %s" % " ".join(keyvals))

    if len(args) + len(kwargs) >0:
        reload()

@task
def config(operation=None, local_file=None):
    if operation is None:
        webapp.site_operation("config")
        return
    elif operation not in ("push", "pull"):
        raise Exception("Unknown config operation: %s" % operation)
    elif local_file is None:
        raise Exception("Local file must be specified in order to %s" % operation)
        
    config_path = str(webapp.site_operation("config_path"))
    if operation == "pull":
        get(config_path, local_file)
    if operation == "push":
        if files.exists(config_path):
            if "y" != prompt("**WARNING** This will overwrite servers local config. Proceed? [yn]"):
                return
            run("rm %s" % config_path)
        put(local_file, config_path)
        reload()