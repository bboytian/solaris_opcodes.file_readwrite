'''
.mpl file format for SigmaMPL2015R2.3 Manual, Data file version 5
'''
# import
import numpy as np


# supp function
def size2eind_func(bytesizedic):
    '''
    converts bytesizedic to byteinddic. end index of each data key
    '''
    vals, keys = list(bytesizedic.values()), list(bytesizedic.keys())
    vals = np.cumsum(vals)
    return dict(zip(keys, vals))

def size2sind_func(sinddic):
    '''
    converts bytesizedic to byteinddic. start index of each data key
    '''
    vals, keys = list(sinddic.values()), list(sinddic.keys())
    vals.pop()
    vals.insert(0, 0)
    return dict(zip(keys, vals))


# defining data
time_keylst = [
    'year',                   # to be handled seperately this does not follow
    'month',                  # exactly with the manual it is accomodated for
    'day',                    # pandas
    'hour',                   #
    'minute',                 #
    'second',                 #
]
channel_keylst = [
    'Channel #1 Data',
    'Channel #2 Data',
]
wanted_keylst = [
    # 'Unit Number',
    # 'Version Format',
    'year',                  # to be handled seperately, this does not follow
    'month',                 # exactly with the manual, it is accomodated for
    'day',                   # pandas
    'hour',                  #
    'minute',                #
    'second',                #
    'Shots Sum',
    'Trigger Frequency',        # for performance check
    'Energy Monitor',           # [nJ]
    'Temp #0',                  # Detector Temperature
    'Temp #1',                  # unknown
    'Temp #2',                  # Telescope Temperature
    'Temp #3',                  # Laser temperature
    'Temp #4',                  # unknown
    'Background Average',
    'Background Std Dev',
    # 'Number Channels',        # assumed to always be 2
    'Number Bins',
    'Bin Time',                 # half the bin size in temporal
    'Range Calibration',        # mainly zero, check for every new unit
    'Number Data Bins',
    'Scan Scenario Flag',       # check angle and remove
    'Number of Background Bins',
    'Azimuth Angle',
    'Elevation Angle',
    # 'Compass Degrees',
    # 'Lidar Site',
    # 'Wavelength',
    # 'GPS Latitude',
    # 'GPS Longitude',
    # 'GPS Altitude',
    'A/D Data Bad flag',        # for performance check, 0 is good, 1 is bad
    # 'DataFileVersion',          # version 5
    'Background Average 2',
    'Background Std Dev 2',
    'McsMode',
    'First data bin',           # noted to be zero, might be redundant
    'System Type',
    'Sync Pulses Seen Per Second',  # for performance, this values changes
    'First Background Bin',
    # 'Header Size',              # static 163,size of data before the channels
    'Weather Station Used',
    'Weather Station: Inside Temperature',
    'Weather Station: Outside Temperature',
    'Weather Station: Inside Humidity',
    'Weather Station: Outside Humidity',
    'Weather Station: Dew Point',
    'Weather Station: Wind Speed',
    'Weather Station: Wind Direction',
    'Weather Station: Barometric Pressure',
    'Weather Station: Rain Rate',
    'Channel #1 Data',        # [MHz]
    'Channel #2 Data',        # [MHz]
]
dtype_dic = {
    'Unit Number':np.uint16,
    'Version Format':np.uint16,
    'year':np.uint16,
    'month':np.uint16,
    'day':np.uint16,
    'hour':np.uint16,
    'minute':np.uint16,
    'second':np.uint16,
    'Shots Sum':np.uint32,
    'Trigger Frequency':np.int32,
    'Energy Monitor':np.uint32,
    'Temp #0':np.uint32,
    'Temp #1':np.uint32,
    'Temp #2':np.uint32,
    'Temp #3':np.uint32,
    'Temp #4':np.uint32,
    'Background Average':np.float32,
    'Background Std Dev':np.float32,
    'Number Channels':np.uint16,
    'Number Bins':np.uint32,
    'Bin Time':np.float32,
    'Range Calibration':np.float32,
    'Number Data Bins':np.uint16,
    'Scan Scenario Flag':np.uint16,
    'Number of Background Bins':np.uint16,
    'Azimuth Angle':np.float32,
    'Elevation Angle':np.float32,
    'Compass Degrees':np.float32,
    'Lidar Site':np.char,       # this is not correct
    'Wavelength':np.uint16,
    'GPS Latitude':np.float32,
    'GPS Longitude':np.float32,
    'GPS Altitude':np.float32,
    'A/D Data Bad flag':np.int8,
    'DataFileVersion':np.int8,
    'Background Average 2':np.float32,
    'Background Std Dev 2':np.float32,
    'McsMode':np.int8,
    'First data bin':np.uint16,
    'System Type':np.int8,
    'Sync Pulses Seen Per Second':np.uint16,
    'First Background Bin':np.uint16,
    'Header Size':np.uint16,
    'Weather Station Used':np.int8,
    'Weather Station: Inside Temperature':np.float32,
    'Weather Station: Outside Temperature':np.float32,
    'Weather Station: Inside Humidity':np.float32,
    'Weather Station: Outside Humidity':np.float32,
    'Weather Station: Dew Point':np.float32,
    'Weather Station: Wind Speed':np.float32,
    'Weather Station: Wind Direction':np.int16,
    'Weather Station: Barometric Pressure':np.float32,
    'Weather Station: Rain Rate':np.float32,
    'Channel #1 Data':np.float32,
    'Channel #2 Data':np.float32,
}
## config dependent
bytesize_dic = {
    'Unit Number':2,
    'Version Format':2,
    'year':2,
    'month':2,
    'day':2,
    'hour':2,
    'minute':2,
    'second':2,
    'Shots Sum':4,
    'Trigger Frequency':4,
    'Energy Monitor':4,
    'Temp #0':4,
    'Temp #1':4,
    'Temp #2':4,
    'Temp #3':4,
    'Temp #4':4,
    'Background Average':4,
    'Background Std Dev':4,
    'Number Channels':2,
    'Number Bins':4,
    'Bin Time':4,
    'Range Calibration':4,
    'Number Data Bins':2,
    'Scan Scenario Flag':2,
    'Number of Background Bins':2,
    'Azimuth Angle':4,
    'Elevation Angle':4,
    'Compass Degrees':4,
    'Lidar Site':6,
    'Wavelength':2,
    'GPS Latitude':4,
    'GPS Longitude':4,
    'GPS Altitude':4,
    'A/D Data Bad flag':1,
    'DataFileVersion':1,
    'Background Average 2':4,
    'Background Std Dev 2':4,
    'McsMode':1,
    'First data bin':2,
    'System Type':1,
    'Sync Pulses Seen Per Second':2,
    'First Background Bin':2,
    'Header Size':2,
    'Weather Station Used':1,
    'Weather Station: Inside Temperature':4,
    'Weather Station: Outside Temperature':4,
    'Weather Station: Inside Humidity':4,
    'Weather Station: Outside Humidity':4,
    'Weather Station: Dew Point':4,
    'Weather Station: Wind Speed':4,
    'Weather Station: Wind Direction':2,
    'Weather Station: Barometric Pressure':4,
    'Weather Station: Rain Rate':4,
    'Channel #1 Data':0,     # to be filled in by reader
    'Channel #2 Data':0      # 1000 -> 30m binsize, 2000 -> 15m binsize
}


byteeind_dic = size2eind_func(bytesize_dic)
bytesind_dic = size2sind_func(byteeind_dic)


# for import
import_dic = {
    'time_key':'Timestamp',
    'range_key':'Range',
    'mask_key':'Channel Data Mask',
    'pad_key':'Pad',
    'headersize':163,
    'bintimefactor':0.5,
    'energyfactor':1e-3,
    'channelbytenum':4,

    'time_keylst':time_keylst,
    'channel_keylst':channel_keylst,
    'wanted_keylst':wanted_keylst,

    'dtype_dic':dtype_dic,
    'bytesize_dic':bytesize_dic,
    'bytesind_dic':bytesind_dic,
    'byteeind_dic':byteeind_dic,
}

# testing
if __name__ == '__main__':
    print(byteeind_dic)
