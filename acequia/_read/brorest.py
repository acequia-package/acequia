"""
Module with functions for retrieving data fro BRO REST service.
"""
import datetime as dt
import requests
#import lxml.etree as ET
import xml.etree.ElementTree as ET
from pandas import Series, DataFrame
import pandas as pd

#def _parse_dispatchDocument(tree):
#    pass
""""Helper function for parsing BRO XML tree.

Parameters
----------
tree : lxml tree
    XML tree with well properties.

Returns
-------
pd.DataFrame
"""

#nsmap = tree.nsmap
#root = tree.getroottree()

# dataFrame node properties
"""
tag = 'dispatchDocument'
nodes = root.findall(f'.//{tag}',nsmap)
reclist = []
for node in nodes:
    eldict = {}
    for el in node.iterdescendants(): # iter all descendants
        tag = ET.QName(el).localname
        eldict[tag]=el.text
    reclist.append(eldict)

return DataFrame(reclist)
"""

def get_area_wellprops(center=None, radius=None, lowerleft=None, 
    upperright=None, startdate=None, enddate=None):
    """Return properties of wells within an area (rectangle or circle).
    
    Parameters
    ----------
    centre : tuple | list
        Area centre as (latitude,longitude) tuple.
    radius : float
        Area radius in kilometers.
    lowerleft : tuple | list
        Lowerleft corner of rectangle as (latitude,longitude).
    uperright : tuple | list
        Upperright corner of rectangle as (latitude,longitude).
    startdate : str, default '2001-01-01'
        Minimum value of well registration date.
    enddate : str, default today
        Maximum value of well registration date. 

    Returns
    -------
    pd.DataFrame

    Examples
    --------
    > wells = brorest.get_area_wellprops(center=(52.386449,6.919354),radius=0.5)

    """
    bro = BroREST()
    df = bro.get_area_wellprops(center=center, radius=radius, 
        lowerleft=lowerleft, upperright=upperright, startdate=startdate, 
        enddate=enddate)
    return df


def get_wellprops(gmwid=None, description=None):
    """Return well properties.
    
    Parameters
    ----------
    gmwid : str
        Valid BRO well id.
    description : str, optional
        User defined description.

    Returns
    -------
    ElementTree tree
        
    """
    bro = BroREST()
    root = bro.get_wellprops(gmwid=gmwid, description=description)
    return root


def get_welltubes(gmwid):
    """Return well tube number, well tube gldid and instantie for all
    tubes in a well.

    Parameters
    ----------
    gmwid : str
        Valid BRO groundwater monitoring well id.

    Returns
    -------
    pd.DataFrame
        Table with well tube properties.
    """
    bro = BroREST()
    welltubes = bro.get_welltubes(gmwid)
    return welltubes


def get_wellcode(gmwid):
    """Return BRO well user name putcode.

    Parameters
    ----------
    gmwid : str
        Valid BRO groundwater monitoring well id.

    Returns
    -------
    str
    """
    bro = BroREST()
    return bro.get_wellcode(gmwid)


def get_levels(gldid=None, startdate=None, enddate=None, reference=None):
    """Return Groundwater Level Data (GLD) for GLD.

    Parameters
    ----------
    brogld : str
        Valid BroGldId.
    startdate : str, default '1900-01-01'
        Start date of groundwater level data.
    enddate : str, default today
        End date of ground water level data.
    reference : str, optional
        Optional user reference for data request.

    Returns
    -------
    ElementTree tree
    """
    bro = BroREST()
    tree = bro.get_levels(gldid=gldid, startdate=startdate, enddate=enddate, reference=reference)
    return tree


def get_gld_codes(bronhouder):
    """Return list of groundwater level data (GLD) codes for given bronhouder.

    Parameters
    ----------
    bronhouder : str, int
        Valid BRO bronhouder ID number (KvK number).

    Returns
    -------
    list
    """
    bro = BroREST()
    gldcodes = bro.get_gld_codes(bronhouder)
    return gldcodes


def get_gmw_codes(bronhouder):
    """Return list of groundwater monitoring well (GMW) codes for given bronhouder.

    Parameters
    ----------
    bronhouder : str, int
        Valid BRO bronhouder ID number (KvK number).

    Returns
    -------
    list
    """
    bro = BroREST()
    return bro.get_gmw_codes(bronhouder)


