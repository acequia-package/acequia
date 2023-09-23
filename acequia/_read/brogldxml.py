"""
Class BroGldXml reads XML with Groundwater Level Data from BRO XML 
file and also accepts result from a REST request.

"""
import os
import warnings
from pandas import Series,DataFrame
import pandas as pd
#import xml.etree.ElementTree as ET
from lxml.etree import _Element, _ElementTree
import lxml.etree as ET

class BroGldXml:
    """Read BRO Groundwater Level Data in XML tree format."""

    GLDPROPTAGS_XMLFILE = [
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

    GLDPROCESTAGS_XMLFILE = {
        'ObservationProcess':'ns5:ObservationProcess',
        'NamedValue':'ns6:NamedValue',
        'value':'ns6:value',
        }

    GLDOBSTAGS_XMLFILE = {
        'MeasurementTimeseries':'ns5:MeasurementTimeseries',
        'MeasurementTVP':'ns5:MeasurementTVP',
        'obstime':'ns5:time',
        'obsvalue':'ns5:value',
        'TVPMeasurementMetadata':'ns5:metadata/ns5:TVPMeasurementMetadata/ns5:qualifier/ns7:Category/ns7:value',
        }

    GLDOBSPROPSTAGS_XMLFILE = {
        'OM_Observation':'ns6:OM_Observation',
        'CI_RoleCode':'ns9:CI_RoleCode',
        'Date':'ns8:Date',
        }

    GLDPROPTAGS_RESTSERVICE = [
        ('dispatchTime','brocom:dispatchTime'),
        ('broIdGld','brocom:broId'),
        ('deliveryAccountableParty','brocom:deliveryAccountableParty'),
        ('qualityRegime','brocom:qualityRegime'),
        ('objectRegistrationTime','brocom:objectRegistrationTime'),
        ('registrationStatus','brocom:registrationStatus'),
        ('latestAdditionTime','brocom:latestAdditionTime'),
        ('corrected','brocom:corrected'),
        ('underReview','brocom:underReview'),
        ('deregistered','brocom:deregistered'),
        ('reregistered','brocom:reregistered'),
        ('researchFirstDate','ns11:researchFirstDate'),
        ('researchLastDate','ns11:researchLastDate'),
        ('broIdGmw','gldcommon:broId'),
        ('tubeNumber','gldcommon:tubeNumber'),
        ]

    GLDPROCESTAGS_RESTSERVICE = {
        'ObservationProcess':'waterml:ObservationProcess',
        'NamedValue':'om:NamedValue',
        'value':'om:value',
        }

    GLDOBSTAGS_RESTSERVICE = {
        'MeasurementTimeseries':'waterml:MeasurementTimeseries',
        'MeasurementTVP':'waterml:MeasurementTVP',
        'obstime':'waterml:time',
        'obsvalue':'waterml:value',
        'TVPMeasurementMetadata':'waterml:metadata/waterml:TVPMeasurementMetadata/waterml:qualifier/swe:Category/swe:value',
        }

    GLDOBSPROPSTAGS_RESTSERVICE = {
        'OM_Observation':'om:OM_Observation',
        'CI_RoleCode':'gmd:CI_RoleCode',
        'Date':'gco:Date',
        }


    def __init__(self,tree,xmlsource='file'):
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
        self._root = self._tree.getroot()
        self.NS = self._root.nsmap
        
        # define proper namespace tags for given source
        if xmlsource=='file':
            self.GLDPROPTAGS = self.GLDPROPTAGS_XMLFILE
            self.GLDPROCESTAGS = self.GLDPROCESTAGS_XMLFILE
            self.GLDOBSTAGS = self.GLDOBSTAGS_XMLFILE
            self.GLDOBSPROPSTAGS = self.GLDOBSPROPSTAGS_XMLFILE
        elif xmlsource=='rest':
            self.GLDPROPTAGS = self.GLDPROPTAGS_RESTSERVICE
            self.GLDPROCESTAGS = self.GLDPROCESTAGS_RESTSERVICE
            self.GLDOBSTAGS = self.GLDOBSTAGS_RESTSERVICE
            self.GLDOBSPROPSTAGS = self.GLDOBSPROPSTAGS_RESTSERVICE

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
        return cls(tree,xmlsource='file')

    @classmethod
    def from_rest(cls,xmltree):
        """Parse BRO GLD tree returned from REST service.
        
        Parameters
        ----------
        xmltree : lxml tree
            Valid BRO GLD XML tree from BRO REST service.

        Returns
        -------
        BroGldXml object"""

        if isinstance(xmltree,_Element):
            # the BRO REST service returns an object of type _Element
            # not a tree
            xmltree = tree.getroottree()

        if not isinstance(xmltree,_ElementTree):
            raise ValueError(('Input is not a valid XML Element tree.'))

        tree = xmltree
        return cls(tree,xmlsource='rest')


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
        for node in self._root.iterfind(f'.//{self.GLDPROCESTAGS["ObservationProcess"]}',self.NS):
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
        for srnode in self._root.iterfind(f'.//{self.GLDOBSTAGS["MeasurementTimeseries"]}',self.NS):

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
        for node in self._root.iterfind(F'.//{self.GLDOBSPROPSTAGS["OM_Observation"]}',self.NS):
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
