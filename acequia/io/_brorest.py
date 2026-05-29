"""
Module with functions for retrieving data fro BRO REST service.
"""
import datetime as _dt
import requests as _requests
#import lxml.etree as ET
import xml.etree.ElementTree as _ET
#from pandas import Series, DataFrame
import pandas as _pd
import warnings as _warnings

from ..tools import convert_RDtoWGS84


def get_bro_gmwcodes_from_area(xmin=None, xmax=None, ymin=None, ymax=None,
    center=None, radius=None, startdate=None, enddate=None):
    """Return properties of wells within an area (rectangle or circle).
    
    Parameters
    ----------
    xmin : int
        Left boundary coordinate for rectangle (RD-coordinates)
    xmax : int
        Right boundary coordinate for rectangle (RD-coordinates)
    ymin : int
        Lower boundary coordinate for rectangle (RD-coordinates)
    ymax : int
        Upper boundary coordinate for rectangle (RD-coordinates)
    centre : tuple | list
        Area centre as (xcoor, ycoor) tuple.
    radius : float
        Area radius in kilometers.
    startdate : str, default None
        Minimum value of well registration date '2001-01-01'.
    enddate : str, default None
        Maximum value of well registration date. 

    Returns
    -------
    pd.DataFrame

    """
    bro = BroREST()
    df = bro.get_gmwcodes_from_area(xmin=xmin, xmax=xmax, ymin=ymin, 
        ymax=ymax, center=center, radius=radius, 
        startdate=startdate, enddate=None)

    return df


def get_bro_gmwprops(gmwid=None, description=None):
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
    wellprops = bro.get_gmwprops(gmwid=gmwid, description=description)
    return wellprops


def get_bro_gld_from_gmw(gmwid):
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
    ##welltubes = bro.get_welltubes(gmwid)
    welltubes = bro.get_gld_from_gmw(gmwid)
    return welltubes


def get_bro_gmw_username(gmwid):
    """Return BRO well user name wellcode for given gmwid.

    Parameters
    ----------
    gmwid : str
        Valid BRO groundwater monitoring well id.

    Returns
    -------
    str
    """
    bro = BroREST()
    #return bro.get_wellcode(gmwid)
    return bro.get_gmw_username(gmwid)


def get_bro_gmwcodes_from_bronhouder(bronhouder):
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
    gmwcodes = bro.get_gmwcodes_from_bronhouder(bronhouder)
    return gmwcodes


