# imports
from copy import deepcopy
import json
import os

import numpy as np
import pandas as pd

from ..datajson_readwrite import datajson_write
from ...global_imports.solaris_opcodes import *


# reader_funcfunc
def main(import_d, size2eind_func, size2sind_func):
    '''
    Parameters
        import_d (dict): dictionary of .mpl file formats. should differ for
                        scanning minimpl and mpl
        size2e/sind_func (func): function to calculate the index of given key
    Return
        reader_func (func): function to read .mpl files of given function
    '''
    # defining references
    timekey = import_d['time_key']
    rangekey = import_d['range_key']
    maskkey = import_d['mask_key']
    padkey = import_d['pad_key']
    Nbinkey = 'Number Bins'
    firstbinkey = 'First data bin'
    bintimekey = 'Bin Time'
    energykey = 'Energy Monitor'

    bintimefactor = import_d['bintimefactor']
    energyfactor = import_d['energyfactor']
    headersize = import_d['headersize']
    channelbytenum = import_d['channelbytenum']

    timekey_l = import_d['time_keylst']
    channelkey_l = import_d['channel_keylst']
    wantedkey_l = import_d['wanted_keylst']

    bytesize_d = import_d['bytesize_dic']  # redundant
    bytesind_d = import_d['bytesind_dic']
    byteeind_d = import_d['byteeind_dic']
    dtype_d = import_d['dtype_dic']

    Nbinsind, Nbineind = bytesind_d[Nbinkey], byteeind_d[Nbinkey]

    # main reader func
    @verbose
    @announcer
    def reader_func(
            datesdir=None,
            readerstartind=MPLREADERSTARTIND, readerendind=MPLREADERENDIND,
            mplfiledir=None,
            starttime=None, endtime=None,
            slicetup=None,
            filename=None,
    ):
        '''
        1 shot no. of bytes  = headersize + no. of channels * dtype size * Nbin
        so far headersize is fixed at 163
        for mpl:
            30m -> Nbin 798
        for smmpl:
            15m -> Nbin 2000
            30m -> Nbin 1000

        file search performed b/n starttime and endtime if provided.
        single file used if mplfiledir is provided.
        Bintime is scaled by bintime factor from {}_fmt.py here

        This reader generates the following which did not exist in .mpl files
            - timestamp array
            - mask for channel data
            - range array for channels

        Future
            - There is a very crude hardcode here that filters the directories
              under data, to only include relevant data.
              It finds the directories which start with '2'.
              This could be left alone for now.

        Parameters
            datesdir (str): directory containing all the dates which contains the
                            mpl files
            readerstart/endind (int): index offset from the specified data start
                                      and end dates to search for the profiles
            mplfiledir (str): non absolute filename of single mpl file, date
                              should be None
            start/endtime (datetime like): approx start/end time of data of
                                           interest, specified if mplfiledir
                                           is None.
                                           leave endtime empty if we want latest
                                           must be timezone aware
            slicetup (slice): slice tuple along time axis, only if mplfiledir
                              is specified
            filename (str): output will be a json file format, if specified

        Return
            mpldic (dict): dictionary of data in specified time frame.
                           keys are listed in .mplfmt.py. The added keys are:
                               - Timestamp
                               - Range
                               - mask_key: 'Channel Data Mask'



                           dictionary is empty if the starttime is greater than
                           available files
        '''
        # catching wrong inputs
        try:
            if endtime <= starttime:
                raise ValueError(
                    f'{endtime=:} must be greater than {starttime=:} '
                )
        except TypeError:       # when endtime is not specified
            pass

        if mplfiledir:          # single file read
            mplfiles = [mplfiledir]
        else:                   # finding files in data archive
            # finding files
            ## listing directories
            dates = np.array(list(filter(
                    lambda x: x[0] == '2',
                    os.listdir(datesdir)
                )))
            dates = LOCTIMEFN(dates, UTCINFO)
            dates.sort()
            ## choosing relevant date folders
            starttimeboo_a = dates > starttime
            startind = np.argmax(starttimeboo_a) - readerstartind
            if startind < 0:
                if starttimeboo_a.any():  # starttime is before first date
                    startind = 0
                else:                   # starttime could be within last date
                    startind = -1
            if endtime:
                endtimeboo_a = dates > endtime
                endind = np.argmax(endtimeboo_a) + readerendind
                if not endtimeboo_a.any():  # endtime is after last date
                    endind = None
            else:
                endind = None
            dates = dates[startind:endind]
            dates = list(map(lambda x: DATEFMT.format(x), dates))
            ## finding mpl files
            datedir_l = [DIRCONFN(datesdir, date) for date in dates]
            mplfiles = FINDFILESFN(MPLFILE, datedir_l)
            mplfiles.sort()
            mplfiles = np.array(mplfiles)

        # reading files
        ## reading files one scanpattern at a time
        byteara_l = []
        Nbin_l = []
        print('reading files:')
        for mplfile in mplfiles:
            print('\t{}'.format(mplfile))
            with open(mplfile, 'rb') as mplf:
                byteara = bytearray(mplf.read())
            # convert binary data to numpy array for reshaping
            byteara = np.frombuffer(byteara, dtype=np.byte)
            ## reading channel length from first measurement
            try:
                Nbin = np.frombuffer(byteara[Nbinsind:Nbineind],
                                     dtype=dtype_d[Nbinkey])[0]
                Nbin_l.append(Nbin)
                byteara_l.append(byteara)
            except IndexError:  # in the event the file is empty
                pass

        ## catching the case where all files are empty
        if not byteara_l:
            print('no non-empty files found')
            return {}

        ## editing indices for channels to fit the maxNbbin
        maxNbin = max(Nbin_l)
        for channelkey in channelkey_l:  # to be used when convert ara to dic
            bytesize_d[channelkey] = channelbytenum * maxNbin
        byteeind_d = size2eind_func(bytesize_d)
        bytesind_d = size2sind_func(byteeind_d)

        ## extending measurement to form rectangle block
        cbyteara_l = deepcopy(byteara_l)
        byteara_l = []
        pad_a = np.array([], dtype=np.int)
        for i, Nbin in enumerate(Nbin_l):
            byteara = cbyteara_l[i]
            # reshape into rectangle for time axis
            bytesize = headersize + Nbin * len(channelkey_l) * channelbytenum
            bytearalen = len(byteara)
            numara = bytearalen//bytesize
            exind = -(bytearalen % bytesize)
            if exind:
                raise Exception('Incomplete profile in file')
                byteara = byteara[:exind]  # trim incomplete mea
            byteara = byteara.reshape(numara, bytesize)
            # extending rectangle
            pad = maxNbin - Nbin
            pad_a = np.append(pad_a, [pad]*numara)
            append_a = np.zeros((
                numara, pad * channelbytenum
            ), dtype=np.byte)
            cheind_a = headersize + np.cumsum(
                np.arange(len(channelkey_l)) * channelbytenum * Nbin
                )
            split_A = np.split(byteara, cheind_a, axis=1)
            byteara = np.concatenate([
                split_a if i == len(split_A) - 1 else
                np.append(split_a, append_a, axis=1)
                for i, split_a in enumerate(split_A)
            ], axis=1)
            byteara_l.append(byteara)

        ## concat scanpatterns together
        byteara_l = np.concatenate(byteara_l, axis=0)
        del cbyteara_l
        ## convert array of measurement bytes to dict
        ## channel arrays are flattened and need to be reshaped
        mpl_d = {
            key: np.frombuffer(
                np.apply_along_axis(
                    lambda x: x[bytesind_d[key]:byteeind_d[key]].tobytes(),
                    axis=1, arr=byteara_l
                ), dtype=dtype_d[key]
            ) for key in wantedkey_l
        }

        ## scaling certain quantities to follow convention
        mpl_d[bintimekey] = mpl_d[bintimekey] * bintimefactor
        mpl_d[energykey] = mpl_d[energykey] * energyfactor

        ## converting time to datetime like object
        time_d = {key: mpl_d[key] for key in timekey_l}
        timeara = pd.to_datetime(pd.DataFrame(time_d)).to_numpy('datetime64[s]')
        timeara = LOCTIMEFN(timeara, UTCINFO)
        mpl_d[timekey] = timeara

        ## treating channels differently;
        ### reshape arrays into measurements, removing as much padding as possible
        firstbin_ara = mpl_d[firstbinkey]  # effectively Ndatabin_ara-Nbin_ara
        pad_a += firstbin_ara
        removepadnum = pad_a.min()
        pad_a -= removepadnum
        mpl_d[padkey] = pad_a
        for key in channelkey_l:
            chara = mpl_d[key]
            mpl_d[key] = chara.reshape(
                len(chara)//maxNbin, maxNbin
            )[:, removepadnum:]
        ### creating mask to accomodate padding
        newmaxNbin = mpl_d[key].shape[-1]
        mpl_d[maskkey] = np.arange(newmaxNbin) >= pad_a[:, None]
        ### creating range array
        Delr_ta = SPEEDOFLIGHT * mpl_d[bintimekey]  # binsize
        mpl_d[rangekey] = Delr_ta[:, None] * np.arange(newmaxNbin)\
            - (Delr_ta * pad_a)[:, None]

        ## trimming according to starttime and endtime
        mplkey_l = list(mpl_d.keys())
        if starttime:
            # trimming can still take place even when reading single file
            startboo_a = timeara >= starttime
            if startboo_a.any():
                startind = np.argmax(startboo_a)
            else:
                startind = len(timeara)
            if endtime:
                endind = np.argmax(timeara > endtime)
                if not endind:
                    endind = None
            else:
                endind = None
            mpl_d = {key: mpl_d[key][startind:endind] for key in mplkey_l}
        elif slicetup and mplfiledir:   # accord to slicetup
            mpl_d = {key: mpl_d[key][slicetup] for key in mplkey_l}

        nummeasurements = len(mpl_d[timekey])
        if nummeasurements:
            print('total of {} profiles'.format(len(mpl_d[timekey])))
        else:
            mpl_d = {}
            print('no profiles found')

        # writing to file
        if filename:
            datajson_write(mpl_d, filename)

        # returning
        return mpl_d

    return reader_func


