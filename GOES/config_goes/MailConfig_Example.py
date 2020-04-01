from config_goes.params import GMAIL

def get_config():
    cur_config = {
        GMAIL.FROM_EMAIL: 'rk.ecmwf@gmail.com',
        GMAIL.FROM_PWD: '6$$%70Wu',
        GMAIL.local_path: '../test_data/goes'
    }
    return cur_config