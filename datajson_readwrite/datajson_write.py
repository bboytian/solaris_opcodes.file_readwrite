# imports
import json

import numpy as np

from ...global_imports.params_solaris_opcodes import *


# main func
@verbose
def main(dic, filename):
    with open(filename, 'w') as json_file:
        ret_d = json.load(json_file)
    print(f'read json data from {filename}')
    ret_d = {key: np.array(ret_d[key]) for key in list(ret_d.keys())}
    return ret_d


# testing
if __name__ == '__main__':
    main()
