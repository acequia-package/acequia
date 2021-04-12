
import acequia as aq


def hdr(msg):
    print()
    print('#','-'*50)
    print(msg)
    print('#','-'*50)
    print()


if __name__ == '__main__':


    hdr('# Test Dinocsv reader object init method')

    dnpath = r'.\testdata\dinosurface\P13D0013.csv'
    dns = aq.DinoSurfaceLevel(dnpath)
    print(dns)

    hdr('# Test Dinocsv.locprops() ')
    print(dns.locprops())

    hdr('# Test Dinocsv.levels() ')
    print(f'Number of measured levels is {len(dns.levels())}.')
    print(dns.levels().head(3))

    hdr('# Test Dinocsv.locprops() ')
    print(dns.remarks())

    hdr('# Test Dinocsv.metadata() ')
    print(dns.metadata())


