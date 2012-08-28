from fabric.tasks import Task
from fabric.decorators import task
from fabric.api import env, put, run, get, prompt, local, lcd, abort
from fabric.contrib import files
from ..models import Webapp
import os

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
def reinstall(package):
    #Force-Reinstalls a dependency
    webapp.reinstall(package)
    
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
def config(pull=None, push=None):
    if pull is None and push is None:
        webapp.site_operation("config")
        return
    elif pull is not None and push is not None:
        raise Exception("Choose a single operation")
        
    config_path = str(webapp.site_operation("config_path"))
    if pull:
        get(config_path, pull)
    if push:
        if files.exists(config_path):
            if "y" != prompt("**WARNING** This will overwrite servers local config. Proceed? [yn]"):
                return
            run("rm %s" % config_path)
        put(push, config_path)
        reload()
        
@task
def createsuperuser():
    webapp.manage("createsuperuser")

@task
def tail(process="web.0"):
    webapp.supervisor("tail -100 %s" % process)

@task
def ps():
    webapp.supervisor("status")
    
@task
def maintenance(mode=None):
    if mode == "on":
        webapp.supervisor("stop all")
    elif mode == "off":
        webapp.supervisor("start all")
    else:
        abort("Usage: maintenance:[on|off]")
        