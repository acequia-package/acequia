


import acequia as aq

def hdr(msg):
    print()
    print('#','-'*50)
    print(msg)
    print('#','-'*50)
    print()


if __name__ == '__main__':

    #srcpath = r'D:\py3\gwdata\knmi\weather\etmgeg_280.txt'
    srcpath = r'.\testdata\knmi\etmgeg_280.txt'
    wth = aq.KnmiWeather(srcpath)
    prc = wth.timeseries('prc')
    evp = wth.timeseries('evp')

    hdr('Test init MeteoDrought')
    drg = aq.MeteoDrought(prc,evp)
    print(drg)

    hdr('Test MeteoDrought.recharge()')
    rch = drg.recharge()
    print('Total number of days with known recharge is ',len(rch))

    hdr('Test MeteoDrought.summer_recharge()')
    rchsmr = drg.summer_recharge()
    print('Number of summers is ',len(rchsmr))

    hdr('Test MeteoDrought.daycum()')
    daycum = drg.daycum()

    hdr('Test MeteoDrought.summercum()')
    summercum = drg.summercum()
    print('Cumulative sum of 2018 is:',summercum[2018])

    hdr('Test MeteoDrought.summersum()')
    summersum = drg.summersum()
    print('Summer sum of 2018 is:',summersum[2018])
