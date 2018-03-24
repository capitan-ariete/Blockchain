import os
import logging
import datetime as dt

token = os.environ['TOKEN']

if not os.path.isdir('logs'):
    os.makedirs('logs')
if not os.path.isfile('logs/python.log'):
    os.mknod('logs/python.log')

logger = logging.getLogger(__name__)
fileConfig('logger.ini')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

start = dt.datetime.now()

logger.info("IT'S SHOWTIME")


