"""
Class BroGldXml reads XML with Groundwater Level Data from BRO XML 
file and also accepts result from a REST request.

"""
import os
import warnings
from pandas import Series,DataFrame
import pandas as pd
#import xml.etree.ElementTree as ET
import lxml.etree as ET

class BroGldXml:
    """Read BRO Groundwater Level Data in XML tree format."""

    """
    NS = {
        "":"http://www.broservices.nl/xsd/brocommon/3.0",
        "ns6":"http://www.opengis.net/om/2.0",
        "ns5":"http://www.opengis.net/waterml/2.0",
        "ns8":"http://www.isotc211.org/2005/gco",
        "ns7":"http://www.opengis.net/swe/2.0",
        "ns9":"http://www.isotc211.org/2005/gmd",
        "ns10":"http://www.broservices.nl/xsd/gldcommon/1.0",
        "ns2":"http://www.opengis.net/gml/3.2",
        "ns4":"http://www.broservices.nl/xsd/dsgld/1.0",
        "ns3":"http://www.w3.org/1999/xlink",
        }
    """

    GLDPROPTAGS = [
        ('dispatchTime','dispatchTime'),
        ('broIdGld','broId'),
        ('deliveryAccountableParty','deliveryAccountableParty'),
        ('qualityRegime','qualityRegime'),
        ('objectRegistrationTime','objectRegistrationTime'),
        ('registrationStatus','registrationStatus'),
        ('latestAdditionTime','latestAdditionTime'),
        ('corrected','corrected'),
        ('underReview','underReview'),
        ('deregistered','deregistered'),
        ('reregistered','reregistered'),
        ('researchFirstDate','ns4:researchFirstDate'),
        ('researchLastDate','ns4:researchLastDate'),
        ('broIdGmw','ns10:broId'),
        ('tubeNumber','ns10:tubeNumber'),
        ]


    def __init__(self,tree):
        """
        Parameters
        ----------
        tree : ElementTree tree object
            Valid XML tree with groundwater level measurement data (GLD).

        Example
        -------
        gld = BroGld(<elementtree>)
        """

        self._tree = tree
        self._root = self._tree.getroot()
        self.NS = self._root.nsmap
        
        ##self.gldprops = self._gldprops(self._root)
        ##self.proces = self._proces(self._root)
        ##self.levels = self._levels(self._root)
        ##self.tsprops = self._tsprops(self._root)


    def __repr__(self):
        return self.gldprops['broIdGld']


    @classmethod
    def from_file(cls,xmlpath):
        """Read BRO GLD object from XML file.

        Parameters
        ----------
        xmlpath : str
            Valid filepath to XML file with groundwater level measurements.

        Returns
        -------
        BroGldXml object

        Example
        -------
        gld = BroGldXml.from_file(<valid xml filepath>)
        """

        if not os.path.isfile(xmlpath):
            raise ValueError(f'Invalid filepath: "{xmlpath}".')
        tree = ET.parse(xmlpath)
        return cls(tree)


    @property
    def gldprops(self):
        """Get level data properties."""
        gldprops = {}
        for key,tag in self.GLDPROPTAGS:
            node = self._root.find(f'.//{tag}',self.NS)
            if node is not None:
                gldprops[key]=node.text
            else:
                gldprops[key]=''
        return Series(gldprops,name='GldProperties')

    @property
    def procesprops(self):
        """Collect observation process parameters."""
        propslist = []
        
        # collect paramaters for all time series
        for node in self._root.iterfind('.//ns5:ObservationProcess',self.NS):
            props = {}
            
            # get time series id
            attdict = node.attrib
            tsid = [attdict[key] for key in attdict.keys()][0]
            tsid = tsid.split('_')[1]

            # get all paramaters for time series
            for subnode in node.iterfind('.//ns6:NamedValue',self.NS):
                item = subnode.find('.//ns6:value',self.NS)
                prop = item.attrib['codeSpace'].split(':')[-1]
                props = {
                    'proces':tsid,
                    'parameter':prop,
                    'value':item.text,
                    }
                propslist.append(props)
                
        return DataFrame(propslist)
        
    @property
    def obs(self):
        """Get all observation data."""
        tslist = []
        for srnode in self._root.iterfind('.//ns5:MeasurementTimeseries',self.NS):

            # get time series id
            attdict = srnode.attrib
            tsid = [attdict[key] for key in attdict.keys()][0]
            tsid = tsid.split('_')[1]

            # collect all time series
            ts = []
            for msnode in srnode.iterfind('.//ns5:MeasurementTVP',self.NS):
                event = {
                    'time':msnode.find(f'.//ns5:time',self.NS).text,
                    'value':msnode.find(f'.//ns5:value',self.NS).text,
                    'quality':msnode.find(f'.//ns5:metadata/ns5:TVPMeasurementMetadata/ns5:qualifier/ns7:Category/ns7:value',self.NS).text,
                    }
                ts.append(event)

            ts = DataFrame(ts)
            ts['timeseries'] = tsid
            tslist.append(ts)

        return pd.concat(tslist).sort_values(by='time').reset_index(drop=True)

    @property
    def obsprops(self):
        """Return observations metadata."""
        propslist = []
        for node in self._root.iterfind('.//ns6:OM_Observation',self.NS):
            obsprops = {}
            attdict = node.attrib
            tsid = [attdict[key] for key in attdict.keys()][0]
            tsid = tsid.split('_')[1]
            obsprops['obsId']=tsid
            
            taglist = [
                ('obsRole','.//ns9:CI_RoleCode'),
                ('dataStamp','.//ns8:Date'),
                ]
            for key,tag in taglist:
                obsprops[key] = node.find(tag,self.NS).text
            propslist.append(Series(obsprops))
        return DataFrame(propslist)
 
 
    @property
    def heads(self):
        """Return time series with groundwater levels."""
        levels = self.obs['value'].astype(float).values
        datetimes = pd.to_datetime(self.obs['time'],infer_datetime_format=True)
        name = self.gldprops['broIdGld']
        heads = Series(data=levels,index=datetimes,name=name)
        if heads.index.has_duplicates:
            warnings.warn(f'Duplicate datetimes found in head series {name}.')
        return heads

