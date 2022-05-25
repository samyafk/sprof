# -*- coding: utf-8 -*
# python3
# Author : LJK - Laboratoire Jean Kuntzmann - C. Bligny
"""
    radar file module. Contains :
    - methods to get command line radar file params
    - methods to parse a dir and get the radar file(s)
    - RadarFile class : load radar datas from radar files provided by STALKER,
    version 5.020 and build the numpy arrays T adn V (times and velocities)

	 Radar Files :
	.rad files : processed data + meta datas
	.rda files : row data
"""

import numpy as np
import matplotlib.pyplot as plt
import logging
import os
from datetime import datetime
from sprof.utils import str_simplify, print_obj_attr
from sprof.settings import RADAR_DATA_DIR

RAD_FILE_EXTENSION = ".rad"
RDA_FILE_EXTENSION = ".rda"
DEFAULT_EXTENSION = RDA_FILE_EXTENSION

# ------ Decorator ----------------------------------------------------------------------

def scan_dir(max_file=5):
    def decorated(func):
        def wrapper(*args, **kwargs):
            # Pré-traitement
            files = params_get_files()
            i=1
            for file in files:
                i+=1
                func(file)
                if i>max_file:
                    break
            #return response
        return wrapper
    return decorated

# ------ Utils --------------------------------------------------------------------------

def params_get_file():
    ''' Get one file name, using command line parameters
    '''
    (dir,filepattern,fileext,file) = get_file_params()

    if not(file):
        files = search_radar_files(dir, filepattern, fileext )
        file=next(files,None)

    return file

def search_radar_file(dir=".", pattern="",ext=""):
    ''' Get one file name, using method parameters
    '''
    files = search_radar_files(dir, pattern, ext )
    file=next(files,None)
    return file

def params_get_files():
    ''' Get a list of file name, using command line parameters
    '''
    (dir,filepattern,fileext,file) = get_file_params()
    return search_radar_files(dir=dir, pattern=filepattern,ext=fileext)

def search_radar_files(dir=".", pattern="",ext=""):
    ''' Get a list of file name, using method parameters
    '''
    # iterateur : retourne tous les fichiers radar dans le rep dir, qui contiennent
    # filepattern dans le nom. retourne le .rda en priorité, le .rad si E pas la rda

    # if pattern ends by a number, split it
    # permet de taper un pattern type alex2
    # un certain nombre de pre-supposé, notemment que le file name de type "... atheletename d.rda"
    # avec d le digit
    # si changement, on met la date en numérique, et à la fin, ça va plus marcher
    # si plus de 9 sprints, ça va pas marcher non plus
    # mais en attentant, c'est super pratique pour tester.

    # ATTENTION : default data dir ici est le rep courant . - mais dans get param on utilise les DATA_DIR. A voir

    sprint_number=""
    if pattern:
        if pattern[-1].isdigit():
            sprint_number=pattern[-1]
            pattern = pattern[0:-1] # on enlève le dernier caractère au pattern

    # on vérifie l'extension, on récupère celle par défaut
    required_ext = check_radar_ext(ext)

    for file in os.listdir(dir):
        # check the hidden files. there are some with windows
        # or problem with unclosed files?
        if not(file.startswith('.')):
            # analyse only .rad files
            fileext = os.path.splitext(file)[-1]
            #basename = os.path.splitext(file)[0]
            if (fileext==required_ext):
                # search if the file name contains name
                if str_simplify(pattern) in str_simplify(file):
                    if ( sprint_number and file[-5].isdigit()):
                        if file[-5]==sprint_number:
                            fullpath=os.path.join(dir,file)
                            yield fullpath
                    else:
                        fullpath=os.path.join(dir,file)
                        yield fullpath

def get_file_params():
    ''' Get file parameter from command line.
    Wether a full file name (with path), or some search indications : the directory,
    the pattern the filename will contains, and the file extention
    '''
    #dir ="/Users/bligny/Projects/innovalie/30-07_Fichiers_traite/Avants Pro"
    dir = RADAR_DATA_DIR
    filepattern=""
    fileext=""
    file=""

    # get command line parameters
    import argparse
    desc="On peut donner en argument soit le nom complet du fichier (--file ou -f), soit des\
    elements qui vont permettre de chercher des fichiers : le répertoire, \
    l'extention du nom du fichier, et tout ou partie du nom du fichier (le pattern)."
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('--dir', '-d',help='Répertoire contenant les données')
    parser.add_argument('--pattern', '-p', help='Le nom du fichier contient ce pattern. Exemple : alex ou alex2')
    parser.add_argument('--ext', '-e', help='Forcer l\'extention du fichier (rad ou rda)')
    parser.add_argument('--file', '-f', help='Fichier contenant les données')
    args = parser.parse_args()

    # if user defines read and write arguments at the same time raise exception
    if args.file and not all(arg is None for arg in (args.dir, args.pattern, args.ext)):
        parser.error('Erreur dans les paramètres : Si le fichier (-f ou --file) est fourni, \
        il ne faut pas utiliser les autres paramètres')

    if args.file:
        file=args.file
    if args.dir:
        dir=args.dir
    if args.pattern:
        filepattern=args.pattern
    if args.ext:
        fileext=args.ext

    return (dir,filepattern,fileext,file)

