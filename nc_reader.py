import json
import os
import os.path as osp
import subprocess as sb

import netCDF4 as nc4
import numpy as np
import pandas as pd

from ..globalimports import *


def main(data_dir, refreshjson_boo=False):
    '''
    - single value variables are written as strings
    - time axis of dimension 1 is removed from variables which are array like
    - arrays are converted to list before json dumping as numpy arrays canno
      be serialised
    - function is called recursively so that data is read as numpy arrays
    - json file stores date and time as string, but function reads them as 
      pd.Timstamp

    Parameters:
        data_dir (str): directory containing all the nc files, must end with '/'
        refreshjson_boo (boolean): decides whether to rewrite the data.json file

    Returns:
        ret_ara (array): array of dictionaries
    '''
    # listing out info for extracting
    timevar = 'time'
    timevar_lst = [
        'date_yyyyMMdd', 'time_hhmmss',        
    ]
    valvar_lst = [
        'elevation_angle', 'azimuth_angle',
        'copol_background', 'crosspol_background',
        'year', 'month', 'day', 'hour', 'minute', 'second',
        'latitude', 'longitude', 'altitude'
    ]
    valvar_lststr = ','.join(valvar_lst + timevar_lst)

    aravar_lst = [
        # data
        'range_raw',
        'copol_raw', 'crosspol_raw',
        'copol_snr', 'crosspol_snr',
        'range_nrb',
        'copol_nrb', 'crosspol_nrb',

        # products
        'number_of_clouds',
        'clouds',
    ]

    
    try:                        # reading from file if data has been read before
        if refreshjson_boo:     # forcing a refresh of the file
            raise IOError
        else:
            with open(DIRCONFN(data_dir, JSONFILE)) as json_file:
                ret_ara = json.load(json_file)
                for dic in ret_ara:
                    # handling time
                    dic[timevar] = pd.Timestamp(
                        dic['date_yyyyMMdd'][1:-1] + dic['time_hhmmss'][1:-1]
                    )
                    
                    # turning lists arrays into numpy arrays
                    for var, val in dic.items():
                        if var in valvar_lst and var not in timevar_lst:
                            dic[var] = float(val)
                        elif var in aravar_lst and var not in timevar_lst:
                            dic[var] = np.array(val)
                        
                return ret_ara
                            

    except IOError:             # reading files and writing json file
        # iterating through nc files
        ret_ara = []
        nc_lst = [DIRCONFN(data_dir,nc_file) for nc_file in os.listdir(data_dir)\
                  if nc_file[-2:] == 'nc']
        nc_lst.sort()
        for nc_file in nc_lst:

            # handling variable values
            comm_str = "ncdump -v {} {} | sed -e '1,/data:/d' -e '$d'".\
                format(valvar_lststr, nc_file)
            valvar_varstr = sb.check_output(comm_str, shell=True).\
                decode('utf-8')
            valvar_varlst = valvar_varstr.split('\n\n')
            valvar_varlst[0] = valvar_varlst[0][1:]
            valvar_varlst[-1] = valvar_varlst[-1][:-1]
            valvar_dict = dict(map(lambda x: x[1:-2].split(' = '),
                                   valvar_varlst))

            # handling variable arrays
            nc_ds = nc4.Dataset(nc_file, mode='r', format='NETCDF4_CLASSIC')
            aravar_dict = {}
            for var in aravar_lst:
                ara = np.array(nc_ds.variables[var][:])
                # removing redundant time axis in arrays
                if ara.shape[0] == 1 and len(ara.shape) != 1:
                    ara = np.squeeze(ara, axis=0)
                aravar_dict[var] = ara.tolist()

            # appending to array
            ret_ara.append({**valvar_dict, **aravar_dict})


        # writing dictionary to json file
        with open(DIRCONFN(data_dir, JSONFILE), 'w+') as json_file:
            json.dump(ret_ara, json_file)


        # calling function again so that data can be read as numpy array
        return main(data_dir, refreshjson_boo=False)
    

if __name__ == '__main__':

    import os.path as osp

    datadate = '20200304'
    data_dir = osp.dirname(osp.dirname(osp.dirname(osp.dirname(osp.abspath(__file__)))))\
        + '/data/smmpl_E2/{}/'.format(datadate)

    data_dictara = main(data_dir, refreshjson_boo=False)
    range_raw = data_dictara[0]['range_raw']
    print(range_raw[0], range_raw[1], len(range_raw))
    print((range_raw[1]-range_raw[0])/1e-7*2)
