'''
Hardcode file concatenator and trimmer
'''
def main(dst_d, file_dlst, fronttrim, endtrim, meabytesize):
    byte_a = bytearray()
    for file_d in file_dlst:
        with open(file_d, 'rb') as file_f:
            byte_a += bytearray(file_f.read())

    print(len(byte_a))
    if endtrim == 0:
        endind = None
    else:
        endind = meabytesize * endind
    byte_a = byte_a[meabytesize*fronttrim:meabytesize*endtrim]
    print(len(byte_a))

    with open(dst_d, 'wb') as dst_f:
        dst_f.write(byte_a)


if __name__ == '__main__':
    import datetime as dt
    import os
    import os.path as osp

    from ..globalimports import *

    lidarname = 'mpl_S2S'
    date = dt.datetime(2020, 6, 2)
    data_d = osp.join(SOLARISMPLDIR.format(lidarname), DATEFMT.format(date))
    file_dlst = list(filter(
        lambda x: MPLFILE[MPLTIMEIND:] in x,
        [osp.join(data_d, fn) for fn in os.listdir(data_d)]
    ))
    file_dlst.sort()

    bintime = 1e-7              # assumed for 15m
    dst_d = osp.join('/home/tianli/SOLAR_EMA_project/codes/solaris_opcodes/product_calc/nrb_calc/testNRB_mpl_S2S.mpl')

    main(dst_d, file_dlst, 0, 0, 6547)
