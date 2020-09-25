# imports
import numpy as np


# params
_sumpad_l = [
    'Channel #1 Data',
    'Channel #2 Data',
    'Range',
]
_scalarmult_l = [
    'Background Average',
    'Background Average 2',
    'Bin Time'
]
_scalarmulterr_l = [
    'Background Std Dev',
    'Background Std Dev 2',
]
_scalardiv_l = [
    'Range'
]
_floordivision_l = [
    'Number Data Bins',
    'Number of Background Bins',
    'First Background Bin',
]
_zero_l = [
    'First data bin'
]
_maskkey = 'Channel Data Mask'


# main func
def main(mpl_d, rstep):

    # performing summation
    mask = list(mpl_d[_maskkey])
    for key in _sumpad_l:
        ara = mpl_d[key]
        rlen = ara.shape[-1]
        ara = list(ara)

        pad_a = np.array([])
        for i, a in enumerate(ara):
            q, r = divmod(len(a), rstep)
            if not r:
                sliceind = None
            else:
                sliceind = -r
            newa = a[mask[i]][:sliceind]
            newa = newa.reshape(q, rstep)
            newa = newa.sum(axis=-1)
            newalen = len(newa)
            pad_a = np.append(pad_a, newalen)

            ara[i] = np.append(
                newa,
                np.zeros(rlen-newalen)  # padding
            )

        mpl_d[key] = np.array(ara)

    ## setting mask
    mpl_d[_maskkey] = np.arange(rlen) < pad_a[:, None]

    # performing scalar multiplication
    for key in _scalarmult_l:
        mpl_d[key] *= rstep

    # performing scalar mulplication error propagation
    for key in _scalarmulterr_l:
        mpl_d[key] *= (rstep**0.5)

    # performing scalar division
    for key in _scalardiv_l:
        mpl_d[key] /= rstep

    # performing floor division
    for key in _floordivision_l:
        mpl_d[key] //= rstep

    # performing setting to zero
    for key in _zero_l:
        mpl_d[key] *= 0


    return mpl_d


# testing
if __name__ == '__main__':
    main()
