"""
Class BroGldXml reads XML with Groundwater Level Data from BRO XML 
file and also accepts result from a REST request.

"""
import os
import warnings
import numpy as np
from pandas import Series,DataFrame
import pandas as pd
import xml.etree.ElementTree as ET
from . import brorest


class BroGldXml:
    """Read BRO Groundwater Level Data in XML tree format."""

    GLDPROPTAGS = [
        ('dispatchTime','ns1:dispatchTime'),
        ('broIdGld','ns1:broId'),
        ('deliveryAccountableParty','ns1:deliveryAccountableParty'),
        ('qualityRegime','ns1:qualityRegime'),
        ('objectRegistrationTime','ns1:objectRegistrationTime'),
        ('registrationStatus','ns1:registrationStatus'),
        ('latestAdditionTime','ns1:latestAdditionTime'),
        ('corrected','ns1:corrected'),
        ('underReview','ns1:underReview'),
        ('deregistered','ns1:deregistered'),
        ('reregistered','ns1:reregistered'),
        ('researchFirstDate','ns0:researchFirstDate'),
        ('researchLastDate','ns0:researchLastDate'),
        ('broIdGmn','ns3:GroundwaterMonitoringNet/ns3:broId'),
        #('broIdGmw','ns3:broId'),
        ('broIdGmw','ns3:GroundwaterMonitoringTube/ns3:broId'),
        #('tubeNumber','ns3:tubeNumber'),
        ('tubeNumber','ns3:GroundwaterMonitoringTube/ns3:tubeNumber'),
        ]

    GLDPROCESTAGS = {
        'ObservationProcess':'ns6:ObservationProcess',
        'NamedValue':'ns4:NamedValue',
        'value':'ns4:value',
        }

    GLDOBSTAGS = {
        'MeasurementTimeseries':'ns6:MeasurementTimeseries',
        'MeasurementTVP':'ns6:MeasurementTVP',
        'obstime':'ns6:time',
        'obsvalue':'ns6:value',
        'TVPMeasurementMetadata':'ns6:metadata/ns6:TVPMeasurementMetadata/ns6:qualifier/ns10:Category/ns10:value',
        }

    GLDOBSPROPSTAGS = {
        'OM_Observation':'ns4:OM_Observation',
        'CI_RoleCode':'ns7:CI_RoleCode',
        'Date':'ns8:Date',
        }

    NS = { 
        "ns0" : "http://www.broservices.nl/xsd/dsgld/1.0",
        "ns1" : "http://www.broservices.nl/xsd/brocommon/3.0",
        "ns10" : "http://www.opengis.net/swe/2.0",
        "ns2" : "http://www.opengis.net/gml/3.2",
        "ns3" : "http://www.broservices.nl/xsd/gldcommon/1.0",
        "ns4" : "http://www.opengis.net/om/2.0",
        "ns5" : "http://www.w3.org/1999/xlink",
        "ns6" : "http://www.opengis.net/waterml/2.0",
        "ns7" : "http://www.isotc211.org/2005/gmd",
        "ns8" : "http://www.isotc211.org/2005/gco",
        "xsi" : "http://www.w3.org/2001/XMLSchema-instance",
        }

    def __init__(self, tree): ##, xmlsource='file'):
        """
        Parameters
        ----------
        tree : ElementTree tree object
            Valid XML tree with groundwater level measurement data (GLD).
        xmlsource : {'file','rest'}, default 'file'
            Source of the XML tree (namespaces are different for 
            various sources).

        Example
        -------
        gld = BroGld(<elementtree>)"""

        self._tree = tree
        #self._root = self._tree.getroot()


    def __repr__(self):
        return self.gldprops['broIdGld']


    @classmethod
    def from_xml(cls,xmlpath):
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

        cls._tree = ET.parse(xmlpath)
        #root = tree.getroot()

        # check xml source type
        if not cls.is_gld:
            raise ValueError((f'{xmlpath} is not a valid BROGLD XML-file.'))

        return cls(cls._tree)


    @classmethod
    def from_server(cls, gldid=None, startdate=None, enddate=None, 
        reference=None):
        """Download BRO GLD XML tree from BRO server.

        Parameters
        ----------
        gldid : str
            Valid BroGldId.
        startdate : str, default '1900-01-01'
            Start date of groundwater level data.
        enddate : str, default today
            End date of ground water level data.
        reference : str, optional
            Optional user reference for data request.

        Returns
        -------
        BroGldXml
            
        Example
        -------
        gmw = BroGld.from_server(brogld='GLD000000010138')
            
        """
        ##cls._tree = brorest._request_gld(brogld='GLD000000012658')
        tree = brorest.get_levels(gldid=gldid, startdate=startdate, 
            enddate=enddate, reference=reference)

        return cls(tree)

    @property
    def gldid(self):
        return self.gldprops['broIdGld']

    @property
    def is_gld(self):
        """Return True if XML tree contains GMW data."""
        
        tag = 'ns0:GLD_O'
        el = self._tree.find(f'.//{tag}', self.NS)
        findtag = el.tag.split('}')[1]
        version = el.attrib['{http://www.opengis.net/gml/3.2}id']
        if not findtag=='GLD_O':
            return False
        return True

    @property
    def gldprops(self):
        """Get level data properties."""
        gldprops = {}
        for key,tag in self.GLDPROPTAGS:
            node = self._tree.find(f'.//{tag}',self.NS)
            if node is not None:
                gldprops[key]=node.text
            else:
                gldprops[key]=np.nan
        return Series(gldprops,name='GldProperties')


    @property
    def procesprops(self):
        """Collect observation process parameters."""
        propslist = []
        
        # collect paramaters for all time series
        for node in self._tree.iterfind(f'.//{self.GLDPROCESTAGS["ObservationProcess"]}',self.NS):
            props = {}
            
            # get time series id
            attdict = node.attrib
            tsid = [attdict[key] for key in attdict.keys()][0]
            tsid = tsid.split('_')[1]

            # get all parameters for time series
            for subnode in node.iterfind(f'.//{self.GLDPROCESTAGS["NamedValue"]}',self.NS):
                item = subnode.find(f'.//{self.GLDPROCESTAGS["value"]}',self.NS)
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
        for srnode in self._tree.iterfind(f'.//{self.GLDOBSTAGS["MeasurementTimeseries"]}',self.NS):

            # get time series id
            attdict = srnode.attrib
            tsid = [attdict[key] for key in attdict.keys()][0]
            tsid = tsid.split('_')[1]

            # collect all time series
            ts = []
            for msnode in srnode.iterfind(f'.//{self.GLDOBSTAGS["MeasurementTVP"]}',self.NS):
                event = {
                    'time':msnode.find(f'.//{self.GLDOBSTAGS["obstime"]}',self.NS).text,
                    'value':msnode.find(f'.//{self.GLDOBSTAGS["obsvalue"]}',self.NS).text,
                    'quality':msnode.find(f'.//{self.GLDOBSTAGS["TVPMeasurementMetadata"]}',self.NS).text,
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
        for node in self._tree.iterfind(F'.//{self.GLDOBSPROPSTAGS["OM_Observation"]}',self.NS):
            obsprops = {}
            attdict = node.attrib
            tsid = [attdict[key] for key in attdict.keys()][0]
            tsid = tsid.split('_')[1]
            obsprops['obsId']=tsid
            
            taglist = [
                ('obsRole',f'.//{self.GLDOBSPROPSTAGS["CI_RoleCode"]}'),
                ('dataStamp',f'.//{self.GLDOBSPROPSTAGS["Date"]}'),
                ]
            for key,tag in taglist:
                obsprops[key] = node.find(tag,self.NS).text
            propslist.append(Series(obsprops))

        obsprops = DataFrame(propslist).set_index('obsId').sort_values('dataStamp')
        return obsprops

    @property
    def heads(self):
        """Return time series with groundwater levels."""
        levels = self.obs['value'].astype(float).values
        datetimes = pd.DatetimeIndex(
            pd.to_datetime(self.obs['time'],
            infer_datetime_format=True, utc=True)).tz_localize(None)
        name = self.gldprops['broIdGld']
        heads = Series(data=levels,index=datetimes,name=name)
        if heads.index.has_duplicates:
            dupcount = len(heads[heads.index.duplicated(keep='first')])
            #warnings.warn(f'Removed {dupcount} duplicate datetimes from head series {name}.')
            heads = heads[~heads.index.duplicated(keep='first')].copy()
        return heads.sort_index()

    @property
    def timeseriescounts(self):
        return self.obs['timeseries'].value_counts()