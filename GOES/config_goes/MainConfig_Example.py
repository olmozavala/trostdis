from config_goes.params import GOES

def get_config():
    cur_config = {
        GOES.band: '6',
        GOES.input_folder: '../test_data/goes',
        GOES.output_folder: 'output_goes'
    }
    return cur_config