# testing
if __name__ == '__main__':
    import matplotlib.pyplot as plt

    from .mpl_fmt import import_dic
    from .mpl_fmt import size2eind_func, size2sind_func
    mpl_reader = main(import_dic, size2eind_func, size2sind_func)

    from .smmpl_fmt import import_dic
    from .smmpl_fmt import size2eind_func, size2sind_func
    smmpl_reader = main(import_dic, size2eind_func, size2sind_func)


    # test block 1

    # starttime = LOCTIMEFN('202009290000', UTCINFO)
    # endtime = LOCTIMEFN('202009290500', UTCINFO)
    # mpl_d = smmpl_reader(
    #     datesdir=SOLARISMPLDIR.format('smmpl_E2'),
    #     starttime=starttime, endtime=endtime,
    # )

    # ch1_tra = mpl_d['Channel #1 Data']
    # ch2_tra = mpl_d['Channel #2 Data']
    # ch_trm = mpl_d['Channel Data Mask']
    # bintime_ta = mpl_d['Bin Time']
    # binnum_ta = mpl_d['Number Bins']
    # r_tra = mpl_d['Range']

    # counter = 0
    # for i, binnum in enumerate(binnum_ta):
    #     plt.plot(r_tra[i][ch_trm[i]], ch1_tra[i][ch_trm[i]], color='C0')
    #     plt.plot(r_tra[i][ch_trm[i]], ch2_tra[i][ch_trm[i]], color='C1')
    #     counter += 1
    #     if counter > 100:
    #         break
    # plt.yscale('log')
    # plt.show()


    # test block 2

    # mpl_fn = '/home/tianli/SOLAR_EMA_project/codes/solaris_opcodes/product_calc/nrb_calc/testNRB_mpl_S2S.mpl'
    # mpl_d = mpl_reader(
    #     mplfiledir=mpl_fn,
    #     slicetup=slice(OVERLAPPROFSTART, OVERLAPPROFEND, 1)
    # )

    # ch1_tra = mpl_d['Channel #1 Data']
    # ch2_tra = mpl_d['Channel #2 Data']
    # ch_trm = mpl_d['Channel Data Mask']
    # bintime_ta = mpl_d['Bin Time']
    # binnum_ta = mpl_d['Number Data Bins']
    # r_tra = mpl_d['Range']

    # for i, binnum in enumerate(binnum_ta):
    #     if i in []:
    #         pass
    #     else:
    #         plt.plot(r_tra[i][ch_trm[i]], ch1_tra[i][ch_trm[i]], color='C0')
    #         plt.plot(r_tra[i][ch_trm[i]], ch2_tra[i][ch_trm[i]], color='C1')
    # plt.yscale('log')
    # plt.show()


    # test block 3
    starttime = LOCTIMEFN('202011260030', 0)
    endtime = LOCTIMEFN('202011260100', 0)
    mpl_d = smmpl_reader(
        datesdir=SOLARISMPLDIR.format('smmpl_E2'),
        starttime=starttime, endtime=endtime,
    )

    ts_ta = mpl_d['Timestamp']
    print(ts_ta[0])
    print(ts_ta[-1])
