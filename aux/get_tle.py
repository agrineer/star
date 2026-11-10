#!/usr/bin/env python3

#  get_tle.py                                                       
#                                                                               
#  Copyright (C) 2020-2026 Scott L. Williams
#                                                                               
#  This program is free software; you can redistribute it and/or modify         
#  it under the terms of the GNU General Public License as published by         
#  the Free Software Foundation; either version 3 of the License, or            
#  (at your option) any later version.                                          
#                                                                               
#  This program is distributed in the hope that it will be useful,              
#  but WITHOUT ANY WARRANTY; without even the implied warranty of               
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                
#  GNU General Public License for more details.                                 
#                                                                               
#  You should have received a copy of the GNU General Public License            
#  along with this program; if not, write to the Free Software                  
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#  or visit https://www.gnu.org/licenses/gpl-3.0-standalone.html or
#  see http://www.gnu.org/licenses/gpl-3.0.html

copyright = 'get_tle.py Copyright (c) 2016-2026 Scott L. Williams ' + \
            'released under GNU GPL V3.0'   

# get specific satellite TLEs

import os
import sys
import time
import glob
import string
import datetime

# NOTE: celestrack searches name and returns any sat that contains the name
weather_sats = ['NOAA 18', 'NOAA 19', 'METOP-A', 'METOP-B', 'METOP-C' ]
resource_sats = ['TERRA', 'AQUA']

# print fuctions to reduce clutter and to flush
def eprint( *args ):
    print( *args, file=sys.stderr, flush=True)

# print out exit message
def print_and_exit( *args ):
    eprint( *args )
    sys.exit( 2 )
       
# run system command and exit if fails
def os_command( command ):
    #eprint( 'running command: ' + command )
    status = os.system( command )
    if status != 0:
        print_and_exit( 'something went wrong...cannot run command:', command  )

def get_files( stype, sats ):

    # save last file; use os.system;
    # if there is no file to move, error is ignored
    os.system( 'mv -f ' + stype + '.tle ' + stype + '.tle.OLD' )

    # start new file
    os_command( 'touch ' + stype +'.tle' )

    # get TLEs for given satellites
    for s in sats:

        fname = '"gp.php?NAME=' + s + '&FORMAT=TLE"'
        loc = 'https://celestrak.org/NORAD/elements/' + fname
              
        eprint( 'getting TLE for: ', s )
        os_command( 'wget ' + loc )
        os_command( 'cat ' + fname + ' >> ' + stype + '.tle' )
        os_command( 'rm ' + fname )

    os_command( 'rm -f ' + 'wget.*' )

########################################################
# main

# get orbit directory 
star_home = os.environ['STAR_HOME']
orbit_dir = star_home + '/orbits'

os.chdir( orbit_dir )

get_files( 'weather', weather_sats )
get_files( 'resource', resource_sats )












