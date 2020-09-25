# imports
import json
import numpy as np
import pandas as pd

# params
_time_key = 'Timestamp'


# write function
def datajson_write(dic, filename):
    # handling special data types
    dic[_time_key] = dic[_time_key].astype(np.str)

    # convert arrays to list for serialisation
    for key, value in dic.items():
        try:
            dic[key] = value.tolist()
        except AttributeError:
            pass

    with open(filename, 'w') as json_file:
        json_file.write(json.dumps(dic))
    print(f'wrote data to {filename}')


# read func
def datajson_read(filename):
    with open(filename, 'r') as json_file:
        ret_d = json.load(json_file)
    print(f'read json data from {filename}')

    # converting serializable arrays to numpy arrays
    ret_d = {key: np.array(ret_d[key]) for key in list(ret_d.keys())}

    # handling special data types
    ret_d[_time_key] = np.array(list(map(pd.Timestamp, ret_d[_time_key])))

    return ret_d
