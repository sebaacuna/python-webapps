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