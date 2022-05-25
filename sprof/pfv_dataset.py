# -*- coding: utf-8 -*
# python3
# Author : LJK - Laboratoire Jean Kuntzmann - C. Bligny
"""
Manage several pfv profiling , save the result to csv file
"""
import os
from datetime import datetime
import pandas as pd
from sprof.radar_file import params_get_files
from sprof.analyse import build_analyse_from_file
from sprof.settings import PFV_ANALYSE_DIR
from sprof.settings import EXPORT_CSV_DECIMAL, EXPORT_CSV_SEPARATOR
from sprof.settings import EXPORT_TIMES, EXPORT_DISTANCES

# ------ PFV Dataset Class Builder ------------------------------------------------------

def build_PFV_DS_from_files(files, name="", auto=True, outliers=True):

    ds=PFVDataset(name=name)
    for file in files:
        ds.add_row_from_file(file, auto=auto, outliers=outliers)
    return ds

# ------ PFV Dataset Class --------------------------------------------------------------

class PFVDataset():

    EXPORT_FILE_PATTERN = "pfv"

    # liste ordonnée des colonnes potentielles à exporter
    # colonnes de base
    EXPORT_MAIN_COLS=['name','mass','V0', 'F0','F0_kg','Pmax','Pmax_kg','sfv','RF_peak', 'DRF','top_speed','tau' ]

    # Informations qualité données
    EXPORT_CHECK_COLS=['points_out','plateau_duration','vmax_diff']

    # titre de toutes les colonnes (l'ordre n'importe pas, il sera donné par EXPORT_COLUMNS)
    COL_TITLES={ 'name':'Sprint title',
                    #   'v_max':'v max th (m/s)',
                    'top_speed':'top speed (m/s)',
                    'tau':'Acc. constant',
                    'mass':'Mass (kg)',
                    #'stature':'Stature (m)',
                    'duration':'duration (s)',
                    'stature':'stature (m)',
                    'F0':'F0 (N)',
                    'V0': 'V0 (m/s)',
                    'Pmax':'P max (W)',
                    'F0_kg':'F0 (N/kg)',
                    'Pmax_kg':'P max (W/kg)',
                    'sfv':'Force-Velocity profile',
                    'RF_peak':'RF peak',
                    'DRF':'DRF (%)',
                    'temp':'temperature (°C )',
                    'pression' : 'pression (hPa)',
                     # Infos de temps et de distances : construites dans le __init__
                     # Informations qualité des données
                     'points_out':'Nb points out',
                     'plateau_duration':'Plateau (s)',
                     'vmax_diff':'Diff vmax th/measure'
                     }

    # compare 2 dataframes
    COMPARE_COLS = ['V0 (m/s)','F0 (N)','P max (W)','Force-Velocity profile','RF peak','DRF (%)','top speed (m/s)', 'Acceleration constant']

    def __init__(self,name=""):

        self.name=name

        # Init the column and column title list
        self.export_cols = self.EXPORT_MAIN_COLS+self._get_optional_export_cols()+self.EXPORT_CHECK_COLS
        self.export_col_titles = dict(self.COL_TITLES,**self._get_optional_col_titles())

        # Init the dataframe with the columns titles
        #titles=self._get_export_titles()
        self.datas=pd.DataFrame(columns=self._get_export_titles())
        #self.data=self.datas.set_index('Sprint title')
        #print(self.datas)

        # build the export file
        self.export_filename=self._get_export_filename()
        self.export_file=self._get_export_file()
        self.data_dir=""

        # get the atheles dataset
        #self.athletes=AthleteDS()
        '''
        # potentially other attributes
        self.run_date
        self.pression
        self.temperature
        self.wind
        '''

    def __str__(self):
        return str(self.datas)

    def export_csv(self, filename=None):
        """ Save datas into csv file.
        """
        if self.datas.empty:
            print("Le dataset est vide, pas d'export")
        else:
            decimal = EXPORT_CSV_DECIMAL
            sep = EXPORT_CSV_SEPARATOR
            if not(filename):
                filename=self.export_file
            self.datas=self.datas.sort_values(by=self.export_col_titles['name'])
            self.datas.to_csv(filename,decimal=decimal,sep=sep,index = None, header=True)
            print(f"Données exportées dans le fichier : {filename}")

    def read_csv(self, filename):
        """ Read dataset from csv file.
        """
        # On teste pas si c'est au bon format, si ya les bonne colonnes
        # --> réservé à data_watcher, et pas très robuste
        decimal = EXPORT_CSV_DECIMAL
        sep = EXPORT_CSV_SEPARATOR
        if os.path.exists(filename):
            try:
                df=pd.read_csv(filename, decimal=decimal,sep=sep)#,header=True)
                self.datas=df
            except:
                print(f"Impossible de récupérer des données à partir du fichier {filename}")
        else:
            print(f"Read CSV - fichier {filename} non trouvé")

    def add_row(self,attr_dict):
        """ Add a raw to the dataset.
            A raw is the data resulting of the analyse of a sprint.
            The input parameter is a dictionnary with the values
        """
        # Note : what if the raw already exists ?

        dict={}
        nb_rows_ini=self.datas.shape[0]

        for key in self.export_cols:
            title=self.export_col_titles[key]
            value=attr_dict[key]
            dict.update({title:value})

        #print(dict)
        # on met à jour ['Sprint title'] pour que le premier caractere soit en majuscule
        # bah, faudrait faire ça mieux et le mettre dans utils ?
        title=dict['Sprint title'].rstrip()
        if len(title) > 1:
            title = title[0].upper() + title[1:]
            title=title.lstrip().lstrip("Juillet").lstrip()
            if (title[-1].isnumeric() and title[-2].isalpha()):
                title=title[0:-2]+' '+title[-1]
            dict['Sprint title']=title

        # on ajoute aux données et on trie par ordre alphabétique
        self.datas = self.datas.append(dict, ignore_index=True)
        self.datas=self.datas.sort_values(by=['Sprint title'])
        self.datas =self.datas.reset_index(drop=True)
        #self.data=self.datas.set_index('Sprint title')
        #print(self.datas)
        # rechercher du cote de df.loc['new titlte']=['liste',2,'des','valeurs']

        nb_row_add=self.datas.shape[0]-nb_rows_ini
        return nb_row_add

    def add_row_from_analyse(self, a):
        """ Add a raw to the dataset.
            The input parameter is an sprof object "Analyse"
            This method extract the values to put to the dataset from the Analyse object.
        """

        nb_row_add=0

        if a and a.pfv and a.sprint:

             # dictionnaire des attributs simplifiés : sans les arrays, et avec les float à 2 digits
            data_dic=a.pfv.simp_vars()

            #data_dic.update({'name':sprint_name+" sp"})
            # on met à jour le nom. Vérifier si c'est nécessaire
            data_dic.update({'name':a.sprint.title})

            # Ajout des temps par distance.
            for time in EXPORT_TIMES:
                data_dic.update({self._get_time_colname(time):a.pfv.str_time_distance(time)})

            # Ajout des distances pour un temps donné
            for distance in EXPORT_DISTANCES:
                data_dic.update({self._get_dist_colname(distance):a.pfv.str_distance_time(distance)})

            # on ajoute les infos de qualité des données
            data_dic.update({'points_out':a.points_out})
            data_dic.update({'plateau_duration':a.plateau_duration})
            data_dic.update({'vmax_diff':a.vmax_diff})

            # ajoute la ligne au dataset
            nb_row_add=self.add_row(data_dic)

        else:
            print("Warning - DS add_row_from_analyse - l'analyse n'est pas complète")

        # return le nb de row ajouté
        return nb_row_add

    def add_row_from_file(self, file, auto=True, outliers=True):
        """ Add a raw to the dataset.
            The input parameter is a file containing sprint data
            This method build an Analyse object from the input file, and then add a
            raw to the dataset from this Analyse.
        """
        nb_row_add=0
        a=build_analyse_from_file(file, auto=auto, outliers=outliers)
        nb_row_add = self.add_row_from_analyse(a)

        # set dir to last file dir
        self.data_dir=os.path.dirname(file)

        return nb_row_add

    def compare(self,df2):
        """
        Compare the variation (%) between 2 PFV dataframes
        Returns a dataframe
        """
        df1 = self.datas

        df_diff = round( (df1[self.COMPARE_COLS] - df2[self.COMPARE_COLS])*100/abs(df1[self.COMPARE_COLS]), 1)
        df_diff['Sprint title']=df1['Sprint title']

        return df_diff

    def _get_export_file(self):
        """ Returns default export fullpath file
        """
        file=os.path.join(PFV_ANALYSE_DIR,self.export_filename)
        return file

    def _get_export_filename(self):
        """ Returns the export filename
        """
        dt = datetime.today()
        strDate=dt.strftime("%y%m%d")
        #filename = strDate+'_'+self.name+'_'+self.EXPORT_FILE_PATTERN+'.csv'
        filename = strDate+'_'+self.EXPORT_FILE_PATTERN
        if self.name:
            filename+='_'+self.name
        filename += '.csv'
        return filename

    def _get_time_colname(self,time):
        #'time_5m':'Time @ 5 m (s)'
        return f'time_{time}m'

    def _get_dist_colname(self,distance):
        #'distance_2s':'Distance in 2 s (m)'
        return f'distance_{distance}s'

    def _get_time_coltitle(self,time):
        #'time_5m':'Time @ 5 m (s)'
        return f'Time @ {time} m (s)'

    def _get_dist_coltitle(self,distance):
        #'distance_2s':'Distance in 2 s (m)'
        return f'Distance in {distance} s (m)'

    def _get_optional_export_cols(self):
        col_times=[self._get_time_colname(time) for time in EXPORT_TIMES]
        col_dist=[self._get_dist_colname(distance) for distance in EXPORT_DISTANCES]
        return col_times+col_dist

    def _get_optional_col_titles(self):
        col_time_titles={self._get_time_colname(time):self._get_time_coltitle(time) for time in EXPORT_TIMES}
        col_dist_titles={self._get_dist_colname(distance):self._get_dist_coltitle(distance) for distance in EXPORT_DISTANCES}
        #return col_time_titles+col_dist_titles
        return dict(col_time_titles, **col_dist_titles);

    def _get_export_titles(self):
        titles=[]
        for col in self.export_cols:
            title=self.export_col_titles[col]
            titles.append(title)
        return titles

 # ------ Main --------------------------------------------------------------------------
if __name__ == "__main__":
    # test PFVDataset

    def test_columns():
        ds=PFVDataset("simple_test")
        print(ds.export_col_titles)
        print(ds.export_cols)

    # pour test pas trop long :
    # python pfv_dataset.py -p fou
    # ou
    # python pfv_dataset.py -p ma

    files = params_get_files()

    def test_files():
        ds=build_PFV_DS_from_files(files,'test_files')
        print(ds)

    def analyse():
        ds=build_PFV_DS_from_files(files,'Analyse')
        print(ds)
        # save pfv analyse to default analyse dir
        ds.export_csv()
        # save pfv analyse to data dir
        if ds.data_dir:
            file=os.path.join(ds.data_dir,ds.export_filename)
            ds.export_csv(file)

    #test_columns()
    #test_files()
    analyse()