def check_radar_ext(ext):
    # check that an extention is compatible with radar files
    # if not, or empty, returns the default file extension

    if not(ext):
        ext = DEFAULT_EXTENSION

    # add the '.' to the extention if not present
    if not(ext.startswith('.')):
        ext="." + ext

    if not(ext == RAD_FILE_EXTENSION or ext == RDA_FILE_EXTENSION):
        print("L'Extension fournie n'est pas valide, elle ne sera pas prise en compte")
        ext = DEFAULT_EXTENSION

    return ext


# ------ RadarFile Class ----------------------------------------------------------------

def build_RF_from_pattern(dir="", pattern="", ext=""):
    """
    Build and returns a RadarData instance, using a radar data file.
    """
    if not dir:
        dir = RADAR_DATA_DIR

    file = search_radar_file(dir=dir, pattern=pattern,ext=ext)
    print(f"nom de fichier trouvé : {file}")
    radar_file=RadarFile(file)
    return radar_file


class RadarFile:

    # Présuposé sur le format STALKER. En cas de changement de version, il se peut que cela
    # ne fonctionne plus

    # File format contants
    #.rad files
    RAD_FIRST_LINE = "STALKER Version 5.020 using ATS II"
    RAD_BEFORE_LAST_LINE = "END OF FILE"
    RAD_COLUMN_LINE = "  Sample   Time   Speed   Accel     Dist"
    RAD_COLUMN_LINE_IDX = 16 # Line number for columns names
    RAD_SPEED_UNIT_IDX = 11	 # Line number for speed unit
    RAD_NAME_IDX = 2         # Line number for data name (usually, athlete name)
    RAD_DATETIME_IDX = 3     # Line number for record date
    RAD_SAMPLE_RATE_IDX = 6  # line number to get the sample range
    RAD_START_IDX = 18
    RAD_END_IDX = -2

    #.rda files
    RDA_FIRST_LINE = "STALKER Version 5.020 using ATS II radar gun"
    RDA_START_IDX = 4
    RDA_END_IDX = -1

    # default values
    DEF_SAMPLE_RATE = 46.875 # Hertz. Number of events (here, measures) in one second.
    DEF_SPEED_UNITS = ('meters/sec','m/s','mètres/seconde')

    def __init__(self, filename = None, debug=False):
        """Class Attributes.
           Convention : for velocity (v, V) and time (T, t), Arrays/Vectors starts
           with uppercase, scalar with lowercase
        """

        # input file
        self.filename = filename

        # Data directly from file
        self.file_ext=""
        self.T = [] # Time array
        self.V = [] # Velocity array
        self.n = 0 # Points number (arrays size)
        self.title = "" # Sprint title - usually athlete name + trial number
        self.date = ""
        self.sample_rate = 0.0 # replace by a get_sample_rate
        self.speed_unit=""

        # get the file extension of the input file
        if filename:

            # test if file exists
            if not(os.path.isfile(filename)):
                print(f"Erreur : le fichier {filename} n'existe pas")
            else:
                ext=filename[-4:]
                if ext not in (RAD_FILE_EXTENSION, RDA_FILE_EXTENSION):
                    print("Erreur : Le fichier fourni ne semble pas être un fichier radar")
                else:
                    self.file_ext = filename[-4:] # file extention
                    self._load_header()
                    self._load_data()
        else :
        	print("Il faut donner en paramètre un fichier radar")

        print(f"Fichier {self.filename} : {self.n} points chargés")


    def print_attr(self):
        print_obj_attr(self)

    def _get_rad_file(self):
        return self.filename[:-4] + RAD_FILE_EXTENSION

    def _get_rda_file(self):
        return self.filename[:-4] + RDA_FILE_EXTENSION

    def _exists_rad_file(self):
        return os.path.exists(self._get_rad_file())

    def _exists_rda_file(self):
        return os.path.exists(self._get_rda_file())

    def _load_header(self):
        """
        Charge les données d'entête.
        Elles sont contenu dans le fichier rad, si non trouvé on garde le nom du fichier
        dans le nom, et on n'a pas la date
        returns false if there is an error in the header
        """
        # todo : mettre self.date au même format

        logging.debug(f"Chargement de l'entête")

        if self._exists_rad_file():
            rad_file = open(self._get_rad_file(),'r')
            # boucle sur les lignes. check la premiere, get name, date, sample_rate, speed unit (11 si on part à 0)
            for i in range(0,12):
                line=rad_file.readline().rstrip('\n')
                if i==0:
                    # check first tile
                    if not(line == self.RAD_FIRST_LINE):
                        logging.warning("Attention : la première ligne n'est pas du format attendu")
                        logging.warning(f"Format attendu : '{self.RAD_FIRST_LINE}'")
                        logging.warning(f"Valeur de la première ligne : '{line}'")
                if i == self.RAD_NAME_IDX:
                    self.title = line.split(':')[-1].strip()
                if i == self.RAD_DATETIME_IDX:
                    datetime_line = line.split()
                    self.date = datetime_line[0] + " - "+datetime_line[1]
                    # TODO :  format if to datetime
                if i == self.RAD_SAMPLE_RATE_IDX:
                    str_rate = line.split(':')[-1]
                    self.sample_rate = float(str_rate.replace(',','.'))
                if i == self.RAD_SPEED_UNIT_IDX:
                    self.speed_unit = line.split(":")[1].strip()
                    if self.speed_unit not in (self.DEF_SPEED_UNITS):
                        logging.warning("Attention : l'unité pour la vitesse n'est pas celle attendue")
                        logging.warning(f"Unités attendues : '{self.DEF_SPEED_UNITS}'")
                        logging.warning(f"Unité trouvé dans le fichier : '{self.speed_unit}'")

            rad_file.close()

        else:
            # title = nom du fichier sans l'extention et sans le rep
            basefile = os.path.basename(os.path.normpath(self.filename))
            self.title = basefile[:-4]
            # sample_rate = default sample rate
            self.sample_rate=self.DEF_SAMPLE_RATE
            # date = date of unix timestamp of file last modification
            ts = os.path.getmtime(self.filename)
            self.date=datetime.utcfromtimestamp(ts)
            self.speed_unit=self.DEF_SPEED_UNITS[0]


    def _load_data(self):

        file_radar=open(self.filename,'r')

		# Load all file lines at once into an array - OK for a reasonable file size
        all_lines=file_radar.read()
        file_radar.close()
        all_lines=all_lines.split('\n')

        if self.file_ext == RDA_FILE_EXTENSION:
            self._load_rda_data(all_lines)
        elif self.file_ext == RAD_FILE_EXTENSION:
            self._load_rad_data(all_lines)
        else:
            print("Le fichier fourni ne semble pas être un fichier radar")

        logging.debug(f"{self.n} points de mesure chargés")
        if self.n>0:
            logging.debug(f"Tmin = {self.T[0]} Tmax = {self.T[-1]} , Vmin = {self.V[0]} Vmax = {self.V[-1]}")


    def _load_rad_data(self,lines):
        """
        Read the input radar file and fill class attributes
        Returns the number of lines loaded.
        """
        logging.debug(f"Chargement des données au format rad")

        # Some checks
        if not(lines[0] == self.RAD_FIRST_LINE):
            logging.warning("Attention : la première ligne n'est pas du format attendu")
            logging.warning(f"Format attendu : '{self.RAD_FIRST_LINE}'")
            logging.warning(f"Valeur de la première ligne : '{lines[0]}'")
            return 0

        if not(lines[16] == self.RAD_COLUMN_LINE):
            logging.warning("Attention : la lignes des nom de colonnes n'est pas du format attendu")
            logging.warning(f"Format attendu : '{self.RAD_COLUMN_LINE}'")
            logging.warning(f"Valeur de la ligne d'indice {self.RAD_COLUMN_LINE_IDX} : '{lines[self.RAD_COLUMN_LINE_IDX]}'")
            return 0

        if not(lines[-2] == self.RAD_BEFORE_LAST_LINE):
            logging.warning("Attention : la lignes de fin du fichier n'est pas du format attendu")
            logging.warning(f"Format attendu : '{self.RAD_BEFORE_LAST_LINE}'")
            logging.warning(f"Valeur de la ligne d'indice 16 : '{lines[-2]}'")
            return 0

        data_lines=lines[self.RAD_START_IDX:self.RAD_END_IDX] # Last line is empty, before last = "end of file"

        # Build the data arrays, converting string to float
        datas = np.array([[float(x.replace(',','.')) for x in line.split()] for line in data_lines])

        # init some class attributs
        self.n = datas.shape[0]
        self.T = datas[:,1]
        self.V = datas[:,2]

        logging.debug(f"{self.n} points de mesure chargés - format rad")

        return self.n

    def _load_rda_data(self, lines):

        logging.debug(f"Chargement des données au format rda")

        # Some checks
        if not(lines[0] == self.RDA_FIRST_LINE):
            logging.warning("Attention : la première ligne n'est pas du format attendu")
            logging.warning(f"Format attendu : '{self.RDA_FIRST_LINE}'")
            logging.warning(f"Valeur de la première ligne : '{lines[0]}'")
            return 0

        # Build the data arrays, converting string to float
        self.V = np.array([float(x.replace(',','.')) for x in lines[self.RDA_START_IDX:self.RDA_END_IDX]])

        # init some class attributs
        self.n = len(self.V)

        end_time=(self.n-1)/self.sample_rate # c'est mieux self.n-1 - mais un peu empirique
        self.T = np.linspace(0,end_time,self.n)

        # on arrondis à 2 chiffes après la virgule
        self.T=np.around(self.T,decimals=2)

        return self.n

