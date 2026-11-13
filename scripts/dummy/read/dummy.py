#!/usr/bin/env python3

import time
import logging

# use the same logger name
logger = logging.getLogger( 'star_logger' )
logger.info( 'logger initialized in read dummy' )

#
logger.info( 'dummy: reading signal beginning ...' )

while True:
	time.sleep(5)

logger.info( 'dummy: reading signal done' )


