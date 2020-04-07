from config_goes.params import GOES

def get_config():
    cur_config = {
        GOES.band: '4',
        GOES.input_folder: '../test_data/goes',
        GOES.output_folder: '../test_data/goes/output'
    }
    return cur_config

