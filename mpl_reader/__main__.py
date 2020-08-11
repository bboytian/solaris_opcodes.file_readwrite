# imports
from copy import deepcopy
import json
import os

import numpy as np
import pandas as pd

from ...global_imports import *


# params
_casetwoind = -2                # in the event there is only one eomtime returned from
                                # _lstfromtimes_func, we will read the last _casetwoind mplfiles


# supp func
def _lstfromtimes_func(times, starttime, endtime, startoff, endoff):
    '''
    Paramters
        times (pd.Timeseries)
        start/endtime (datetime like): approx start/end time of data of interest
        start/endoff (int): offset to start and end trimming, refer to 'Return'
    Return
        whatever left of the timeseries that is (1+startoff) indexes before
        starttime and (endoff) indexes after endtime
        one index after endtime
    '''
    starttimeboo_a = times > starttime
    startind = np.argmax(starttimeboo_a) - 1 - startoff
    if startind < 0:
        if starttimeboo_a.any():  # starttime is before first time provided
            startind = 0
        else:                   # starttime is equal to the last eom.flag
            startind = -1

    if endtime:
        endind = np.argmax(times > endtime) + endoff
        if endind == endoff:        # endtime is after last time provided
            endind = None
    else:
        endind = None
    return times[startind:endind]


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
    time_key = import_d['time_key']
    range_key = import_d['range_key']
    mask_key = import_d['mask_key']
    Nbin_key = 'Number Bins'
    firstbin_key = 'First data bin'  # This is the length of the range axis
    bintime_key = 'Bin Time'
    energy_key = 'Energy Monitor'
    bintimefactor = import_d['bintimefactor']
    energyfactor = import_d['energyfactor']
    headersize = import_d['headersize']
    channelbytenum = import_d['channelbytenum']

    time_keylst = import_d['time_keylst']
    channel_keylst = import_d['channel_keylst']
    wanted_keylst = import_d['wanted_keylst']

    bytesize_dic = import_d['bytesize_dic']  # redundant
    bytesind_dic = import_d['bytesind_dic']
    byteeind_dic = import_d['byteeind_dic']
    dtype_dic = import_d['dtype_dic']

    Nbinsind, Nbineind = bytesind_dic[Nbin_key], byteeind_dic[Nbin_key]

    # main reader func
    @verbose
    @announcer
    def reader_func(
            lidarname,
            mplfiledir=None, slicetup=None,
            starttime=None, endtime=None,
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
            - possible to cut size of array by removing the empty bins at the
              start
            - There is a very crude hardcode here that filters the directories
              under data, to only include relevant data.
              It finds the directories which start with '2'.
              This could be left alone for now.

        Parameters
            lidarname (str): directory name of lidar
            mplfiledir (str): non absolute filename of single mpl file, date
                              should be None
            slicetup (slice): slice tuple along time axis, only if mplfiledir
                              is specified
            start/endtime (datetime like): approx start/end time of data of
                                           interest, specified if mplfiledir
                                           is None.
                                           leave endtime empty if we want latest
                                           must be timezone aware
            filename (str): output will be a json file format, if specified

        Return
            mpldic (dict): dictionary of data in specified time frame.
                           keys are listed in .mplfmt.py.
                           dictionary is empty if the starttime is greater than
                           available files
        '''
        # catching wrong inputs
        try:
            if endtime <= starttime:
                raise ValueError(
                    f'{endtime=:} must be greater than {starttime=:} '
                )
        except TypeError:
            pass

        if mplfiledir:          # single file read
            mplsps = [[mplfiledir]]
        else:                   # finding files in data archive
            # finding files
            ## listing directories
            dates = np.array(list(filter(
                    lambda x: x[0] == '2',
                    os.listdir(SOLARISMPLDIR.format(lidarname))
                )))
            dates = LOCTIMEFN(dates, UTCINFO)
            dates.sort()
            dates = _lstfromtimes_func(dates, starttime, endtime, 1, 1)
            dates = list(map(lambda x: DATEFMT.format(x), dates))

            ## catergorizing files based on flags
            datedir_l = [DIRCONFN(SOLARISMPLDIR.format(lidarname), date)
                         for date in dates]
            eomtimes = DIRPARSEFN(FINDFILESFN(MPLEOMFILE, datedir_l),
                                  MPLEOMTIMEFIELD)
            eomtimes.sort()
            eomtimes = LOCTIMEFN(eomtimes, UTCINFO)
            mplfiles = FINDFILESFN(MPLFILE, datedir_l)
            mplfiles.sort()
            mplfiles = np.array(mplfiles)
            times = DIRPARSEFN(mplfiles, MPLTIMEFIELD)
            times = LOCTIMEFN(times, UTCINFO)
            if starttime > times[-1]:
                return {}

            try:
                # each ara in lst is scanpat, no need to worry about edge cases
                # as there are is an excess of mpl flags
                # here we select all eomtimes within the start and end time
                # all eom flags should fall within the mplfile times
                eomtimes = _lstfromtimes_func(eomtimes,
                                              starttime, endtime, 0, 1)
                seomtimes, eeomtimes = eomtimes[:-1], eomtimes[1:]
                mplsps = []
                for i, seomtime in enumerate(seomtimes):
                    startind = np.argmax(times > seomtime)
                    endind = np.argmax(times > eeomtimes[i])
                    if not endind:  # when the last eeomtime is
                        endind = None
                    mplsps.append(mplfiles[startind:endind])
                # to handle data that falls outside the eom flag boundries
                # due to scanpatterns that has not ended yet
                # logic is a little confusing, refer to log 20200807
                if mplsps:  # indicates that there were full scanpatterns data
                    if endind and eeomtimes[i] == eeomtimes[-1]:
                    # indicates the possibility of trailing files
                        if endind != len(times):
                            if endtime:
                                if endtime > eeomtimes[i]:
                                    mplsps.append(mplfiles[endind:])
                            else:
                                mplsps.append(mplfiles[endind:])
                else:           # probing for last scan pattern file
                    if endtime:
                        mplsps.append(mplfiles[_casetwoind:])
            except ValueError:
                # in the event there are no eom.flags, the collection of files
                # is treated as a single scan pattern
                mplsps = [mplfiles]

        # reading files
        ## reading files one scanpattern at a time
        print('reading files:')
        bytearA = []
        Nbin_arA = []
        for i, mplsp in enumerate(mplsps):
            if len(mplsp):
                print(f'\t scanpattern {i}:')
                # concat files related to scanpattern
                byteara = bytearray()
                for mplfile in mplsp:
                    print('\t{}'.format(mplfile))
                    with open(mplfile, 'rb') as mplf:
                        byteara += bytearray(mplf.read())
                # convert binary data to numpy array for reshaping
                byteara = np.frombuffer(byteara, dtype=np.byte)
                ## reading channel length from first measurement
                Nbin = np.frombuffer(byteara[Nbinsind:Nbineind],
                                     dtype=dtype_dic[Nbin_key])[0]
                Nbin_arA.append(Nbin)
                bytearA.append(byteara)
        ## editing indices for channels to fit the maxNbbin
        maxNbin = max(Nbin_arA)
        for channel_key in channel_keylst:  # to be used when convert ara to dic
            bytesize_dic[channel_key] = channelbytenum * maxNbin
        byteeind_dic = size2eind_func(bytesize_dic)
        bytesind_dic = size2sind_func(byteeind_dic)
        ## extending measurement to form rectangle block
        bytearAcopy = deepcopy(bytearA)
        bytearA = []
        for i, Nbin in enumerate(Nbin_arA):
            byteara = bytearAcopy[i]
            # reshape into rectangle
            bytesize = headersize + Nbin * len(channel_keylst) * channelbytenum
            bytearalen = len(byteara)
            numara = bytearalen//bytesize
            exind = -(bytearalen % bytesize)
            if exind:
                byteara = byteara[:exind]  # trim incomplete mea
            byteara = byteara.reshape(numara, bytesize)
            # extending rectangle
            append_ara = np.zeros((
                numara, (maxNbin - Nbin) * channelbytenum
            ), dtype=np.byte)
            cheind_a = headersize + np.cumsum(
                np.arange(len(channel_keylst)) * channelbytenum * Nbin
                )
            split_arA = np.split(byteara, cheind_a, axis=1)
            byteara = np.concatenate([
                split_ara if i == len(split_arA) - 1 else
                np.append(split_ara, append_ara, axis=1)
                for i, split_ara in enumerate(split_arA)
            ], axis=1)
            bytearA.append(byteara)
        ## concat scanpatterns together
        bytearA = np.concatenate(bytearA, axis=0)
        del(bytearAcopy)
        ## convert array of measurement bytes to dictionary
        ## channel arrays are flattened and need to be reshaped
        mpldic = {
            key:np.frombuffer(
                np.apply_along_axis(
                    lambda x: x[bytesind_dic[key]:byteeind_dic[key]].tobytes(),
                    axis=1, arr=bytearA
                ), dtype=dtype_dic[key]
            ) for key in wanted_keylst
        }
        ## scaling certain quantities to follow convention
        mpldic[bintime_key] = mpldic[bintime_key] * bintimefactor
        mpldic[energy_key] = mpldic[energy_key] * energyfactor
        ## converting time to datetime like object
        timedic = {key: mpldic[key] for key in time_keylst}
        timeara = pd.to_datetime(pd.DataFrame(timedic)).to_numpy('datetime64[s]')
        timeara = LOCTIMEFN(timeara, UTCINFO)
        mpldic[time_key] = timeara
        ## treating channels differently;
        ### reshape arrays into measurements
        for key in channel_keylst:
            chara = mpldic[key]
            mpldic[key] = chara.reshape(len(chara)//maxNbin, maxNbin)
        ### creating mask to accomodate different range bins and appended bins
        Nbin_ara = mpldic[Nbin_key]
        firstbin_ara = mpldic[firstbin_key]  # effectively Ndatabin_ara-Nbin_ara
        mpldic[mask_key] = (np.arange(maxNbin) >= firstbin_ara[:, None]) *\
            ~(np.arange(maxNbin) > Nbin_ara[:, None])
        ### creating range array
        Delr_ta = SPEEDOFLIGHT * mpldic[bintime_key]  # binsize
        mpldic[range_key] = Delr_ta[:, None] * np.arange(np.max(Nbin_ara))\
            + Delr_ta[:, None]/2\
            - (Delr_ta * firstbin_ara)[:, None]
        ## trimming
        mpldickeys = list(mpldic.keys())
        if starttime:
            # trimming can still take place even when reading single file
            startind = np.argmax(timeara >= starttime)
            if endtime:
                endind = np.argmax(timeara > endtime)
                if not endind:
                    endind = None
            else:
                endind = None
            mpldic = {key: mpldic[key][startind:endind] for key in mpldickeys}
        elif slicetup and mplfiledir:   # accord to slicetup
            mpldic = {key: mpldic[key][slicetup] for key in mpldickeys}
        print('total of {} measurements'.format(len(mpldic[time_key])))


        # writing to file
        if filename:
            # jsonify arrays
            mpljson = {
                key:mpldic[key].tolist()
                for key in mpldickeys
            }
            ## treating timestamp array differently
            mpljson[time_key] = (mpldic[time_key].astype(np.str)).tolist()

            with open(filename, 'w') as jsonfile:
                jsonfile.write(json.dumps(mpljson))

        # returning
        return mpldic

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

    from ...global_imports import *

    mpl_d = smmpl_reader(
        'smmpl_E2',
        starttime=LOCTIMEFN('202008040000', 8),
        endtime=LOCTIMEFN(dt.datetime.now(), 8)
    )
    ts_a = mpl_d['Timestamp']
    print(ts_a[0], ts_a[-1])

    # testsmmpl_boo = False
    # if testsmmpl_boo:

    #     starttime = pd.Timestamp('202007150000')
    #     endtime = pd.Timestamp('202007160000')
    #     mpldic = smmpl_reader(
    #         'smmpl_E2',
    #         starttime=starttime, endtime=endtime,
    #     )

    #     ch1_aara = mpldic['Channel #1 Data']
    #     ch2_aara = mpldic['Channel #2 Data']
    #     ch_amask = mpldic['Channel Data Mask']
    #     bintime_ara = mpldic['Bin Time']
    #     binnum_ara = mpldic['Number Bins']

    #     counter = 0
    #     for i, binnum in enumerate(binnum_ara):
    #         r_ara = np.cumsum(3e8*bintime_ara[i] * np.ones(binnum))
    #         plt.plot(r_ara, ch1_aara[i][ch_amask[i]], color='C0')
    #         plt.plot(r_ara, ch2_aara[i][ch_amask[i]], color='C1')
    #         counter += 1
    #         if counter > 100:
    #             break

    # else:
    #     lidarname, mpl_fn = 'mpl_S2S', '/home/tianli/SOLAR_EMA_project/codes/solaris_opcodes/product_calc/nrb_calc/testNRB_mpl_S2S.mpl'
    #     mpldic = mpl_reader(
    #         lidarname, mplfiledir=mpl_fn,
    #         slicetup=slice(OVERLAPPROFSTART, OVERLAPPROFEND, 1)
    #     )

    #     ch1_aara = mpldic['Channel #1 Data']
    #     ch2_aara = mpldic['Channel #2 Data']

    #     ch_amask = mpldic['Channel Data Mask']
    #     bintime_ara = mpldic['Bin Time']
    #     binnum_ara = mpldic['Number Data Bins']

    #     for i, binnum in enumerate(binnum_ara):
    #         if i in []:
    #             pass
    #         else:
    #             r_ara = np.cumsum(3e8*bintime_ara[i]/2/1000 * np.ones(binnum))
    #             plt.plot(r_ara, ch1_aara[i][ch_amask[i]], color='C0')
    #             plt.plot(r_ara, ch2_aara[i][ch_amask[i]], color='C1')

    # plt.yscale('log')
    # plt.show()
