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

    from ..global_imports.solaris_opcodes import *

    lidarname = 'mpl_S2S'
    date = dt.datetime(2020, 6, 2)
    data_d = DIRCONFN(SOLARISMPLDIR.format(lidarname), DATEFMT.format(date))
    file_dlst = list(filter(
        lambda x: DIRPARSEFN(MPLFILE, MPLEXTFIELD) in x,
        [DIRCONFN(data_d, fn) for fn in os.listdir(data_d)]
    ))
    file_dlst.sort()

    bintime = 1e-7              # assumed for 15m
    dst_d = DIRCONFN('/home/tianli/SOLAR_EMA_project/codes/solaris_opcodes/product_calc/nrb_calc/testNRB_mpl_S2S.mpl')

    main(dst_d, file_dlst, 0, 0, 6547)
