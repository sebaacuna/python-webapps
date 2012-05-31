# Scripts for database and user creation
import mysql


drivers = {
    'django.db.backends.mysql': mysql,
    #TODO: postgres 'driver'
    #others
}

def init_db_selective(settings):
    driver = drivers[settings['ENGINE']]
    driver.create_user(settings['USER'], settings['PASSWORD'])
    driver.create_db(settings['NAME'], settings['USER'])
