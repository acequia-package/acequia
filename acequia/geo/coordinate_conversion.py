""" Conversion of geographic coordinates


"""
import numpy as np

class CrdCon:
    """Convert coordinates from Dutch RD Grid to WGS84 and back

    Methods
    -------
        RDtoWGS84(X,Y,Zone=False)
            convert x,y in RD to Lon,Lat in WGS84
        WGS84toRD(Lon,Lat)
            convert Lon,Lat in WGS84 to x,y in RD

    Examples
    --------
    >> crc = acequia.CrdCon()
    >> crc.RDtoWGS84(233883.131, 82065.167)
    >> {'Lon': 6.458551281201178,
        'Lat': 48.726255249201174,
        'East': 313102.7205129704,
        'North': 5400142.229150799,
        'xRD': 233883.131,
        'yRD': 82065.167,
        'UMTZONE': 'UMT32'}
    >> crc.WGS84toRD(4.88352,52.3745)
    >> {'xRD': 233883.06517103617,
        'yRD': 582067.0401935352,
        'Lon': 6.5682,
        'Lat': 53.2194}

    Note
    ----
    Coordinate onversions are valid only for the Netherlands!
    
    Formulas from article by Schreutelkamp en Strang Van Hees:
    "Benaderingsformules voor de transformatie tussen RD-en 
     WGS84-kaartcoordinaten"

    link: http://www.dekoepel.nl/pdf/Transformatieformules.pdf

    """

    Towers = {
             "Westertoren": {
                "town": "Amsterdam",
                "xRD": 120700.723,
                "yRD": 487525.501,
                "Lat_WGS84": 52.3745311,
                "Lon_WGS84": 4.8835223,
                "Lat_DDMMmm" : ['52','22.472'],
                "Lon_DDMMmm" : ['04','53.011'],
                "Lat_DDMMSS" : ['52','22','28.3'],
                "Lon_DDMMSS" : ['04','53','0.7'],
                "East_UMT31": 628217.312,
                "North_UMT31": 5804365.552,
                "East_UMT32": 219827.625, #calculated from RD
                "North_UMT32": 5810673.509, #calculated from RD
                },
            "Martinitoren": {
                "town": "Groningen",
                "xRD": 233883.131,
                "yRD": 582065.167,
                "Lat_WGS84": 53.2193814,
                "Lon_WGS84": 6.5682021,
                "Lat_DDMMmm" : ['53','13.163'],
                "Lon_DDMMmm" : ['06','34.092'],
                "Lat_DDMMSS" : ['53','13','9.8'],
                "Lon_DDMMSS" : ['06','34','5.5'],
                "East_UMT31": 738204.153, #calculated from RD
                "North_UMT31": 5902619.635, #calculated from RD
                "East_UMT32": 337643.235,
                "North_UMT32": 5899435.841,}
            }


    X0 = 155000.00
    Y0 = 463000.00
    Phi0 = 52.15517440
    Lambda0 = 5.38720621
    E0zone31 = 663304.11
    N0zone31 = 5780984.54
    E0zone32 = 252878.65
    N0zone32 = 5784453.44

    def RDtoWGS84(self,X,Y,Zone=False):
        """ Convert RD Xcoor,Ycoor to WGS84 latitude,longitude
        
        Parameters
        ----------
        X : float
            x-coordinate in RD-system
        Y : float
            y-coordinate in RD-system
        Zone : bool, optinal
            Apply different formulas for easting below 6 (UTM31) and
            eastignabove 6 (UTM32). Default is True.

        Returns
        -------
        dict

        Example
        -------
        >> crc = acequia.CrdCon()
        >> crc.RDtoWGS84(233883.131, 82065.167)
        >> {'Lon': 6.458551281201178,
            'Lat': 48.726255249201174,
            'East': 313102.7205129704,
            'North': 5400142.229150799,
            'xRD': 233883.131,
            'yRD': 82065.167,
            'UMTZONE': 'UMT32'}

        Note
        ----
        Within the WGS84 system, the 6th meridian divides the Netherslands 
        into two a western and an eastern zone. The aerea west of the 6th 
        meridian lies UTM zone 31, the eastern part belong to UTM zone 32. 
        To avoid jumps in transformed WGS84 coordinates, the default 
        'Zone=False' unsures that all transformations are calculated with 
        the paramaters for UTMzone 31.
        This follows the suggestion in the orginale article by Schreutelkamp 
        and Strang van Hees, from which all formules wer copied. 


        """
        Lon = self._RDtoWGS84Lon(X,Y)
        Lat = self._RDtoWGS84Lat(X,Y)
        if Lon>6 and Zone:
            [E,N]=self._RDtoWGS84forUMT32(X,Y)
            UMTZONE = "UMT32"
        else:
            [E,N]=self._RDtoWGS84forUMT31(X,Y)
            UMTZONE = "UMT31"
        return {"Lon" : Lon, "Lat" : Lat, "East" : E, "North" : N, 
                "xRD" : X, "yRD" : Y, "UMTZONE" : UMTZONE}


    def WGS84toRD(self,Lon,Lat):
        """ Convert WGS84 latitude,longitude to RD Xcoor,Ycoor
        
        Parameters
        ----------
        Lon : float
            Longitude in WGS84
        Lat : float
            Latitude in WGS84
        Zone : bool, optinal
            Apply different formulas for easting below 6 (UTM31) and
            easting above 6 (UTM32). Default is True.

        Returns
        -------
        dict

        Example
        -------
        >> crc = acequia.CrdCon()
        >> crc.WGS84toRD(4.88352,52.3745)
        >> {'xRD': 233883.06517103617,
            'yRD': 582067.0401935352,
            'Lon': 6.5682,
            'Lat': 53.2194}

        Note
        ----
        Allows for flexible input format of Lat,Lon:
            DD.ddd       : float or str with decimal degrees (default)
            [DD,MM,SS.S] : list (n=3) of float or str giving
                           degrees, minutes and seconds
            [DD,MM.mmmm] : list (n=2) of float or str giving
                           degrees and decimal minutes


        """

        try:

            if (type(Lon)==str) & (type(Lat)==str):

                Lon = float(Lon)
                Lat = float(Lat)


            elif (type(Lon)==list) & (type(Lat)==list):

                def tofloat(mystring):
                    """
                    if (len(mystring)!=0) & mystring[0]=='0':
                        result = float(mystring[1])
                    else: 
                        result = float(mystring)
                    """
                    try:
                        result = float(mystring)
                    except:
                        print('Could not convert to float: {mystring}')
                        raise
                    return result

                if (len(Lon)==3) & (len(Lat)==3):

                    def DDMMSSs(mylist):
                        """ conversie graden minuten seconden (notatie [DD,MM,SS.S])
                        naar decimale graden (notatie DD.ddd) 
                        Martinitoren: N [52,22,28.3], E [4,53,0.7] wordt N 52.37453, E 4.88352 """
                        dd = tofloat(mylist[0])
                        mm = tofloat(mylist[1])
                        ss = tofloat(mylist[2])
                        return dd+(mm*60+ss)/3600

                    Lon = DDMMSSs(Lon)
                    Lat = DDMMSSs(Lat)

                elif (len(Lon)==2) & (len(Lat)==2):

                    def DDMMMmmm(mylist):
                        """ conversie graden minuten (notatie [DD,MM.mmm])
                        naar decimale graden (notatie DD.ddd) 
                        Martinitoren: N [52,22.472], E [4,53.011] wordt N 52.37453, E 4.88352 """
                        dd = tofloat(mylist[0])
                        mm = tofloat(mylist[1])
                        return dd+(mm*60)/3600

                    Lon = DDMMMmmm(Lon)
                    Lat = DDMMMmmm(Lat)

            xcoor = self._WGS84toRDx(Lon,Lat)
            ycoor = self._WGS84toRDy(Lon,Lat)

        except Exception as err:
            xcoor = None
            ycoor = None
            print("Fout opgetreden: ",err.args)
            raise Warning("Error in WGS842RD")

        finally:
            result = {
                "xRD" : xcoor,
                "yRD" : ycoor,
                "Lon"  : Lon,
                "Lat"  : Lat}
        return result


    def _RDtoWGS84Lon(self,X,Y):
        """Calculate WGS84 Longitude from RD X,Y """

        coef = [
               [1,0,5260.52916],
               [1,1,105.94684],
               [1,2,2.45656],
               [3,0,-0.81885],
               [1,3,0.05594],
               [3,1,-0.05607],
               [0,1,0.01199],
               [3,2,-0.00256],
               [1,4,0.00128],
               [0,2,0.00022],
               [2,0,-0.00022],
               [5,0,0.00026]
               ]
        dX=(X-self.X0)*pow(10,-5)
        dY=(Y-self.Y0)*pow(10,-5)
        Lambda = 0
        for i in range(len(coef)):
            p = coef[i][0]
            q = coef[i][1]
            L = coef[i][2]
            Lambda+=L*pow(dX,p)*pow(dY,q)
        return self.Lambda0+Lambda/3600.0


    def _RDtoWGS84Lat(self,X,Y):
        """Calculate WGS84 Latitude from RD X,Y """

        coef = [
               [0,1,3235.65389],
               [2,0,-32.58297],
               [0,2,-0.24750],
               [2,1,-0.84978],
               [0,3,-0.06550],
               [2,2,-0.01709],
               [1,0,-0.00738],
               [4,0,0.00530],
               [2,3,-0.00039],
               [4,1,0.00033],
               [1,1,-0.00012]
               ]
        dX=(X-self.X0)*pow(10,-5)
        dY=(Y-self.Y0)*pow(10,-5)
        phi = 0
        for i in range(len(coef)):
            p = coef[i][0]
            q = coef[i][1]
            K = coef[i][2]
            phi+=K*pow(dX,p)*pow(dY,q)
        return self.Phi0+phi/3600.0

    def _RDtoWGS84forUMT31(self,X,Y):
        """Convert RD-system X,Y to WGS84 Easting,Northing 
        using paramters for Zone UMT31 """

        A0 = self.E0zone31
        B0 = self.N0zone31
        A1 = 99947.539
        B1 = 3290.106
        A2 = 20.008
        B2 = 1.310
        A3 = 2.041
        B3 = 0.203
        A4 = 0.001
        B4 = 0.000

        dX = (X-self.X0)*pow(10,-5)
        dY = (Y-self.Y0)*pow(10,-5)

        E = A0 + A1*dX - B1*dY + A2*(pow(dX,2)-pow(dY,2)) - B2*(2*dX*dY)
        E+= A3*(pow(dX,3)-3*dX*pow(dY,2))-B3*(3*pow(dX,2)*dY-pow(dY,3))
        E+= A4*(pow(dX,4)-6*pow(dX,2)*pow(dY,2)+pow(dY,4))-B4*(4*pow(dX,3)*dY-4*pow(dY,3)*dX)

        N = B0 + B1*dX + A1*dY + B2*(pow(dX,2)-pow(dY,2)) + A2*(2*dX*dY)
        N+= B3*(pow(dX,3)-3*dX*pow(dY,2))+A3*(3*pow(dX,2)*dY-pow(dY,3))
        E+= B4*(pow(dX,4)-6*pow(dX,2)*pow(dY,2)+pow(dY,4))+A4*(4*pow(dX,3)*dY-4*pow(dY,3)*dX)
        return [E,N]

    def _RDtoWGS84forUMT32(self,X,Y):
        """Convert RD-system X,Y to WGS84 Easting,Northing 
        using paramters for Zone UMT32 """

        A0 = self.E0zone32
        B0 = self.N0zone32
        A1 = 99919.783
        B1 = -4982.166
        A2 = -30.208
        B2 = 3.016
        A3 = 2.035
        B3 = -0.309
        A4 = -0.002
        B4 = 0.001

        dX = (X-self.X0)*pow(10,-5)
        dY = (Y-self.Y0)*pow(10,-5)

        E = A0 + A1*dX - B1*dY + A2*(pow(dX,2)-pow(dY,2)) - B2*(2*dX*dY)
        E+= A3*(pow(dX,3)-3*dX*pow(dY,2))-B3*(3*pow(dX,2)*dY-pow(dY,3))
        E+= A4*(pow(dX,4)-6*pow(dX,2)*pow(dY,2)+pow(dY,4))-B4*(4*pow(dX,3)*dY-4*pow(dY,3)*dX)

        N = B0 + B1*dX + A1*dY + B2*(pow(dX,2)-pow(dY,2)) + A2*(2*dX*dY)
        N+= B3*(pow(dX,3)-3*dX*pow(dY,2))+A3*(3*pow(dX,2)*dY-pow(dY,3))
        E+= B4*(pow(dX,4)-6*pow(dX,2)*pow(dY,2)+pow(dY,4))+A4*(4*pow(dX,3)*dY-4*pow(dY,3)*dX)
        return [E,N]


    def _WGS84toRDx(self,Lon,Lat):
        """Convert WGS longitude,latitude to RD-system Xcrd """

        Lambda = Lon
        Phi = Lat

        coef = [#p,q,Rpg
               [0,1,190094.945],
               [1,1,-11832.228],
               [2,1,-114.221],
               [0,3,-32.391],
               [1,0,-0.705],
               [3,1,-2.340],
               [1,3,-0.608],
               [0,2,-0.008],
               [2,3,0.148]
               ]
        dPhi=0.36*(Phi-self.Phi0)
        dLambda=0.36*(Lambda-self.Lambda0)
        X = 0
        for i in range(len(coef)):
           p = coef[i][0]
           q = coef[i][1]
           R = coef[i][2]
           X+=R*pow(dPhi,p)*pow(dLambda,q)
        return self.X0+X


    def _WGS84toRDy(self,Lon,Lat):
        """Convert WGS longitude,latitude to RD-system Ycrd """

        Lambda = Lon
        Phi = Lat
        coef = [
               [1,0,309056.544],
               [0,2,3638.893],
               [2,0,73.077],
               [1,2,-157.984],
               [3,0,59.788],
               [0,1,0.433],
               [2,2,-6.439],
               [1,1,-0.032],
               [0,4,0.092],
               [1,4,-0.054]
               ]
        dPhi=0.36*(Phi-self.Phi0)
        dLambda=0.36*(Lambda-self.Lambda0)
        Y = 0
        for i in range(len(coef)):
            p = coef[i][0]
            q = coef[i][1]
            S = coef[i][2]
            Y+=S*pow(dPhi,p)*pow(dLambda,q)
        return self.Y0+Y


    def _WGS84toRDforUMT31(self,E,N):
        """ Convert WGS84 Easting, Northing tot RD-system X,Y-self
        using paramters for Zone UMT31 """

        C0 = self.X0
        D0 = self.Y0
        C1 = 99944.187
        D1 = -3289.996
        C2 = -20.039
        D2 = 0.668
        C3 = -2.042
        D3 = 0.066
        C4 = 0.001
        D4 = 0.000

        dE = (E-self.E0zone31)*pow(10,-5)
        dN = (N-self.N0zone31)*pow(10,-5)

        X = C0 + C1*dE - D1*dN + C2*(pow(dE,2)-pow(dN,2))-D2*(2*dE*dN)
        X+= C3*(pow(dE,3)-3*dE*pow(dN,2))-D3*(3*pow(dE,2)*dN-pow(dN,3))
        X+= C4*(pow(dE,4)-6*pow(dE,2)*pow(dN,2)+pow(dN,4))-D4*(4*pow(dE,3)*dN-4*pow(dN,3)*dE)

        Y = D0 + D1*dE + C1*dN + D2*(pow(dE,2)-pow(dN,2))+C2*(2*dE*dN)
        Y+= D3*(pow(dE,3)-3*dE*pow(dN,2))+C3*(3*pow(dE,2)*dN-pow(dN,3))
        Y+= D4*(pow(dE,4)-6*pow(dE,2)*pow(dN,2)+pow(dN,4))+C4*(4*pow(dE,3)*dN-4*pow(dN,3)*dE)

        return [X,Y]


    def _WGS84toRDforUMT32(self,E,N):
        """ Convert WGS84 Easting, Northing tot RD-system X,Y-self
        using paramters for Zone UMT32 """

        C0 = 155000.00
        D0 = 463000.00
        C1 = 99832.079
        D1 = 4977.793
        C2 = 30.280
        D2 = 1.514
        C3 = -2.034
        D3 = -0.099
        C4 = -0.001
        D4 = 0.000

        dE = (E-self.E0zone32)*pow(10,-5)
        dN = (N-self.N0zone32)*pow(10,-5)

        X = C0 + C1*dE - D1*dN + C2*(pow(dE,2)-pow(dN,2))-D2*(2*dE*dN)
        X+= C3*(pow(dE,3)-3*dE*pow(dN,2))-D3*(3*pow(dE,2)*dN-pow(dN,3))
        X+= C4*(pow(dE,4)-6*pow(dE,2)*pow(dN,2)+pow(dN,4))-D4*(4*pow(dE,3)*dN-4*pow(dN,3)*dE)

        Y = D0 + D1*dE + C1*dN + D2*(pow(dE,2)-pow(dN,2))+C2*(2*dE*dN)
        Y+= D3*(pow(dE,3)-3*dE*pow(dN,2))+C3*(3*pow(dE,2)*dN-pow(dN,3))
        Y+= D4*(pow(dE,4)-6*pow(dE,2)*pow(dN,2)+pow(dN,4))+C4*(4*pow(dE,3)*dN-4*pow(dN,3)*dE)

        return [X,Y]
