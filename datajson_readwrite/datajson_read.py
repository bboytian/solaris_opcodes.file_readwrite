# imports
import json

from ...global_imports.params_solaris_opcodes import *

# main func
@verbose
def main(dic, filename):
    write_d = {key: dic[key].tolist() for key in list(dic.keys())}
    with open(filename, 'w') as json_file:
        json_file.write(json.dumps(write_d))
    print(f'wrote data to {filename}')


# testing
if __name__ == '__main__':
    main()
