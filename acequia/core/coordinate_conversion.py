""" Conversion of geographic coordinates

Convert coordinates from Dutch RD Grid to WGS84 and back
Following conversions can be made:


Examples:
    >>> 

Note:
    Formulas from article:
    "Benaderingsformules voor de transformatie tussen RD-en 
     WGS84-kaartcoordinaten"
    by Schreutelkamp en Strang Van Hees.
    link: http://www.dekoepel.nl/pdf/Transformatieformules.pdf

"""

class CrdCon:

    X0 = 155000.00
    Y0 = 463000.00
    Phi0 = 52.15517440
    Lambda0 = 5.38720621
    E0zone31 = 663304.11
    N0zone31 = 5780984.54
    E0zone32 = 252878.65
    N0zone32 = 5784453.44

    def RDtoWGS84(self,X,Y,Zone=True):
        """Conversie van X en Y in RD-stelsel naar NB,OL en Easting,Northing in WGS84"""
        OL = self._RDtoWGS84OL(X,Y)
        NB = self._RDtoWGS84NB(X,Y)
        if OL>6:
            UMTZONE = "UMT32"
        else:
            UMTZONE = "UMT31"
        if OL>6 and Zone:
            [E,N]=self._RDtoWGS84forUMT32(X,Y)
        else:
            [E,N]=self._RDtoWGS84forUMT31(X,Y)

        return {"OL" : OL, "NB" : NB, "E" : E, "N" : N, "xRD" : X, "yRD" : Y, "UMTZONE" : UMTZONE}

    def OLNBtoRD(self,OL,NB):
        """ Conversie van NB en OL (WGS84) in decimale graden  naar RD-stelsel
        Voor flexibele invoer mogen OL en NB zijn:
        DD.ddd       : float of string  met decimale graden (default)
        [DD,MM,SS.S] : list van strings of floats (n=3) met graden minuten en seconden
        [DD,MM.mmmm] : list van strings of floats (n=2) met graden en decimale minuten """
        try:
            if (type(OL)==str) & (type(NB)==str):

                OL = float(OL)
                NB = float(NB)

            elif (type(OL)==list) & (type(NB)==list):

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

                if (len(OL)==3) & (len(NB)==3):

                    def DDMMSSs(mylist):
                        """ conversie graden minuten seconden (notatie [DD,MM,SS.S])
                        naar decimale graden (notatie DD.ddd) 
                        Martinitoren: N [52,22,28.3], E [4,53,0.7] wordt N 52.37453, E 4.88352 """
                        dd = tofloat(mylist[0])
                        mm = tofloat(mylist[1])
                        ss = tofloat(mylist[2])
                        return dd+(mm*60+ss)/3600

                    OL = DDMMSSs(OL)
                    NB = DDMMSSs(NB)

                elif (len(OL)==2) & (len(NB)==2):

                    def DDMMMmmm(mylist):
                        """ conversie graden minuten (notatie [DD,MM.mmm])
                        naar decimale graden (notatie DD.ddd) 
                        Martinitoren: N [52,22.472], E [4,53.011] wordt N 52.37453, E 4.88352 """
                        dd = tofloat(mylist[0])
                        mm = tofloat(mylist[1])
                        return dd+(mm*60)/3600

                    OL = DDMMMmmm(OL)
                    NB = DDMMMmmm(NB)

            xcoor = self._WGS84toRDx(OL,NB)
            ycoor = self._WGS84toRDy(OL,NB)

        except Exception as err:
            xcoor = None
            ycoor = None
            print("Fout opgetreden: ",err.args)
            raise Warning("Error in OLNB2RD")

        finally:
            result = {
                "xRD" : xcoor,
                "yRD" : ycoor,
                "OL"  : OL,
                "NB"  : NB}
        return result

    def UMTtoRD2(self,E,N):
         """Conversie van Easting en Northing in WGS84 naar RD-stelsel
            Op advies van Schreutelkamp en Strang van Hees wordt de conversie
            altijd gebaseerd op Zone 31, ook voor punten ten oosten van OL = 6,
            die feitelijk in Zone 32 liggen"""
         xcoor, ycoor = self._WGS84toRDforUMT31(E,N)
         return {"xRD" : xcoor, "yRD" : ycoor}

    def _RDtoWGS84OL(self,X,Y):
        """Conversie van X en Y in RD-stelsel naar OL (=Lambda) in WGS84 """
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

    def _RDtoWGS84NB(self,X,Y):
        """Conversie van X en Y in RD-stelsel naar NB (=Phi) in WGS84 """
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
        """Conversie van x en y in RD-stelsel naar Easting en Northing in WGS84 stelsel"""
        """De conversie wordt altijd gebaseerd op de parameterwaarden voor Zone 31"""

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
        """Conversie van x en y in RD-stelsel naar Easting en Northing in WGS84 stelsel"""
        """De conversie wordt gebaseerd op de parameterwaarden voor Zone 32"""

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

    def _WGS84toRDx(self,OL,NB):
        """Conversie van ellipsoidische WGS84-coordinaten (phi, lambda) naar
        X en Y in RD-stelsel. [NB,OL] = [Phi,Lambda]."""
        Lambda = OL
        Phi = NB
        
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

    def _WGS84toRDy(self,OL,NB):
        """Conversie van NB (=Phi) en OL (=Lambda) in WGS84 naar Y in RD-stelsel """
        Lambda = OL
        Phi = NB
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
        """Conversie van Easting en Northing in WGS84 stelsel naar X en Y in RD-stelsel"""
        """De conversie wordt gebaseerd op de parameterwaarden voor Zone 31"""
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
        """Conversie van Easting en Northing in WGS84 stelsel naar X en Y in RD-stelsel"""
        """De conversie wordt gebaseerd op de parameterwaarden voor Zone 32"""

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
