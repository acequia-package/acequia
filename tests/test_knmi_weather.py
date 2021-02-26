
"""
 testing module knmi_weather from acequia

"""
import acequia as aq

def hdr(msg):
    print()
    print('#','-'*50)
    print(msg)
    print('#','-'*50)
    print()


if __name__ == '__main__':

    hdr('# read valid file')
    srcpath = r'.\testdata\knmi\etmgeg_280.txt'
    wht = aq.KnmiWeather(srcpath)
    n = len(wht.rawdata)
    print(f'Number of data rows is {n}')

    hdr('# try to read invalid filepath')
    wht2 = aq.KnmiWeather('dummy')
    n = len(wht2.rawdata)
    print(f'Number of data rows is {n}')

    hdr('# get table with definitions and units')
    tbl = wht.units()
    print(tbl)

    hdr('# read all possible variables and one not possible')
    for name in ['prc','evp','rch','dummy']:
        n = len(wht.timeseries(name))
        print(f'Number of {name}: {n}')

