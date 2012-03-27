from fabric.api import *


@task
def query(sql, db="", mysql_user='webapps', mysql_pass=None):
    #mysql_pass = mysql_pass or env.config.MySQL.root_password

    if type(sql) is list:
        sql = " ".join(sql)
    #run('mysql --user=%s --password=%s -e "%s" %s' % (mysql_user, mysql_pass, sql, db))
    run('mysql --user=%s -e "%s" %s' % (mysql_user, sql, db))


@task
def create_user(user, password):
    sql = []
    sql.append("GRANT USAGE ON *.* TO '%s'@'localhost';" % (user))
    sql.append("DROP USER %s@localhost;" % user)
    sql.append("CREATE USER '%s'@'localhost' IDENTIFIED BY '%s';" % (user, password))
    sql.append("FLUSH PRIVILEGES;")
    query(sql=sql, db="mysql")

@task
def grant_db(name, owner):
    sql = []
    sql.append("GRANT USAGE ON %s.* TO '%s'@'localhost';" % (name, owner))
    sql.append("GRANT ALL ON %s.* TO '$dbuser'@'localhost' WITH GRANT OPTION;" % name)
    sql.append("FLUSH PRIVILEGES;")
    query(sql=sql, db="mysql")

@task
def create_db(name, owner=None):
    sql = []
    sql.append("CREATE DATABASE %s;" % name)
    query(sql=sql, db="mysql")
    if owner is not None:
        grant_db(name, owner)

@task
def drop_db(name):

    sql = []
    sql.append("DROP DATABASE IF EXISTS %s;" % name)
    query(sql=sql, db="mysql")

@task
def drop_user(user):
    print "drop_user(%s)" % user
    if user == "":
        raise Exception("Must provide a valid username")

    sql = []
    sql.append("GRANT USAGE ON *.* TO '%s'@'localhost';" % (user))
    sql.append("DROP USER %s@localhost;" % user)
    sql.append("FLUSH PRIVILEGES;")
    query(sql=sql, db="mysql")

@task
def flush_db(name, mysql_user):
    mysql_pass = env.config.Database.password

    cmd = "mysqldump -u%s -p%s --add-drop-table --no-data %s | grep ^DROP | mysql -u%s -p%s %s"
    cmd %= (mysql_user, mysql_pass, name,
            mysql_user, mysql_pass, name)
    run(cmd)
