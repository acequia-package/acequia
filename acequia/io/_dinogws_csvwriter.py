
import datetime as _dt
import numpy as _np
import pandas as _pd
import logging as _logging

_logger = _logging.getLogger(__name__)


def save_gwseries_to_dinocsv(gw, filedir):
    """Save GwSeries to Dino csv file.
    
    Parameters
    ----------
    filedir : str
        Valid file directory.

    Returns
    -------
    DinoCsvWriter
                
    """
    dnwriter = DinoGwsWriter(gw)
    dnwriter.save(filedir)
    return dnwriter


class DinoGwsWriter:
    """Write data from GwSeries object to Dinocsv file format."""

    HEADER_COLUMNS = {
        'locname':'Locatie',
        'filter':'Filternummer',
        'alias':'Externe aanduiding',
        'xcr':'X-coordinaat',
        'ycr':'Y-coordinaat',
        'surfacelevel':'Maaiveld (cm t.o.v. NAP)',
        'surfacedate':'Datum maaiveld gemeten',
        'startdate':'Startdatum',
        'enddate':'Einddatum',
        'mplevel':'Meetpunt (cm t.o.v. NAP)',
        'mpmv':'Meetpunt (cm t.o.v. MV)',
        'filtop':'Bovenkant filter (cm t.o.v. NAP)',
        'filbot':'Onderkant filter (cm t.o.v. NAP)',
        }

    OBSERVATIONS_COLUMNS= {
        'locname':'Locatie', 
        'tube':'Filternummer', 
        'headdatetime':'Peildatum', 
        'mp':'Stand (cm t.o.v. MP)', 
        'surface':'Stand (cm t.o.v. MV)', 
        'datum':'Stand (cm t.o.v. NAP)',
        'headnote':'Bijzonderheid',
        'remarks':'Opmerking',
        }


    def __init__(self, gw):

        self._gw = gw


    def __repr__(self):
        return (f'{self.locname()}_{self.tube()}')


    def __len__(self):
        return len(self._gw)


    def header(self):
        """Return table with header data."""

        locprops = self._gw.locprops()
        tubeprops = self._gw.tubeprops()

        # if no data
        locprops_empty = all(self._gw.locprops().isnull().all())
        tubeprops_empty = all(self._gw.tubeprops().isnull().all())
        if (locprops_empty|tubeprops_empty):
            ncols = len(self.HEADER_COLUMNS.values())
            headerdata = _pd.DataFrame(
                data = [ncols*[_np.nan]],
                columns=self.HEADER_COLUMNS,
                dtype='object',
                )
            return headerdata

        # fill dataframe with headerdata
        headerdata = tubeprops.copy()
        headerdata['locname'] = self.locname()
        headerdata['filter'] = self._gw.tube().zfill(3)
        idx = locprops.index[0]
        headerdata['alias'] = locprops.loc[idx, 'alias']
        headerdata['xcr'] = str(locprops.loc[idx, 'xcr'])
        headerdata['ycr'] = str(locprops.loc[idx, 'ycr'])
        headerdata['enddate'] = list(tubeprops['startdate'].values[1:]) + [self._gw.heads().index[-1]]
        headerdata['mpmv'] = tubeprops['mplevel']-tubeprops['surfacelevel']

        for col in ['surfacelevel','mplevel','mpmv','filtop','filbot']:
            headerdata[col] = headerdata[col].apply(lambda x:str(int(x*100)) if not _np.isnan(x) else '')
        for col in ['surfacedate','startdate','enddate']:
            headerdata[col] = headerdata[col].map(lambda x: x.strftime('%d-%m-%Y') if _pd.notnull(x) else '')

        headerdata = headerdata.rename(columns=self.HEADER_COLUMNS)
        ordered_colnames = self.HEADER_COLUMNS.values()
        headerdata = headerdata[ordered_colnames].copy()
        return headerdata


    def obs(self, days=True):
        """Return table with observations.
        
        Parameters
        ----------
        days : bool, default True
            Return daily values (True) or orginnal data (False).

        Returns
        -------
        Dataframe
            Groundwater observations.
                                        
        """
        # if nodata
        if self._gw.heads().empty:
            ncols = len(self.OBSERVATIONS_COLUMNS.values())
            headstable = _pd.DataFrame(
                data = [ncols*[_np.nan]],
                columns=self.OBSERVATIONS_COLUMNS.values(),
                dtype='object',
                )
            return headstable

        # get heads in three referecne levels
        columns = []
        reflevels = ['mp', 'surface', 'datum']
        for ref in reflevels:
            if not days:
                heads = self._gw.heads(ref=ref)
            else:
                heads = self._gw.heads(ref=ref).resample('D').mean().dropna()

            heads = (heads*100).astype('int')
            heads.name = ref
            heads.index.name = 'headdatetime'
            stringhead = heads.apply(lambda x:str(int(x)) if not _np.isnan(x) else '')
            columns.append(stringhead)

        # create table of heads
        headstable = _pd.concat(columns, axis=1).reset_index()
        headstable['headdatetime'] = headstable['headdatetime'].apply(lambda x:x.strftime('%d-%m-%Y'))
        headstable.insert(0,'locname', self.locname())
        headstable.insert(1, 'tube', str(self.tube()).zfill(3))

        # add headnotes and remarks
        notes = self._gw.obs()
        notes = notes.groupby(notes['headdatetime'].dt.date).first()
        notes = notes[['headnote','remarks']].reset_index(drop=False)
        headstable = _pd.merge(
            headstable, 
            notes[['headdatetime','headnote','remarks']],
            left_on='headdatetime',
            right_on='headdatetime',
            how='left',
            )

        # rename columns
        headstable = headstable.rename(columns=self.OBSERVATIONS_COLUMNS)
        return headstable


    def locname(self):

        if all(self._gw.locprops().isnull().all()):
            return _np.nan
        locname = self._gw.locprops().loc[self._gw.locname(),'alias2']
        if _pd.isnull(locname):
            locname = self._gw.locprops().loc[self._gw.locname(),'alias']
            if locname.startswith('GMW'):
                locname = f'B{locname[3:]}'
        if _pd.isnull(locname):
            locname = self._gw.locname() #GMW000000084991
            locname = f"GMW{locname[3:].lstrip('0')}"
        return locname


    def tube(self):
        if _pd.isnull(self._gw.tube()):
            return _np.nan
        return int(self._gw.tube())


    def _today(self):
        today = _dt.datetime.now()
        return today.strftime('%d-%m-%Y')


    def _firstobsdate(self):
        heads = self._gw.heads()
        if heads.empty:
            return ''
        return heads.index[0].strftime('%d-%m-%Y')


    def _lastobsdate(self):
        heads = self._gw.heads()
        if heads.empty:
            return ''
        return heads.index[-1].strftime('%d-%m-%Y')


    def _metalines(self):
        """Return lines with request meta data."""
        lines = [
            "Titel:,,,,,,,,,,,",
            "Gebruikersnaam:,,,,,,,,,,,",
            ##f"Periode aangevraagd:,01-01-1900,tot:,{self._today()},,,,,,,,",
            f"Periode aangevraagd:,,tot:,,,,,,,,,",
            f"Gegevens beschikbaar:,{self._firstobsdate()},tot:,{self._lastobsdate()},,,,,,,,",
            f"Datum:,{self._today()},,,,,,,,,,",
            "Referentie:,NAP,,,,,,,,,,",
            "",
            "NAP:,Normaal Amsterdams Peil,,,,,,,,,,",
            "MV:,Maaiveld,,,,,,,,,,",
            "MP:,Meetpunt,,,,,,,,,,",
            "",
            ]
        return lines


    def _headerlines(self):
        """Return lines with header data."""
        headerlines = [','.join(self.header().columns)]
        for idx, row in self.header().fillna('').iterrows():
            headerlines.append(
                ','.join(row.values)
                )
        headerlines.append('')
        headerlines.append('')
        return headerlines


    def _obslines(self):
        """Return lines with observations."""
        # obs header line
        header = ','.join(self.obs().columns) + ",,,"
        obslines = [header]

        # observations
        obs = self.obs().fillna('')
        for idx, row in obs.iterrows():
            header = ','.join(row.values) + ',,,,'
            obslines.append(header)

        return obslines


    def filelines(self):
        """Return csv filelines."""

        lines = []

        # get file meta data
        lines += self._metalines()

        # get filter properties
        lines += self._headerlines()

        # get meaasured heads
        lines += self._obslines()

        # final empty line
        lines += ['']

        return lines


    def save(self, fdir):
        """Save dinocsv file.
        
        Parameters
        ----------
        fdir : str
            Path to output directoy.

        Returns
        -------
        list | None
            List with filelines.
                                
        """
        if self._gw.heads().empty:
            ##_warnings.warn((f'No measured heads for {self._gw.name()}, no dinocsv file saved.'))
            _logger.warning((f'{self.__class__.__name__}: Empty GwSeries object, no dinocsv file saved.'))
            return None

        # write file
        filelines = self.filelines()
        fname = f'{self.locname()}{str(self.tube()).zfill(3)}_1.csv'
        fpath = f'{fdir}{fname}'
        with open(fpath, mode='wt', encoding='utf-8') as dinofile:
            dinofile.write('\n'.join(filelines))

        return filelines

