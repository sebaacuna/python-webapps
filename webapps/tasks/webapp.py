from fabric.tasks import Task
from fabric.decorators import task
from fabric.api import env, put, run
from ..models import Webapp

webapp = Webapp(env.app_name, env.repository)

@task
def deploy(branch=None):
    webapp.pull_or_clone()
    if branch is not None:
        webapp.switch_branch(branch)
    webapp.init_and_update_submodules()
    webapp.prepare_paths()
    webapp.install_requirements()
    webapp.install_app()
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
def config(*args, **kwargs):
    if len(args) >0:
        args = map(lambda x: x[1:], filter(lambda x: x[0] == "-", args))
        webapp.site_operation("delconfig %s" % " ".join(args))
    if len(kwargs):
        keyvals = ["%s=%s" % (key,val) for key,val in kwargs.items()]
        webapp.site_operation("config %s" % " ".join(keyvals))
    reload()