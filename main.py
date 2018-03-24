import os
import sys
import logging
import json
import datetime as dt

token = os.environ['TOKEN']

if not os.path.exists(os.path.join(path_name, 'logs')):
    os.mkdir(os.path.join(path_name, 'logs'))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# .log name variables
date = '{dia}_{hora}'.format(dia=dt.datetime.today().strftime("%Y%m%d"),
                             hora=dt.datetime.now().time().strftime("%H%M%S"))

path_name = os.path.abspath(os.path.dirname(sys.argv[0]))

script_name = os.path.basename(__file__)

# log name. Format example: .../myapp_20170613_150738.log
log_file = '{p}/logs/{f}_{d}.log'.format(p=path_name,
                                         f=script_name,
                                         d=date)
# handler
hdlr = logging.FileHandler(log_file)
# .log line format i.e date and time attached.
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
# logging level.
logger.setLevel(logging.INFO)

start = dt.datetime.now()

logger.info("IT'S SHOWTIME")


