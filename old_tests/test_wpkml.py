from collections import OrderedDict
import pandas as pd
from pandas import DataFrame, Series
from acequia import WpKml
import acequia as aq

if __name__ == '__main__':


    sourcepath = '.\\testdata\\waypoints\\pmgloc.csv'
    outdir = '.\\output\\kml\\'

    pmgloc = pd.read_csv(sourcepath)
    pmgloc = pmgloc.replace({-1:'true',0:'false'})


    # test without formatting
    pts = WpKml(pmgloc,label="nitgcode",xcoor="xcr",ycoor="ycr")
    pts.writekml(f'{outdir}pmv-noformatting.kml')


    # test with styledict and stylecol
    styledict_truefalse = OrderedDict([
        ("true",
            {"iconshape":"circle","iconscale":1.0,
             "iconcolor":"#0000FF","labelscale":0.7,
             "labelcolor":"FFFFFF"}),
        ("false",
            {"iconshape":"circle","iconscale":1.0,
             "iconcolor":"#FF00FF","labelscale":0.7,
             "labelcolor":"FFFFFF"}),
        ])

    pts = WpKml(pmgloc,label="nitgcode",xcoor="xcr",ycoor="ycr",
                styledict=styledict_truefalse, stylecol="ispmg")
    pts.writekml(f'{outdir}pmv-styledict-and-stylecol.kml')


    # test with only stylecol and no styledict
    pts = WpKml(pmgloc,label="nitgcode",xcoor="xcr",ycoor="ycr",
                stylecol="iskrw")
    pts.writekml(f'{outdir}pmv-stylecol-nostyledict.kml')


