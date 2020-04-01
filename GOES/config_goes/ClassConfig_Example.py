from config_goes.params import CLASS

def get_config():
    cur_config = {
        CLASS.user0: 'rk.ecmwf',
        CLASS.pass0: 'BI755N0txW',
        CLASS.dates: '../test_data/goes/Ernesto.npz'
    }
    return cur_config