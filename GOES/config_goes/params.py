from enum import Enum

class GOES(Enum):
    band = 1  # The band of the satellite we want to downloadj
    input_folder = 2
    output_folder = 3

class CLASS(Enum):
    user0 = 1
    pass0 = 2
    dates = 3
    
class GMAIL(Enum):
    FROM_EMAIL = 1
    FROM_PWD = 2
    local_path = 3

