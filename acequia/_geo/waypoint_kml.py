"""
Convert pd.DataFrame with coordinates to KML file

Created on 12-05-2013. Migrated to Acequia on 27-06-2020
Depends on package SimpleKML

"""

import os
import os.path
import warnings
from collections import OrderedDict

import pandas as pd
from pandas import DataFrame, Series
import numpy as np
import simplekml as skml

from .coordinate_conversion import CrdCon as CrdCon


sep = ','


class WpKml:
    """ Save Pandas DataFrame with waypoints in RD-coordinates to KML """

    ICONSHAPES = {'square' : 'http://maps.google.com/mapfiles/kml/shapes/placemark_square.png',
                  'circle' : 'http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png',
                  'cross'  : 'http://maps.google.com/mapfiles/kml/shapes/cross-hairs.png'}

    COLORS = {
      'white'       : '#FFFFFF',
      'brightgreen' : '#33FF00',
      'mossgreen'   : '#CCFF00',
      'deepyellow'  : '#FFFF00',
      'darkyellow'  : '#FFCC00',
      'orange'      : '#FF6600',
      'lightblue'   : '#99CCFF',
      'deepblue'    : '#0000FF',
      'brightpurple': '#CC00CC',
      'darkpurple'  : '#6600CC',
      'pink'        : '#FF00FF',
      'brightred'   : '#FF0000'}


    DEFAULT_STYLEDICT = OrderedDict([
        ('1',{'iconshape':'square','iconscale':1.0,'iconcolor':'#0c7cac',
              'labelscale':0.7,'labelcolor':'#FFFFFF'}),
        ('2',{'iconshape':'square','iconscale':1.0,'iconcolor':'#ac0b35',
              'labelscale':0.7,'labelcolor':'#FFFFFF'}),
        ('3',{'iconshape':'square','iconscale':1.0,'iconcolor':'#9e00b5',
              'labelscale':0.7,'labelcolor':'#FFFFFF'}),
        ('4',{'iconshape':'square','iconscale':1.0,'iconcolor':'#54a910',
              'labelscale':0.7,'labelcolor':'#FFFFFF'}),
        ('5',{'iconshape':'square','iconscale':1.0,'iconcolor':'#f69601',
              'labelscale':0.7,'labelcolor':'#FFFFFF'}),
        ('6',{'iconshape':'square','iconscale':1.0,'iconcolor':'#0011ff',
              'labelscale':0.7,'labelcolor':'#FFFFFF'}),
        ('7',{'iconshape':'square','iconscale':1.0,'iconcolor':'#ff00c1',
              'labelscale':0.7,'labelcolor':'#FFFFFF'}),
        ('9',{'iconshape':'square','iconscale':1.0,'iconcolor':'#ffff00',
              'labelscale':0.0,'labelcolor':'#FFFFFF'}),
        ])


    missing_style = { 'iconshape':'cross',
                      'iconscale':1.0,
                      'iconcolor':'#FFFFFF',
                      'labelscale':0.7,
                      'labelcolor':'#FFFFFF'}


    def __repr__(self):
        return f'{self.__class__.__name__} (n={len(self.wplist)})'


    def __init__(self,wplist,label=None,xcoor=None,ycoor=None,
        styledict=None, stylecol=None):
        """Create KML file object from pd.DataFrame with waypoints

        Parameters
        ----------
        wplist : pd.DataFrame
            points with coordinates given in Standard Dutch Grid
        label : str
            columnname in wplist used for naming kml waypoints
        xcoor : float, optinal
            xcoordinate in RD
        ycoor : float, optional
            ycoordinate in RD
        styledic : dictionary, optional
            style definitions for each marker
        stylecol : str, optional
            column name for assigning styles

        Examples
        --------
        >>>sourcepath = '.\\testdata\\waypoints\\pmgloc.csv'
        >>>pmgloc = pd.read_csv(sourcepath)
        >>>pts = WpKml(pmgloc,label="nitgcode",xcoor="xcr",ycoor="ycr")
        >>>outdir = '.\\output\\kml\\'
        >>>pts.writekml(f'{outdir}pmv2019-noformatting.kml')

        >>>styledict_truefalse = {
                "true":
                    {"iconshape":"circle","iconscale":1.0,
                     "iconcolor":"#0000FF","labelscale":0.7,
                     "labelcolor":"FFFFFF"}),
                {"false":
                    {"iconshape":"circle","iconscale":1.0,
                     "iconcolor":"#FF00FF","labelscale":0.7,
                     "labelcolor":"FFFFFF"},}
        >>>pts = WpKml(pmgloc,label="nitgcode",xcoor="xcr",ycoor="ycr",
                       styledict=styledict_truefalse, stylecol="ispmg")
        >>>pts.writekml(f'{outdir}pmv-styledict-and-stylecol.kml')

        Notes
        -----
        If no values for xcoor,ycoor are given, column names with
        coordinates will be inferred from wplist column names.
        
        """

        self.kml = skml.Kml()
        self.defaultstyle = self._basestyle()

        if not isinstance(wplist, pd.DataFrame):
            raise TypeError('Variable wplist must be a pandas dataframe.')        

        if wplist.empty:
            raise ValueError('Variable wplist cannot be empty.')

        self.wplist = wplist.copy()
        self.wplist.columns = self.wplist.columns.str.lower()

        # set coordinates
        self.xcoor,self.ycoor = self._coordinate_columns(xcoor,ycoor)

        notlon = 'lon' not in self.wplist.keys()
        notlat = 'lat' not in self.wplist.keys()
        if notlon or notlat:
            self.wplist['lon'],self.wplist['lat'] = self.wgs84_coords

        # set label column name
        if label is None:
            self.label = self.wplist.keys()[0]

        if label.lower() in self.wplist.keys():
            self.label = label.lower()
        else:
            firstcol = list(self.wplist)[0]
            self.label = firstcol
            warnings.warn((f'Value {label} for label column not found '
                f'in {self.wplist} column names. Column {firstcol} is ',
                f'used for KML labels.'))

        if stylecol is not None:
            stylecol = stylecol.lower()

        # set kml waypoint styles
        # TODO: Test function _validate_styledict
        self.styledict, self.stylecol = self._validate_styledict(styledict,stylecol)
        self.pointstyles = OrderedDict()
        for iconkey,icondef in self.styledict.items():
            basestyle = self._basestyle()
            self.pointstyles[iconkey] = self._changestyle(basestyle,icondef)


    def _coordinate_columns(self,xcoor=None,ycoor=None):
        """Return names of columns with xcoor,ycoor """

        if xcoor is None:
            xlist = ['xcoor','xrd','x']
            for x in xlist:
                if x in self.wplist.keys(): 
                    xcol = x
        else:
            if xcoor.lower() in self.wplist.keys(): 
                xcol = xcoor.lower()
            else:
                msg = f'No column with xcoor value available.'
                raise ValueError(msg)

        if ycoor is None:
            ylist = ['ycoor','yrd','y']
            for y in ylist:
                if y in self.wplist.keys(): 
                    yxol = y
        else:
            if ycoor.lower() in self.wplist.keys():
                ycol = ycoor.lower()
            else:
                msg = f'No column with ycoor value available.'
                raise ValueError(msg)

        return xcol,ycol

    @property
    def wgs84_coords(self):
        """Return lon and lat as ps.Series

        Returns
        -------
        lon,lat
        """
        crdcon = CrdCon()
        lon = self.wplist.apply(
                lambda x: crdcon.convert_RDtoWGS84(float(x[self.xcoor]),
                float(x[self.ycoor]))['Lon'],axis=1)
        lat = self.wplist.apply(
                lambda x: crdcon.convert_RDtoWGS84(float(x[self.xcoor]),
                float(x[self.ycoor]))['Lat'],axis=1)
        return lon,lat

    def _validate_styledict(self,styledict,stylecol):
        """ validate styledict and stylecol """

        if (stylecol is not None) and (styledict is not None):

            # fill nans in column stylecol
            nanrows = self.wplist[self.wplist[stylecol].isnull()]
            if len(nanrows) !=0:
                fillnans = self.wplist[stylecol].replace(
                            np.nan,'missing',inplace=False)
                self.wplist[stylecol] = fillnans
                styledict['missing'] = self.missing_style


            # check styledict for missing keys
            # change stylecol to None if keys are missing from styledict
            missing = list(set(self.wplist[stylecol].unique()) 
                           - set(styledict.keys()))
            if len(missing)!=0: #not all(elem in wplabels for elem in styledict.keys()):               
                msg = ''.join([
                        f'Custom style dictionary styledict is missing ',
                        f'labels from waypoint column {stylecol}. ',
                        f'No formatting applied.\\n',
                        f'Missing labels are: {missing}'])
                warnings.warn(msg,UserWarning)
                stylecol = None


        if (stylecol is not None) and (styledict is None):

            wplabels = self.wplist[stylecol].unique()
            defaultkeys = list(self.DEFAULT_STYLEDICT.keys())
            if len(wplabels) <= len(defaultkeys):
                newstyles = []
                for i,wplabel in enumerate(wplabels):
                    newstyles.append((wplabel,self.DEFAULT_STYLEDICT[defaultkeys[i]]))
                styledict = OrderedDict(newstyles)
                #self.pointstyles = self._styles_from_dict(self.styledict)

            else:
                lenwp = len(wplabels)
                lenkeys = len(defaultkeys)
                message = ''.join(
                  [f'\nTo many unique values in waypoint stylecolumn '
                   f'{stylecol}.\n',
                   f'Stylecolumn {stylecol} contains {lenwp} values.\n',
                   f'Default style definitions contains {lenkeys} values.\n',
                   f'No formatting of waypoints applied.\n',])
                warnings.warn(message,UserWarning)
                styledict = {'default' : self.DEFAULT_STYLEDICT['1']}
                stylecol = None


        if (stylecol is None) and (styledict is not None):
            styledict = next(iter(styledict.values())) # abitrary single element from styledict

        if (stylecol is None) and (styledict is None):
                styledict = {'default' : self.DEFAULT_STYLEDICT['1']}


        """
        elif ((self.stylecol is None) and isinstance(self.styledict,dict)):
        if (stylecol is None) and (styledict is not None):
        if isinstance(styledict,dict):
            self.pointstyles = self._styles_from_dict(styledict)
        """
        return styledict,stylecol


    def _styles_from_dict(self,icondict):
        """Return OrderedDict of KML pointstyles with keys from icondict
        as point style names 

        Parameters
        ----------
        icondict : dict
            valid iconstyle dictionary


        Returns
        -------
        Ordereddict with KML pointstyles

        """
        pointstyles = OrderedDict()
        for iconkey,icondef in icondict.items():
            pointstyles[iconkey] = self._changestyle(
                                   kmlstyle=self._basestyle(),
                                   icondef=icondef)
        return pointstyles


    def _basestyle(self,icondict=None):
        """ Return default KML icon style """

        basestyle = skml.Style()
        basestyle.labelstyle.color = skml.Color.hex(self.COLORS['white'])
        basestyle.labelstyle.scale = 0.7
        basestyle.iconstyle.icon.href = self.ICONSHAPES['square']
        basestyle.iconstyle.scale = 0.9
        basestyle.iconstyle.color= skml.Color.hex('33FF33')

        # only show desciption in balloon
        basestyle.balloonstyle.text = r'$[description]' 

        if icondict is not None:
            basestyle = self._changestyle(kmlstyle=basestyle,
                                          icondef=icondict)

        return basestyle


    def _changestyle(self,kmlstyle=None,icondef={}):
        """ Change existing kml style with definitions given in dictionary

        Parameters
        ----------
        kmlstyle : skml.style
            existing skml style object
        icondef : dict
            dictionary with items and values to change

        Returns
        -------
        KML style object

        """

        if not isinstance(kmlstyle,skml.styleselector.Style):
            msg = f'Variable {kmlstyle} must be a simplekml style object.'
            raise TypeError(msg)

        if not isinstance(icondef,dict):
            msg = f'Variable {icondef} must be a dictionary not {type(icondef)}.'
            raise TypeError(msg)

        for itemkey in icondef.keys():

            if itemkey=='iconshape':
                icon_name = icondef['iconshape']
                kmlstyle.iconstyle.icon.href = self.ICONSHAPES[icon_name]

            elif itemkey=='iconscale':
                kmlstyle.iconstyle.scale = icondef['iconscale']

            elif itemkey=='iconcolor':
                mycolor = icondef['iconcolor']
                if mycolor.startswith('#'): 
                    mycolor = mycolor[1:]               
                kmlstyle.iconstyle.color= skml.Color.hex(mycolor)

            elif itemkey=='labelcolor':
                labelcolor = icondef['labelcolor']
                if labelcolor.startswith('#'): 
                    mycolor = mycolor[1:]               
                kmlstyle.labelstyle.color = skml.Color.hex(labelcolor)

            elif itemkey=='labelscale':
                kmlstyle.labelstyle.scale = float(icondef['labelscale'])

        return kmlstyle


    def _addcustomstyle(self,name,colorname=None,hexcolor=None,
        iconshape=None,styledic=None):
        """Add new custom KML waypoint style to customstyles"""

        newstyle = self.basestyle()

        if isinstance(styledic,dict):

            newstyle.iconstyle.icon.href = self.icons[styledic['iconshape']]
            newstyle.iconstyle.scale = styledic['iconscale']

            mycolor = styledic['iconcolor']
            if mycolor.startswith('#'): 
                mycolor = mycolor[1:]               
            newstyle.iconstyle.color= skml.Color.hex(mycolor)

            labelcolor = styledic['labelcolor']
            if labelcolor.startswith('#'): 
                mycolor = mycolor[1:]               
            newstyle.labelstyle.color = skml.Color.hex(labelcolor)
            newstyle.labelstyle.scale = float(styledic['labelscale'])

        if colorname is not None:

            if colorname in self.COLORS.keys(): 
                hexcolor = self.COLORS[colorname]

            if hexcolor.startswith('#'): 
                hexcolor = int(hexcolor[1:])

            newstyle.iconstyle.color= skml.Color.hex(hexcolor)

        if iconshape is not None:

            if iconshape in self.icons.keys(): 
                iconshape = self.icons[iconshape]
            else: 
                iconshape = self.icons['square']
            newstyle.iconstyle.icon.href = iconshape

        self.customstyles[name] = newstyle
        return self.customstyles[name]


    def writekml(self,kmlfile,metadata=True,cols=None):
        """ Write list of waypoints in RD to KML

        Parameters
        ----------
        kmlname : str
            name of kml file
        metadata : True,False, optional
            add metadata in bollontext (True) or not (False)
        cols : list of str, optional
            list of column names to add to balloontext of waypoints
        """
        #TODO: check if kmlfile path exists

        # Make list of fields to write to balloontext
        ##self.ballooncols = cols


        for idx, wp in self.wplist.iterrows():
   
            pnt = self.kml.newpoint(name=wp[self.label], 
                        coords=[(wp['lon'],wp['lat'])])  # lon, lat optional height
            pnt.snippet.maxlines = 0
            pointname = r'<font color='#000' size='+1'><strong>'+wp[self.label]+'</strong></font><br>'

            # assign waypoint style
            if (isinstance(self.stylecol,str) and isinstance(self.styledict,dict)):
                pnt.style = self.pointstyles[wp[self.stylecol]]
            else:
                pnt.style = self._basestyle(icondict=self.styledict)

            if metadata is True:

                if cols is None:
                    cols = list(wp.index)
                else:
                    cols = [x.lower() for x in cols]
                fields = zip(wp[cols].index, wp[cols].values)

                for ifield,field in enumerate(fields):
                    if ifield==0: 
                        tekst = field[0]+': '+str(field[1])+'<br>'
                    else: 
                        tekst = tekst + field[0]+': '+str(field[1])+'<br>'
            
                # save balloontext to kml
                pnt.description = tekst

        self.kml.save(kmlfile)

        return self.kml

