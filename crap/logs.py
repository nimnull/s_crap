import logging

import sys

logger = logging.getLogger('crap')
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(console_handler)
