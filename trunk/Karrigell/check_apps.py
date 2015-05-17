import os
import Karrigell.sessions
import Karrigell.admin_db

class ConfigError(Exception):
    pass

def check(apps):
    for app in apps:
        # root_url starts with / ?
        if not app.root_url.startswith('/'):
            msg = 'Root url {} does not start with "/"'
            raise ConfigError(msg.format(app.root_url))
        # root dir exists ?
        if not os.path.exists(app.root_dir):
            msg = 'Root directory {} does not exist'
            raise ConfigError(msg.format(app.root_dir))
        if isinstance(app.users_db,Karrigell.admin_db.SQLiteUsersDb):
            app.users_db.setup() # will raise an exception if folder
                                 # can't be created
            
            