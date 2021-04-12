





import acequia as aq


def hdr(msg):
    print()
    print('#','-'*50)
    print(msg)
    print('#','-'*50)
    print()


if __name__ == '__main__':


    hdr('# test SwSeries.from_dinocsv')
    dnpath = r'.\testdata\dinosurface\P13D0013.csv'
    dsw = aq.SwSeries.from_dinocsv(dnpath)
    print(dsw)

    hdr('# SwSeries.name()')
    print(dsw.name())

    hdr('# SwSeries.remarks()')
    print(dsw.remarks())

    hdr('# SwSeries.stats()')
    print(dsw.stats())



