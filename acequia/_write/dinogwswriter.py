
import datetime as dt
import numpy as np
import pandas as pd

class DinoGwsWriter:
    """Write data from GwSeries object to Dinocsv file format."""

    def __init__(self, gw):

        self.gw = gw

    def __repr__(self):
        return (f'{self.locname}_{self.fil}') # (n={len(self)})')

    @property
    def filprops(self):

        lp = self.gw.locprops()
        df = self.gw.tubeprops()

        df['locname'] = self.locname #gw.locname()
        df['filter'] = self.fil

        df['alias'] = lp.loc[self.locname,'alias']
        df['xcr'] = str(lp.loc[self.locname,'xcr'])
        df['ycr'] = str(lp.loc[self.locname,'ycr'])
        df['enddate'] =list(df['startdate'].values[1:]) + [self.gw.heads().index[-1]]
        df['mpmv'] = df['mplevel']-df['surfacelevel']

        for col in ['surfacelevel','mplevel','mpmv','filtop','filbot']:
            df[col] = df[col].apply(lambda x:str(int(x*100)) if not np.isnan(x) else '')
        for col in ['surfacedate','startdate','enddate']:
            df[col] = df[col].map(lambda x: x.strftime('%d-%m-%Y') if pd.notnull(x) else '')
            #df[col] = df[col].apply(lambda x:x.strftime('%d-%m-%Y') if not pd.notnull(x) else '')

        colnames = {'locname':'Locatie','filter':'Filternummer',
            'alias':'Externe aanduiding','xcr':'X-coordinaat',
            'ycr':'Y-coordinaat','surfacelevel':'Maaiveld (cm t.o.v. NAP)',
            'surfacedate':'Datum maaiveld gemeten','startdate':'Startdatum',
            'enddate':'Einddatum','mplevel':'Meetpunt (cm t.o.v. NAP)',
            'mpmv':'Meetpunt (cm t.o.v. MV)','filtop':'Bovenkant filter (cm t.o.v. NAP)',
            'filbot':'Onderkant filter (cm t.o.v. NAP)',}
        df = df.rename(columns=colnames)
        filprops = df[colnames.values()].copy()
        return filprops

    @property
    def heads(self):

        columns = []
        reflevels = ['mp', 'surface', 'datum']
        for ref in reflevels:
            sr = self.gw.heads(ref=ref, freq='D') * 100
            sr = sr.dropna()
            sr.name = ref
            sr = sr.apply(lambda x:str(int(x)) if not np.isnan(x) else '')
            columns.append(sr)
        df = pd.concat(columns, axis=1)

        df = df.reset_index()
        df['headdatetime'] = df['headdatetime'].apply(lambda x:x.strftime('%d-%m-%Y'))
        df.insert(0,'locname', self.locname) ##gw.locname())
        df.insert(1,'tube', self.fil) ##gw.tube().zfill(3))

        colnames= {'locname':'Locatie', 'tube':'Filternummer', 'headdatetime':'Peildatum', 
        'mp':'Stand (cm t.o.v. MP)', 'surface':'Stand (cm t.o.v. MV)', 
        'datum':'Stand (cm t.o.v. NAP)'}
        df = df.rename(columns=colnames)

        df['Bijzonderheid'] = ''
        df['Opmerking'] = ''
        heads = df.copy()
        return heads

    @property
    def locname(self):
        locname = self.gw.locname()
        #if locname.startswith('GMW'):
        #    locname = 'GMW' + locname[3:].lstrip('0')
        return locname

    @property
    def fil(self):
        return self.gw.tube().zfill(3)

    @property
    def today(self):
        today = dt.datetime.now()
        today = today.strftime('%d-%m-%Y')
        return today

    @property
    def firstdate(self):
        return self.gw.heads().index[0].strftime('%d-%m-%Y')

    @property
    def lastdate(self):
        return self.gw.heads().index[-1].strftime('%d-%m-%Y')

    @property
    def _headerlines(self):
        lines = [
            "Titel:,,,,,,,,,,,",
            "Gebruikersnaam:,,,,,,,,,,,",
            f"Periode aangevraagd:,01-01-1900,tot:,{self.today},,,,,,,,",
            f"Gegevens beschikbaar:,{self.firstdate},tot:,{self.lastdate},,,,,,,,",
            "Datum: ,17-03-2014,,,,,,,,,,",
            "Referentie:,NAP,,,,,,,,,,",
            "",
            "NAP:,Normaal Amsterdams Peil,,,,,,,,,,",
            "MV:,Maaiveld,,,,,,,,,,",
            "MP:,Meetpunt,,,,,,,,,,",
            "",
            ]
        return lines

    @property
    def _filterlines(self):

        header = ','.join(self.filprops.columns)
        lines = [header]

        for idx, row in self.filprops.iterrows():
            lines.append(
                ','.join(row.values)
                )
        lines.append('')
        lines.append('')
        return lines

    @property
    def _headslines(self):

        # append heads to flines
        header = ','.join(self.heads.columns) + ",,,"
        lines = [header]

        for idx, row in self.heads.iterrows():
            header = ','.join(row.values) + ',,,,'
            lines.append(header)

        return lines

    def get_lines(self):

        lines = []

        # get file header
        lines += self._headerlines

        # get filter properties
        lines += self._filterlines

        # get meaasured heads
        lines += self._headslines

        # final empty line
        lines += ['']

        return lines

    def save(self, fdir):
    
        lines = self.get_lines()

        fname = f'{self.locname}{self.fil}_1.csv'
        fpath = f'{fdir}{fname}'
        with open(fpath, mode='wt', encoding='utf-8') as dinofile:
            dinofile.write('\n'.join(lines))