class BroREST:
    """Make requests to the BRO RESt service."""
    
    STARTDATE = '1900-01-01'
    TIMEOUT = 60*60 # seconds 501

    def __init__(self):
        self.response = None

    @property
    def status_code(self):
        """Server status response code."""
        if self.response:
            return self.response.status_code
        else:
            return None

    @property
    def status_reason(self):
        """Server status response reason."""
        if self.response:
            return self.response.reason
        else:
            return None

    def get_gmwprops(self, gmwid=None, description=None):
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
            _warnings.warn((f'No BRO well id was given. Values for well '
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
        self.response = _requests.get(f'https://publiek.broservices.nl/gm/gmw/v1/objects/{gmwid}',
            params=params, headers=headers, timeout=self.TIMEOUT)

        if not self.response.ok:
            return None

        self._root = _ET.fromstring(self.response.content)
        self._tree = _ET.ElementTree(self._root)

        return self._tree


    def get_gld_from_gmw(self, gmwid):
        """Return well tube number, well tube gldid and instantie for all
        tubes in a well.

        Parameters
        ----------
        gmwid : str
            Valid BRO groundwater monitoring well id.

        Returns
        -------
        DataFrame
            Table with well tube properties.
        """

        # make request
        url = f'https://publiek.broservices.nl/gm/v1/gmw-relations/{gmwid}'
        self.response = _requests.get(url)
        
        if not self.response.ok:
            return _pd.DataFrame()
        
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
            welltubes = _pd.DataFrame(tubes).set_index('tubenr').sort_index(ascending=True)
        else:
            welltubes = _pd.DataFrame()

        return welltubes


    def get_gmw_username(self, gmwid):
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
        self.response = _requests.get(url, timeout=self.TIMEOUT)
        if not self.response.ok:
            return None
        return self.response.text


    def get_gldxml(self, gldid=None, startdate=None, enddate=None, reference=None):
        """Return XML with groundwater level data (GLD) for GLD ID.

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
            enddate = _pd.Timestamp.today().strftime('%Y-%m-%d')
        if reference is None:
            reference = 'no user reference given'
        filtered = 'NEE'

        url = ((f'https://publiek.broservices.nl/gm/gld/v1/objects/{gldid}?'
            f'filtered={filtered}&observationPeriodBeginDate={startdate}&'
            f'observationPeriodEndDate={enddate}&requestReference={reference}'))
        self.response = _requests.get(url, timeout=self.TIMEOUT)

        if not self.response.ok:
            return None


        self._root = _ET.fromstring(self.response.content)
        self._tree = _ET.ElementTree(self._root)
        return self._tree


    def get_gmwcodes_from_bronhouder(self, bronhouder):
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
        self.response = _requests.get(url, timeout=self.TIMEOUT)
        return self.response.json()['broIds']


    def get_gldcodes_from_bronhouder(self, bronhouder):
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
        self.response = _requests.get(url, timeout=self.TIMEOUT)
        
        if not self.response.ok:
            return []

        return self.response.json()['broIds']


    def get_gmwcodes_from_area(self, xmin=None, xmax=None, ymin=None, 
        ymax=None, center=None, radius=None, 
        startdate=None, enddate=None, description=None):
        """Return properties of wells within an area (rectangle or circle).
        
        Parameters
        ----------
        Parameters
        ----------
        xmin : float
            Xcoor left boundary in Dutch RD coordinates.
        xmax : float
            Xcoor right boundary in Dutch RD coordinates.
        ymin : float
            Ycoor lower boundary in Dutch RD coordinates.
        ymax : float
            Ycoor upper boundary in Dutch RD coordinates.
        center : tuple
            Center(x, y) of circle in Dutch RD coordinates.
        radius : float
            Radius of circle in kilometers.
        startdate : str, default '2001-01-01'
            Minimum value of well registration date.
        enddate : str, default today
            Maximum value of well registration date. 
        description : str
            User description of dataset

        Returns
        -------
        pd.DataFrame

        Examples
        --------
        > wells = brorest.get_area_wellprops(center=(52.386449,6.919354),radius=0.5)

        """

        if startdate is None:
            startdate = self.STARTDATE
        if description is None:
            description = 'No user description was given.'

        # validate startdate
        try:
            date = _dt.datetime.strptime(startdate, '%Y-%m-%d')
        except ValueError as e:
            warnings.warn((f'Invalid startdate {startdate} was given. '
                f'Default startdate "{self.STARTDATE}" will be used.'))
            date = self.STARTDATE

        # validate enddate
        today = _dt.date.today().strftime("%Y-%m-%d")
        if enddate is None:
            enddate = today
        try:
            date = _dt.datetime.strptime(enddate, '%Y-%m-%d')
        except ValueError as e:
            warnings.warn((f'Invalid startdate {startdate} was given. '
                f'Wells registered until until today will be selected.'))
            enddate = today

        # circle with radius
        if (center is not None) and (radius is not None):
            lat, lon = convert_RDtoWGS84(center[0], center[1])
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
        #if (lowerleft is not None) and (upperright is not None):
        if (xmin is not None) and (xmax is not None) and (ymin is not None) and (ymax is not None):

            lc_lat, lc_lon = convert_RDtoWGS84(xmin, ymin)
            uc_lat, uc_lon = convert_RDtoWGS84(xmax, ymax)

            #lc_lat = lowerleft[0]
            #lc_lon = lowerleft[1]
            #uc_lat = upperright[0]
            #uc_lon = upperright[1]

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

        self.response = _requests.post('https://publiek.broservices.nl/gm/gmw/v1/characteristics/searches', 
            params=params, headers=headers, json=json_data, timeout=self.TIMEOUT)

        if not self.response.ok:
            return _pd.DataFrame()

        """
        import io
        f = io.StringIO(xmlstring)
        self._tree = _ET.parse(f)
        self._root = self._tree.getroot()
        """
            
        # get xmltree from response
        self._root = _ET.fromstring(self.response.content)

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
        self.wells = self._root.findall(f'.//{{{self.NS["NS0"]}}}{tag}', self.NS)

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
            rec = {}
            for key in self.WELLTAGS.keys():
                try:
                    rec[key] = well.find(self.WELLTAGS[key], self.NS).text
                except AttributeError:
                    rec[key] = _pd.NA
            data.append(rec.copy())
        data = _pd.DataFrame(data)
        return data

