
import os
import warnings
from pandas import Series,DataFrame
import pandas as pd
import xml.etree.ElementTree as ET

from .brorest import get_wellprops

class BroGmwXml:
    """Read well construction data from XML"""

    NS = {
        'gco' : "http://www.isotc211.org/2005/gco",
        'dsgmw' : "https://schema.broservices.nl/xsd/dsgmw/1.1",
        'ns12' : "http://www.broservices.nl/xsd/gmwcommon/1.1",
        'ns11' : "http://www.broservices.nl/xsd/dsgmw/1.1",
        'brocom' : "https://schema.broservices.nl/xsd/brocommon/3.0",
        'gts' : "http://www.isotc211.org/2005/gts",
        'gml' : "http://www.opengis.net/gml/3.2",
        'ns10' : "http://www.broservices.nl/xsd/brocommon/3.0",
        'gmwcom' : "https://schema.broservices.nl/xsd/gmwcommon/1.1",
        'isgmw' : "https://schema.broservices.nl/xsd/isgmw/1.1",
        'xlink' : "http://www.w3.org/1999/xlink",
        'gmd' : "http://www.isotc211.org/2005/gmd",
        }

    WELLPROPTAGS = [
        ('broId','ns10:broId'),   
        ('deliveryAccountableParty','ns10:deliveryAccountableParty'),
        ('qualityRegime','ns10:qualityRegime'),
        ('withPrehistory','ns11:withPrehistory'),
        ('deliveryContext','ns11:deliveryContext'),
        ('constructionStandard','ns11:constructionStandard'),
        ('initialFunction','ns11:initialFunction'),
        ('removed','ns11:removed'),
        ('numberOfMonitoringTubes','ns11:numberOfMonitoringTubes'),
        ('groundLevelStable','ns11:groundLevelStable'),
        ('wellStability','ns11:wellStability'),
        ('nitgCode','ns11:nitgCode'),
        ('wellCode','ns11:wellCode'),
        ('owner','ns11:owner'),
        ('wellHeadProtector','ns11:wellHeadProtector'),
        ('location','ns12:location/gml:pos'),
        ('horizontalPositioningMethod','ns12:horizontalPositioningMethod'),
        ('localVerticalReferencePoint','ns12:localVerticalReferencePoint'),
        ('VerticalOffset','ns12:offset'),
        ('verticalDatum','ns12:verticalDatum'),
        ('groundLevelPosition','ns12:groundLevelPosition'),
        ('groundLevelPositioningMethod','ns12:groundLevelPositioningMethod'),
        ('standardizedLocation','ns11:standardizedLocation/ns10:location/gml:pos'),
        ('coordinateTransformation','ns10:coordinateTransformation'),
        ('objectRegistrationTime','ns10:objectRegistrationTime'),
        ('registrationStatus','ns10:registrationStatus'),
        ('latestAdditionTime','ns10:latestAdditionTime'),
        ('wellConstructionDate','ns11:wellConstructionDate/ns10:date'),
        ]

    TUBEPROPTAGS = [
        'ns11:tubeNumber','ns11:tubeType','ns11:artesianWellCapPresent',
        'ns11:sedimentSumpPresent','ns11:numberOfGeoOhmCables','ns11:tubeTopDiameter',
        'ns11:variableDiameter','ns11:tubeStatus','ns11:tubeTopPosition',
        'ns11:tubeTopPositioningMethod','ns11:tubePartInserted','ns11:tubeInUse',
        'ns12:tubePackingMaterial','ns12:tubeMaterial','ns12:glue',
        'ns11:screenLength','ns11:sockMaterial','ns11:screenTopPosition',
        'ns12:plainTubePartLength','ns11:screenBottomPosition',
        ]

    WELLPROPCOLS_FLOAT = ['numberOfMonitoringTubes', 'VerticalOffset', 
        'groundLevelPosition','xcr', 'ycr',]

    WELLPROPCOLS_TIMESTAMP = ['objectRegistrationTime', 
        'latestAdditionTime', 'wellConstructionDate',]

    TUBEPROPCOLS_FLOAT = ['numberOfGeoOhmCables', 'tubeTopDiameter',
        'tubeTopPosition', 'screenLength', 'screenTopPosition', 
        'plainTubePartLength', 'screenBottomPosition', ]


    def __init__(self, tree):
        """
        Parameters
        ----------
        tree : ElementTree tree object
            Valid XML tree with groundwater level measurement data.

        Example
        -------
        gld = BroGld(<elementtree>)
            
        """
        self._tree = tree

    def __repr__(self):
        if self.is_valid:
            return self.wellprops['wellCode']
        return self.__class__.__name__

    @classmethod
    def from_xml(cls,xmlpath):
        """Read BRO GMW object from XML file.
        
        Parameters
        ----------
        xmlpath : str
            Valid filepath to XML file with well construction data.

        Returns
        -------
        BroGmwXml instance

        Example
        -------
        gmw = BroGmwXml.from_xml(<valid xml filepath>)
        """

        if not os.path.isfile(xmlpath):
            raise ValueError(f'Invalid filepath: "{xmlpath}".')
        cls.tree = ET.parse(xmlpath)

        # check xml source type
        if not cls.is_gmw:
            raise ValueError((f'{xmlpath} is not a valid BROGMW XML-file.'))

        return cls(cls.tree)

    @classmethod
    def from_server(cls, gmwid=None, description=None):
        """Download BRO GMW XML tree from BRO server.
    
        Parameters
        ----------
        gmwid : str
            Valid BRO well id.
        description : str, optional
            User defined description.

        Returns
        -------
        BroGmwXml instance

        Example
        -------
        gmw = BroGmw.from_server(gmwid='GMW000000041145')
            
        """
        tree = get_wellprops(gmwid=gmwid, description=description)        
        return cls(tree)

    @property
    def is_gmw(self):
        """Return True if XML tree contains GMW data."""
        
        tag = 'ns11:GMW_PO'
        el = self.tree.find(f'.//{tag}', self.NS)
        findtag = el.tag.split('}')[1]
        if not findtag=='GMW_PO':
            return False
        return True

    @property
    def is_deregistered(self):
        """Return True if GMW object was deregistered."""
        if self._tree.find('.//ns10:deregistered', self.NS).text=='ja':
            return True
        return False

    @property
    def is_valid(self):
        """True for valid GMW object, else False."""
        if self.is_deregistered:
            return False
        # ToDo: other possible checks for invalid data
        return True

    @property
    def gmwid(self):
        return self.wellprops['broId']

    @property
    def wellprops(self):
        """Read well properties from XML tree"""

        if not self.is_valid:
            return DataFrame()

        # extract wellprops from xml
        wellprops = {}
        for key,tag in self.WELLPROPTAGS:
            node = self._tree.find(f'.//{tag}',self.NS)
            if node is not None:
                wellprops[key]=node.text
            else:
                wellprops[key]=''
                #warnings.warn(f'{key} not found in XML {self._xmlpath}')

        # split coordinates
        wellprops = Series(wellprops)
        wellprops['xcr'] = wellprops['location'].split()[0]
        wellprops['ycr'] = wellprops['location'].split()[1]        
        wellprops['lon'] = wellprops['standardizedLocation'].split()[0]
        wellprops['lat'] = wellprops['standardizedLocation'].split()[1]
        wellprops = wellprops.drop(labels=['location','standardizedLocation',])

        # convert numerics and dates
        for col in self.WELLPROPCOLS_FLOAT:
            wellprops[col] = pd.to_numeric(wellprops[col])
        for col in self.WELLPROPCOLS_TIMESTAMP:
            wellprops[col] = pd.Timestamp(wellprops[col])

        return wellprops

    @property
    def tubeprops(self):
        """Read tube properties from XML tree"""

        if not self.is_valid:
            return DataFrame()

        # extract tubeprops from XML
        tubeprops = []
        for node in self._tree.iterfind(".//ns11:monitoringTube", self.NS):
            props = {}
            for tag in self.TUBEPROPTAGS:
                property = node.find(f'.//{tag}',self.NS).text
                key = tag.split(':')[1]     
                props[key] = property
            tubeprops.append(props)
        tubeprops = DataFrame(tubeprops)
        tubeprops = tubeprops.set_index('tubeNumber',drop=True)

        # convert numeric columns
        for col in self.TUBEPROPCOLS_FLOAT:
            tubeprops[col] = pd.to_numeric(tubeprops[col])

        return tubeprops

    @property
    def events(self):
        """Read tube changes from XML tree"""

        if not self.is_valid:
            return DataFrame()

        events = []
        for node in self._tree.iterfind('.//ns11:intermediateEvent',self.NS):

            event = {'intermediateEvent':None, 'eventDate':None}
            try:
                event['intermediateEvent'] = node.find(f'.//ns11:eventName',self.NS).text
                event['eventDate'] = node.find(f'.//ns10:date',self.NS).text

            except AttributeError as err:
                # in GMW000000042619 eventDate is nested in a childnode <brocom:date>
                # it is not clear if this is a strucutral problem, so we just pass
                # and give a warning
                warnings.warn((f"Error in {self.wellprops['wellCode']} while paring "
                    f"intermediateEvent."))

            finally:
                events.append(event)

        return DataFrame(events)

