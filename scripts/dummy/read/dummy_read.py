#!/usr/bin/env python3

import time
import logging

# use the same logger name
logger = logging.getLogger( 'star_logger' )
logger.info( 'logger initialized in dummy read' )

#
logger.info( 'dummy read: reading signal beginning ...' )

while True:
	time.sleep(5)

logger.info( 'dummy read: reading signal done' )


