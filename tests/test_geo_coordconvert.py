
import pandas as pd
from pandas import Series,DataFrame
import acequia as aq



if __name__ == '__main__':

    crc = aq.CrdCon()
    Towers = crc.Towers
    twr = pd.DataFrame.from_dict(Towers, orient='columns')
    twr = twr.stack().swaplevel().sort_index(level=0)
    twr = DataFrame(twr,columns=['reference'])

    print()
    print("Reference locations:")
    print()
    print(twr)
    print()

    twr['trans'] = ''
    twr['backtrans'] = ''
    twr_names = list(twr.index.get_level_values(0).unique())
    for name in twr_names:

        # calculate column trans
        # ----------------------

        # row 1,2: RD (X,Y) to WGS84 (Lat,Lon)
        xRD = twr.loc[(name,'xRD'),'reference']
        yRD = twr.loc[(name,'yRD'),'reference']
        twr.loc[(name,'xRD'),'trans']=crc.RDtoWGS84(xRD,yRD)["Lat"]
        twr.loc[(name,'yRD'),'trans']=crc.RDtoWGS84(xRD,yRD)["Lon"]

        # row 3,4: WGS84 (Lat,Lon) to RD (X,Y)
        Lat  = twr.loc[(name,'Lat_WGS84'),'reference']
        Lon  = twr.loc[(name,'Lon_WGS84'),'reference']
        twr.loc[(name,'Lat_WGS84'),'trans'] = crc.WGS84toRD(Lon,Lat)["xRD"]
        twr.loc[(name,'Lon_WGS84'),'trans'] = crc.WGS84toRD(Lon,Lat)["yRD"]

        # row 5,6: WGS84 () to RD (X,Y)
        Lat  = twr.loc[(name,'Lat_DDMMmm'),'reference']
        Lon  = twr.loc[(name,'Lon_DDMMmm'),'reference']
        twr.loc[(name,'Lat_DDMMmm'),'trans'] = crc.WGS84toRD(Lon,Lat)["xRD"]
        twr.loc[(name,'Lon_DDMMmm'),'trans'] = crc.WGS84toRD(Lon,Lat)["yRD"]

        # row 7,8: WGS84 () to RD (X,Y)
        Lat  = twr.loc[(name,'Lat_DDMMSS'),'reference']
        Lon  = twr.loc[(name,'Lon_DDMMSS'),'reference']
        twr.loc[(name,'Lat_DDMMSS'),'trans'] = crc.WGS84toRD(Lon,Lat)["xRD"]
        twr.loc[(name,'Lon_DDMMSS'),'trans'] = crc.WGS84toRD(Lon,Lat)["yRD"]

        # row 7,8: WGS84 () to RD (X,Y)
        E  = twr.loc[(name,'East_UMT31'),'reference']
        N  = twr.loc[(name,'North_UMT31'),'reference']
        twr.loc[(name,'East_UMT31'),'trans'] = crc._WGS84toRDforUMT31(E,N)[0]
        twr.loc[(name,'North_UMT31'),'trans'] = crc._WGS84toRDforUMT31(E,N)[1]

        # row 7,8: WGS84 () to RD (X,Y)
        E  = twr.loc[(name,'East_UMT32'),'reference']
        N  = twr.loc[(name,'North_UMT32'),'reference']
        twr.loc[(name,'East_UMT32'),'trans'] = crc._WGS84toRDforUMT32(E,N)[0]
        twr.loc[(name,'North_UMT32'),'trans'] = crc._WGS84toRDforUMT32(E,N)[1]


        # calculate column backtrans
        # --------------------------

        # row 1,2: WGS84 (Lat,Lon) to RD (X,Y)
        Lat  = twr.loc[(name,'xRD'),'trans']
        Lon  = twr.loc[(name,'yRD'),'trans']
        twr.loc[(name,'xRD'),'backtrans'] = crc.WGS84toRD(Lon,Lat)["xRD"]
        twr.loc[(name,'yRD'),'backtrans'] = crc.WGS84toRD(Lon,Lat)["yRD"]

        # row 3,4: RD (X,Y) to WGS84 (Lat,Lon)
        tuples = [('Lat_WGS84','Lon_WGS84','trans','backtrans'),
                  ('Lat_DDMMmm','Lon_DDMMmm','trans','backtrans'),
                  ('Lat_DDMMSS','Lon_DDMMSS','trans','backtrans'),
                  ('East_UMT31','North_UMT31','trans','backtrans'),
                  ('East_UMT32','North_UMT32','trans','backtrans'),
                 ]
        for tp in tuples:
            xRD = twr.loc[(name,tp[0]),tp[2]]
            yRD = twr.loc[(name,tp[1]),tp[2]]
            twr.loc[(name,tp[0]),tp[3]]=crc.RDtoWGS84(xRD,yRD)["Lat"]
            twr.loc[(name,tp[1]),tp[3]]=crc.RDtoWGS84(xRD,yRD)["Lon"]

        print(twr)
        print()

    if 0:

        Ref = crc.Towers
        Torenlijst = crc.Towers.keys()
        
        

    if 0:
    
        # Referentietabel WGS84 en RD
        print()
        print("Referentiewaarden zoals ingevoerd in de tabel")
        print("-"*120)
        print("Locatie        Lon (WGS84)   Lat (WGS84)   XCOOR (RD)   YCOOR (RD)   E (UMT31)    N (UMT31)    E (UMT32)    N (UMT32)")
        for naam in Torenlijst:
            print("{!s:<15}".format(naam), end="")
            # print("{Lon_WGS84:.7f}".format(**Ref[naam]), end="")
            for key in ['Lon_WGS84','Lat_WGS84','xRD','yRD','E_UMT31',
                        'N_UMT31','E_UMT32','N_UMT32']:
                print("{:<13.3f}".format(Ref[naam][key]), end="")
            print()
        print()

    if 0: # Conversie van RD naar WGS84 naar RD
        print()
        print("RDtoWGS84      Lon (WGS84)                Lat (WGS84)                XCOOR (RD)                YCOOR (RD)")
        print("-"*120)
        print ("Locatie        Referentie   Conversie    Referentie   Conversie    Referentie   Terugconv    Referentie   Terugconv")
        for naam in Torenlijst:
            xRD = Ref[naam]['xRD']
            yRD = Ref[naam]['yRD']
            Lon  = crc.RDtoWGS84(xRD,yRD)["Lon"]
            Lat  = crc.RDtoWGS84(xRD,yRD)["Lat"]
            X   = crc.OLNBtoRD(Lon,Lat)["xRD"]
            Y   = crc.OLNBtoRD(Lon,Lat)["yRD"]
            print("{!s:<15}".format(naam), end="")
            allpairs = [(Ref[naam]['Lon_WGS84'],Lon), 
                        (Ref[naam]['Lat_WGS84'],Lat),
                        (Ref[naam]['xRD'],X),
                        (Ref[naam]['yRD'],Y)
                       ]
            for pair in allpairs:
                print("{:<12.3f} {:<13.3f}".format(pair[0],pair[1]),end="")
            print()
        print()

    if 0: # Conversie met functie RDtoWGS84
        print()
        print("Conversie met functie RDtoWGS84")
        print("-"*72)
        print("Locatie        Lon           Lat           ZONE")
        for naam in Torenlijst:
            xRD = Ref[naam]['xRD']
            yRD = Ref[naam]['yRD']
            allcoords=crc.RDtoWGS84(xRD,yRD,True)
            print("{!s:<15}".format(naam), end="")
            print("{:<13.3f}".format(allcoords["Lon"]), end="")
            print("{:<13.3f}".format(allcoords["Lat"]),  end="")
            print("{!s:<17}".format(allcoords["UMTZONE"]))
        print()

    if 0: # test functie LonNBtoRD(Lon,Lat) met verschillende invoerwaarden
        print()
        print("Functie LonNBtoRD(Lon,Lat) met verschillende notaties voor latitude,longitude")
        print("-"*120)
        myheader = "referentie  DD.dddddd   DD MM.mmm   DD MM SS.ss"
        print ("Locatie       ",myheader,myheader)

        for naam in Torenlijst:

            #print("{!s:<15}".format(naam), end="")

            Lat_ref = Ref[naam]['Lat_WGS84']
            Lon_ref = Ref[naam]['Lon_WGS84']
            rec = crc.OLNBtoRD(Lon_ref,Lat_ref)
            Lat = rec['Lat']
            Lon = rec['Lon']

            rec = crc.OLNBtoRD(Ref[naam]['Lon_DDMMmm'],
                               Ref[naam]['Lat_DDMMmm'])
            Lat_DDMMmm = rec['Lat']
            Lon_DDMMmm = rec['Lon']


            rec = crc.OLNBtoRD(Ref[naam]['Lon_DDMMSS'],
                               Ref[naam]['Lat_DDMMSS'])
            Lat_DDMMSS = rec['Lat']
            Lon_DDMMSS = rec['Lon']


            print("{!s:<15}".format(naam), end="")
            for number in [Lon_ref, Lon, Lon_DDMMmm, Lon_DDMMSS,
                           Lat_ref, Lat, Lat_DDMMmm, Lat_DDMMSS]:
                print("{:<12.3f}".format(number), end="")
            print()

        print()
