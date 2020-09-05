from collections import OrderedDict
import pandas as pd
from pandas import DataFrame, Series
#import numpy as np
#import simplekml as skml
from acequia import WpKml
import acequia as aq

if __name__ == '__main__':

    ##pts = aq.WpKml()
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
    pts.writekml(f'{outdir}pmv-stylecolnostyledict.kml')



    if 0:

        filepath = "PMV2019.xlsx"
        dfwp = pd.read_excel(filepath)

        # test basic functionality without formatting


        # test with styldict and stylecol

        styledict_mpbeheer = OrderedDict([
            ("Provincie Overijssel",
                {"iconshape":"circle","iconscale":1.0,
                 "iconcolor":"b0e0e6","labelscale":0.7,
                 "labelcolor":"FFFFFF"}),
            ("Landschap Overijssel",
                {"iconshape":"circle","iconscale":1.0,
                 "iconcolor":"ff00ff","labelscale":0.7,
                 "labelcolor":"FFFFFF"}),
            ("Staatsbosbeheer",
                {"iconshape":"circle","iconscale":0.9,
                 "iconcolor":"00ff00","labelscale":0.7,
                 "labelcolor":"FFFFFF"}),
            ("Natuurmonumenten",
                {"iconshape":"square","iconscale":1.0,
                 "iconcolor":"00ff00","labelscale":0.7,
                 "labelcolor":"FFFFFF"}),
            ("Vitens",
                {"iconshape":"square","iconscale":1.0,
                 "iconcolor":"daa520","labelscale":0.7,
                 "labelcolor":"FFFFFF"}),
            ("Provincie Drenthe",
                {"iconshape":"circle","iconscale":1.0,
                 "iconcolor":"cccccc","labelscale":0.7,
                 "labelcolor":"FFFFFF"}),
            ])

        pts = WpKml(dfwp,label="WERKNAAM",xcoor="XCOOR",ycoor="YCOOR",
                    styledict=styledict_mpbeheer, stylecol="MPBEHEER")
        pts.writekml("pmv2019-styledict-and-stylecol.kml")

    if 0:


        styledic_two_icons = {
            "ACTUEEL"  : {"iconshape":"circle","iconscale":1.0,"iconcolor":"#ffc0cb","labelscale":0.7,"labelcolor":"FFFFFF"},
            "HISTORISCH" : {"iconshape":"circle","iconscale":1.0,"iconcolor":"#00ffff","labelscale":0.7,"labelcolor":"FFFFFF"}
        }

        # test with
        pts = WpKml(dfwp,label="WERKNAAM",xcoor="XCOOR",ycoor="YCOOR",
                    styledict=styledic_two_icons)
        pts.writekml(kmlname="pmv2019-singlestyle.kml")
