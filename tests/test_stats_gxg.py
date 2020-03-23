

"""
    Test GxG object 

"""


from acequia import GwSeries
from acequia import GxG
from acequia import GwList
import acequia as aq


print(__name__)

if __name__ == '__main__':

    if 0:
        sourcedir = ".\\testdata\\dinogws\\"
        srcfile = "B28A0475002_1.csv"
        gw = aq.GwSeries.from_dinogws(sourcedir+srcfile)
        sr = gw.heads(ref='datum')


    if 0:

        srcpath = r'D:\THOMAS\PY3\acequia_develop\testdata\json\B29A0850_1.json'
        gw = aq.GwSeries.from_json(srcpath)

    if 1:

        #srcdir = 'D:\\THOMAS\\PY3\\acequia_develop\\testdata\\json\\'
        srcdir = f'.\\testdata\\json\\'
        gwsr = GwList(srcdir=srcdir,srctype='json')
        for i,gw in enumerate(gwsr):
            if 1<10:
                print(i,gw)        