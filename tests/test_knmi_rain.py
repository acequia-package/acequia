
"""
 testing module knmi_rain from acequia

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
    srcpath = r'.\testdata\knmi\neerslaggeg_EENRUM_154.txt'
    prc = aq.KnmiRain(srcpath)
    n = len(prc.rawdata)
    print(f'Number of data rows is {n}')

    hdr('# try to read invalid filepath')
    prc2 = aq.KnmiRain('dummy')
    n = len(prc2.rawdata)
    print(f'Number of data rows is {n}')

    hdr('# get table with definitions and units')
    tbl = prc.units()
    print(tbl)

    hdr('# read all possible variables and one not possible')
    for name in ['prc','dummy']:
        n = len(prc.timeseries(name))
        print(f'Number of {name}: {n}')