class BroREST:
    """Make requests to the BRO RESt service."""
    
    STARTDATE = '1900-01-01'

    def __init__(self):
        pass

    def get_area_wellprops(self, center=None, radius=None, 
        lowerleft=None, upperright=None, startdate=None, 
        enddate=None, description=None):


        if startdate is None:
            startdate = self.STARTDATE
        if description is None:
            description = 'No user description was given.'

        # validate startdate
        try:
            date = dt.datetime.strptime(startdate, '%Y-%m-%d')
        except ValueError as e:
            warnings.warn((f'Invalid startdate {startdate} was given. '
                f'Default startdate "{self.STARTDATE}" will be used.'))
            date = self.STARTDATE

        # validate enddate
        today = dt.date.today().strftime("%Y-%m-%d")
        if enddate is None:
            enddate = today
        try:
            date = dt.datetime.strptime(enddate, '%Y-%m-%d')
        except ValueError as e:
            warnings.warn((f'Invalid startdate {startdate} was given. '
                f'Wells registered until until today will be selected.'))
            enddate = today

        # circle with radius
        if (center is not None) and (radius is not None):
            lat = center[0]
            lon = center[1]
            json_data = {
                'registrationPeriod': {
                    'beginDate': startdate,
                    'endDate': enddate,
                    },
                'area': {
                    'enclosingCircle': {
                        'center': {
                            'lat': lat, #52.349968,
                            'lon': lon, #7.064451,
                            },
                        'radius': radius, #0.5,
                        },
                    },
                }

        # rectangle
        if (lowerleft is not None) and (upperright is not None):

            lc_lat = lowerleft[0]
            lc_lon = lowerleft[1]
            uc_lat = upperright[0]
            uc_lon = upperright[1]

            json_data = {
                'registrationPeriod': {
                    'beginDate': startdate, #'2017-01-01',
                    'endDate': enddate, #'2021-01-01',
                    },
                'area': {
                    'boundingBox': {
                        'lowerCorner': {
                            'lat': lc_lat, #52.340333,
                            'lon': lc_lon, #6.865430,
                            },
                        'upperCorner': {
                            'lat': uc_lat, #52.347915,
                            'lon': uc_lon, #6.888625,
                            },
                        },
                    },
                }


        # make request
        headers = {'accept': 'application/xml',}
        params = {'requestReference': description,}

        self.response = requests.post('https://publiek.broservices.nl/gm/gmw/v1/characteristics/searches', 
            params=params, headers=headers, json=json_data)

        """
        import io
        f = io.StringIO(xmlstring)
        tree = ET.parse(f)
        root = tree.getroot()
        """
            
        # get xmltree from response
        self.root = ET.fromstring(self.response.content)

        # parse XML tree
        # --------------

        NS0 = 'http://www.broservices.nl/xsd/dsgmw/1.1'
        NS1 = 'http://www.broservices.nl/xsd/brocommon/3.0'
        NS2 = 'http://www.opengis.net/gml/3.2'

        self.NS = {
            'NS0' : NS0,
            'NS1' : NS1,
            'NS2' : NS2,
            }

        # data for each well is stored below the tag "GMW_C"
        # find all wells
        tag = 'GMW_C'
        self.wells = self.root.findall(f'.//{{{self.NS["NS0"]}}}{tag}', self.NS)

        self.WELLTAGS = {
            'gmwid' : f'.//{{{self.NS["NS1"]}}}broId',
            'accountable' : f'.//{{{self.NS["NS1"]}}}deliveryAccountableParty',
            'quality' : f'.//{{{self.NS["NS1"]}}}qualityRegime',
            'registrationtime' : f'.//{{{self.NS["NS1"]}}}objectRegistrationTime',
            'correctiontime' : f'.//{{{self.NS["NS1"]}}}latestCorrectionTime',
            'latlon' : f'.//{{{self.NS["NS1"]}}}standardizedLocation//{{{self.NS["NS2"]}}}pos',
            'xy' : f'.//{{{self.NS["NS1"]}}}deliveredLocation//{{{self.NS["NS2"]}}}pos',
            'reflev' : f'.//{{{self.NS["NS0"]}}}verticalDatum',
            'surfacelevel' : f'.//{{{self.NS["NS0"]}}}groundLevelPosition',
            'owner' : f'.//{{{self.NS["NS0"]}}}owner',
            'constructiondate' : f'.//{{{self.NS["NS0"]}}}wellConstructionDate',
            'removed' : f'.//{{{self.NS["NS0"]}}}removed',
            'tubes' : f'.//{{{self.NS["NS0"]}}}numberOfMonitoringTubes',
            'protection' : f'.//{{{self.NS["NS0"]}}}wellHeadProtector',
            'nitgcode' : f'.//{{{self.NS["NS0"]}}}nitgCode',
            'wellcode' : f'.//{{{self.NS["NS0"]}}}wellCode',
            'wellcode' : f'.//{{{self.NS["NS0"]}}}wellCode',
            'diamin' : f'.//{{{self.NS["NS0"]}}}diameterRange//{{{self.NS["NS0"]}}}smallestTubeTopDiameter',
            'diamax' : f'.//{{{self.NS["NS0"]}}}diameterRange//{{{self.NS["NS0"]}}}largestTubeTopDiameter',
            'filshallow' : f'.//{{{self.NS["NS0"]}}}screenPositionRange//{{{self.NS["NS0"]}}}shallowestScreenTopPosition',
            'fildeep' : f'.//{{{self.NS["NS0"]}}}screenPositionRange//{{{self.NS["NS0"]}}}deepestScreenBottomPosition',
            }

        data = []
        for well in self.wells:
            ##print(well)
            rec = {}
            for key in self.WELLTAGS.keys():
                try:
                    rec[key] = well.find(self.WELLTAGS[key], self.NS).text
                except AttributeError:
                    rec[key] = pd.NA
            data.append(rec.copy())
        data = DataFrame(data)
        return data


    def get_wellprops(self, gmwid=None, description=None):
        """Return well properties.
        
        Parameters
        ----------
        gmwid : str
            Valid BRO well id.
        description : str, optional
            User defined description.

        Returns
        -------
        ElementTree tree
            
        """
        if gmwid is None:
            gmwid = 'GMW000000041033' # for testing
            warnings.warn((f'No BRO well id was given. Values for well '
                f'{gmwid} will be returned.'))

        if description is None:
            description = 'no user description was given'

        headers = {
            'accept': 'application/xml',
            }
        params = {
            'fullHistory': 'ja',
            'requestReference': description,
            }
        response = requests.get(f'https://publiek.broservices.nl/gm/gmw/v1/objects/{gmwid}',
            params=params, headers=headers)

        root = ET.fromstring(response.content)
        tree = ET.ElementTree(root)

        ##wellprops = BroGmwXml(tree)
        ##return wellprops ##wellprops.set_index('broId').squeeze()
        return tree

    def get_welltubes(self, gmwid):
        """Return well tube number, well tube gldid and instantie for all
        tubes in a well.

        Parameters
        ----------
        gmwid : str
            Valid BRO groundwater monitoring well id.

        Returns
        -------
        pd.DataFrame
            Table with well tube properties.
        """

        # make request
        url = f'https://publiek.broservices.nl/gm/v1/gmw-relations/{gmwid}'
        self.response = requests.get(url)
        resdict = self.response.json()

        # iterate over nested json dictionary:
        tubes = []
        for tube in resdict['monitoringTubeReferences']:
            for gld in tube['gldReferences']:
                tubes.append({
                    'gmwid' : resdict['gmwBroId'],
                    'tubenr' : str(tube['tubeNumber']),
                    'gldid' : gld['broId'],
                    'instantie' : gld['accountableParty'],
                    },)

        if tubes:
            welltubes = DataFrame(tubes).set_index('tubenr').sort_index(ascending=True)
        else:
            welltubes = DataFrame()

        return welltubes


    def get_wellcode(self, gmwid):
        """Return BRO well user name putcode.

        Parameters
        ----------
        gmwid : str
            Valid BRO groundwater monitoring well id.

        Returns
        -------
        str
        """
        url = ((f'https://publiek.broservices.nl/gm/gmw/v1/well-code/{gmwid}'
            f'?requestReference=myref'))
        response = requests.get(url)
        return response.text


    def get_levels(self, gldid=None, startdate=None, enddate=None, reference=None):
        """Return Groundwater Level Data (GLD) for GLD.

        Parameters
        ----------
        brogld : str
            Valid BroGldId.
        startdate : str, default '1900-01-01'
            Start date of groundwater level data.
        enddate : str, default today
            End date of ground water level data.
        reference : str, optional
            Optional user reference for data request.

        Returns
        -------
        ElementTree tree
                
        """
        if startdate is None:
            startdate = '1900-01-01'
        if enddate is None:
            enddate = pd.Timestamp.today().strftime('%Y-%m-%d')
        if reference is None:
            reference = 'no user reference given'
        filtered = 'NEE'

        url = ((f'https://publiek.broservices.nl/gm/gld/v1/objects/{gldid}?'
            f'filtered={filtered}&observationPeriodBeginDate={startdate}&'
            f'observationPeriodEndDate={enddate}&requestReference={reference}'))
        response = requests.get(url)
        status_code = response.status_code
        response_string = response.content

        root = ET.fromstring(response.content)
        tree = ET.ElementTree(root)
        #tree = _request_gld(brogld=brogld,startdate=startdate,enddate=enddate,reference=reference)
        return tree


    def get_gld_codes(self, bronhouder):
        """Return list of groundwater level data (GLD) codes for given bronhouder.

        Parameters
        ----------
        bronhouder : str, int
            Valid BRO bronhouder ID number (KvK number).

        Returns
        -------
        list
        """
        bronhouder = str(bronhouder)
        url = f'https://publiek.broservices.nl/gm/gld/v1/bro-ids?bronhouder={bronhouder}'
        self.response = requests.get(url)
        self.response_status_code = self.response.status_code
        return self.response.json()['broIds']


    def get_gmw_codes(self, bronhouder):
        """Return list of groundwater monitoring well (GMW) codes for given bronhouder.

        Parameters
        ----------
        bronhouder : str, int
            Valid BRO bronhouder ID number (KvK number).

        Returns
        -------
        list
        """
        bronhouder = str(bronhouder)
        url = f'https://publiek.broservices.nl/gm/gmw/v1/bro-ids?bronhouder={bronhouder}'
        self.response = requests.get(url)
        #self.response_status_code = self.response.status_code
        return self.response.json()['broIds']