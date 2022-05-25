# -*- coding: utf-8 -*
# python3
# Project local settings
from os.path import dirname, realpath, join

# project dir - do not update
PROJECT_DIR = dirname(dirname(realpath(__file__)))

# Default settings values

# Default directory to search radar datas
RADAR_DATA_DIR = join(PROJECT_DIR,'test')

# File name and directory containing athletes data
ATHLETE_DATA_DIR = join(PROJECT_DIR,'data')
ATHLETE_DATA_FILE = "athlete_data.csv"

PFV_ANALYSE_DIR = join(PROJECT_DIR,'test')

EXPORT_CSV_DECIMAL='.'
EXPORT_CSV_SEPARATOR=';'
CSV_ATHLETE_SEPARATOR=';'

# if debug = true, show more messages on execution.
# Partially used
DEBUG = False

# List of exported time and distance values
EXPORT_TIMES=(5,10,20,30)
EXPORT_DISTANCES=(2,4)

# local values overwrites default values
#from sprof.settings_local import *
try:
    from sprof.settings_local import *
except ImportError:
    pass

'''
def get_logger():
    mpl_logger = logging.getLogger('matplotlib')
    mpl_logger.setLevel(logging.WARNING)

    logging.basicConfig(format='%(levelname)s : %(name)s : %(message)s',level=logging.DEBUG)
    logger = logging.getLogger('sprof')
    return logger

    #logger.info('This is an info message from sprof app')
    #logging.info('This is an info message from sprof app')
    #logging.debug('This is a debug message from sprof app')
'''
