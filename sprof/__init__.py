 # -*- coding: utf-8 -*
# python3
import logging
from sprof.settings import DEBUG

# on desactive le logger de matplotlib qui balance plein de truc
mpl_logger = logging.getLogger('matplotlib')
mpl_logger.setLevel(logging.WARNING)

# ex avec le nom du logger.        
#logging.basicConfig(format='%(levelname)s : %(name)s : %(message)s',level=logging.DEBUG)

if DEBUG:
    logging.basicConfig(format='%(levelname)s %(message)s',level=logging.DEBUG)
else:
    logging.basicConfig(format='%(levelname)s %(message)s',level=logging.INFO)

#logger = logging.getLogger('sprof')
#logger.info('This is an info message from sprof app')
#print("ok, on a fait qq chose dans __init__")
#logging.info('This is an info message from sprof app')
#logging.debug('This is a debug message from sprof app')