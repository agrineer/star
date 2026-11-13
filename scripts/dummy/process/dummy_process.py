#!/usr/bin/env python3
#
# dummy post processing script
#
import time
import logging

# use the same logger name
logger = logging.getLogger( 'star_logger' )
logger.info( 'logger initialized in dummy processing' )
  
logger.info( 'dummy process: post processing beginning ...' )
time.sleep(5)
logger.info( 'dummy process: post processing done.')
