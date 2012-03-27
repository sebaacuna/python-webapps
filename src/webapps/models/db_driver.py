# Scripts for database and user creation
drivers = {
    'django.db.backends.mysql': __import__('mysql'),
    #TODO: postgres 'driver'
    #others
}

def init_db_selective(settings):
    driver = drivers[settings['ENGINE']]
    driver.create_user(settings['USER'], settings['PASSWORD'])
    driver.create_db(settings['NAME'], settings['USER'])
