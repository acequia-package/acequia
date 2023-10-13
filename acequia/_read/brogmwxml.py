
import os
import warnings
from pandas import Series,DataFrame
import pandas as pd
import xml.etree.ElementTree as ET

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


    def __init__(self, root):
        """
        Parameters
        ----------
        tree : ElementTree tree object
            Valid XML tree with groundwater level measurement data.

        Example
        -------
        gld = BroGld(<elementtree>)
            
        """       
        #self._tree = tree
        self._root = root #self._tree.getroot()

    def __repr__(self):
        return self.wellprops['wellCode']

    @classmethod
    def from_xml(cls,xmlpath):
        """Read BRO GMW object from XML file.
        
        Parameters
        ----------
        xmlpath : str
            Valid filepath to XML file with well construction data.

        Returns
        -------
        BroGmwXml object

        Example
        -------
        gmw = BroGmwXml.from_xml(<valid xml filepath>)
        """

        if not os.path.isfile(xmlpath):
            raise ValueError(f'Invalid filepath: "{xmlpath}".')
        tree = ET.parse(xmlpath)
        #root = tree.getroot()
        return cls(tree)


    @property
    def wellprops(self):
        """Read well properties from XML tree"""
        wellprops = {}
        for key,tag in self.WELLPROPTAGS:
            node = self._root.find(f'.//{tag}',self.NS)
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
        
        return wellprops

    @property
    def tubeprops(self):
        """Read tube properties from XML tree"""
        tubeprops = []
        for node in self._root.iterfind(".//ns11:monitoringTube", self.NS):
            props = {}
            for tag in self.TUBEPROPTAGS:
                property = node.find(f'.//{tag}',self.NS).text
                key = tag.split(':')[1]     
                props[key] = property
            tubeprops.append(props)
        tubeprops = DataFrame(tubeprops)
        tubeprops = tubeprops.set_index('tubeNumber',drop=True)
        return tubeprops

    @property
    def events(self):
        """Read tube changes from XML tree"""
        events = []
        for node in self._root.iterfind('.//ns11:intermediateEvent',self.NS):
            event = {
                'intermediateEvent':node.find(f'.//ns11:eventName',self.NS).text,
                'eventDate':node.find(f'.//ns10:date',self.NS).text,
                }
            events.append(event)
        return DataFrame(events)