if __name__ == "__main__":


    def test_get_file_params():
        """
        Tests exemples :
        python radar_file.py -p berru -e toto --dir "/this/is/my/dir"
        python radar_file.py -p berru --ext rad
        python radar_file.py --help
        python radar_file.py -f "this is a full file name and path"
        python radar_file.py -p berru --ext rad -f "this will end with an error"
        """
        print("\n ===== test_get_file_params =====")
        (dir,filepattern,fileext,file) = get_file_params()
        print(f"dir : {dir}")
        print(f"file pattern : {filepattern}")
        print(f"file ext : {fileext}")
        print(f"file : {file}")


    def test_check_radar_ext():
        """
        Test exemple :
        python radar_file.py --ext rad
        python radar_file.py -e rda
        python radar_file.py --ext toto
        """
        print("\n ===== test_check_radar_ext =====")
        (dir,filepattern,fileext,file) = get_file_params()
        print( check_radar_ext(fileext) )


    def test_params_get_files():
        """
        Test exemples :
        python radar_file.py -p ma1
        python radar_file.py -p ma1 -e rad
        """
        print("\n ===== test_params_get_files =====")
        files = params_get_files()
        for file in files:
            print(file)

    def test_params_get_file():
        """
        Test exemples :
        python radar_file.py -p ma1
        python radar_file.py -p ma1 -e rad
        """
        print("\n ===== test_params_get_file =====")
        file = params_get_file()
        print(file)

    # test RadarFile class
    def test_radar_file():
        print("\n ===== test RadarFile class =====")

        file1 = params_get_file()

        f1=RadarFile(file1)
        f1.print_attr()

        file2=file1[:-4]+'.rad'
        f2=RadarFile(file2)
        f2.print_attr()

        plt.plot(f2.T, f2.V)
        plt.plot(f1.T, f1.V)

        plt.show()

    # test RadarFile class
    def plot_radar_file():
        print("\n ===== Plot radar file =====")

        # Get file -
        file1 = params_get_file()

        f1=RadarFile(file1)
        #f1.print_attr()

        # Possibly plot rad file
        '''
        if f1.file_ext==".rda":
            print("Recherche du .rad")
            file2=file1[:-4]+'.rad'
            f2=RadarFile(file2)
            if f2.file_ext==".rad":
                plt.plot(f2.T, f2.V,'g')
        '''

        plt.plot(f1.T, f1.V,color='b')
        plt.title(f1.title+" "+f1.file_ext)

        #plt.show()

        #basefile = os.path.basename(os.path.normpath(file1))
        imgfile = file1[:-4]
        #if pattern:
        #    basefile+='_'+pattern
        imgfile+=f1.file_ext+'.png'
        #fullpath=os.path.join(dir,basefile)
        print(imgfile)
        plt.savefig(imgfile)
        #plt.close()
        plt.show()

    #test_radar_file()
    #test_get_file_params()
    #test_check_radar_ext()
    #test_params_get_files()
    #test_params_get_file()
    plot_radar_file()


    # Ce qu'on veut : la même chose que analyse et tuti quanti, mais avec un "bete" plot
