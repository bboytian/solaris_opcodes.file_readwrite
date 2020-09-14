# imports
from re import split

import numpy as np

from ...global_imports.solaris_opcodes import *


# params
_headersize = 1


# main func
def main(filedir, startime=None, endtime=None):
    '''
    reads the webswitch log file which is derived from the webswitch browser
    interface; i.e. <webswitch url>/log.txt

    By default sensor 2 is humidity, sensor 1 is temperature

    Parameters
    filedir (str): webswitch log file
    start/endtime (datetime like): approx start/end time of data of interest
                                   if not specified, it returns up till the start
                                   and end
                                   has to be datetime aware
    Return
        webswitch_d (dict)
            ts_ta (np.ndarray)
            o1/2_ta (np.ndarray): switch on/off status, boolean
            s1/2_ta (np.ndarray): sensor reading
    '''
    # reading file
    with open(filedir, 'r') as webswitch_file:
        lines_a = webswitch_file.readlines()

    # removing header
    lines_a = lines_a[_headersize:]

    # parsing lines
    lines_a = np.array((list(map(lambda x: split(',', x), lines_a))))
    ts_ta = lines_a[:, 0]
    o1_ta = lines_a[:, 1]
    o2_ta = lines_a[:, 2]
    s1_ta = lines_a[:, 3]
    s2_ta = lines_a[:, 4]

    # converting string to data
    ts_ta = LOCTIMEFN(ts_ta, utcinfo=UTCINFO)
    o1_ta = o1_ta.astype(np.bool)
    o2_ta = o2_ta.astype(np.bool)

    ## replacing all the irrelevant strings with nan
    s1_ta[s1_ta == 'xxx.x'] = np.nan
    s2_ta[s2_ta == 'xxx.x'] = np.nan
    s1_ta = s1_ta.astype(np.float)
    s2_ta = s2_ta.astype(np.float)

    # slicing according to start/end time specified
    startind = 0
    endind = None
    if startime:
        startind = np.argmax(ts_ta >= startime)
    if endtime:
        endind = np.argmax(ts_ta > endime)
    if endind == 0:
        endind = 0

    ts_ta = ts_ta[startind:endind]
    o1_ta = o1_ta[startind:endind]
    o2_ta = o2_ta[startind:endind]
    s1_ta = s1_ta[startind:endind]
    s2_ta = s2_ta[startind:endind]

    # returning
    webswitch_d = {
        'ts_ta': ts_ta,
        'o1_ta': o1_ta,
        'o2_ta': o2_ta,
        's1_ta': s1_ta,
        's2_ta': s2_ta,
    }
    return webswitch_d


# testing
if __name__ == '__main__':
    import matplotlib.pyplot as plt

    webswitch_d = main(
        '/home/tianli/SOLAR_EMA_project/data/smmpl_E2/20200914/202009141035_webswitchlog.txt'
    )

    print(webswitch_d['o2_ta'])
    print(webswitch_d['s2_ta'])
