# imports
import numpy as np
import pandas as pd

# main func
def main(filedir):
    '''
    Reads the YYYYMMddhhmm_cloudheight.txt files which are produced by
    solaris_opcodes.product_calc.cloudproduct_print

    Parameters
        filedir (str): directory of the file we want to read
    Returns
        start/endtime (pd.Timestamp): start/end time of the data in the file
        lat/long_pa (np.ndarray): [deg] lat/long array, number of pixels
        cloudheights_pAl (list): (number of pixels, number of cloud layers)
    '''
    with open(filedir, 'r') as f:
        lines = f.read().splitlines()

    # reading time
    starttime = pd.Timestamp(lines[0])
    endtime = pd.Timestamp(lines[1])

    # reading other data
    lines = lines[2:]
    lat_pa = np.array([])
    long_pa = np.array([])
    cloudheights_pAl = []
    for line in lines:
        line = np.array(line.split(), dtype=np.float)
        lat_pa = np.append(lat_pa, line[0])
        long_pa = np.append(long_pa, line[1])
        cloudheights_pAl.append(np.array(line[2:]))

    return starttime, endtime, lat_pa, long_pa, cloudheights_pAl


# testing
if __name__ == '__main__':
    print(
        main('/home/tianli/SOLAR_EMA_project/data/smmpl_E2/20210101/202101010020_cloudheight.txt')
    )
