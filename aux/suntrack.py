#! /usr/bin/env /usr/bin/python3
'''
@file suntrack.py
@author Scott L. Williams
@package STaR
@brief Tracks the sun for antenna alignment.
@section LICENSE 
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
#

@section DESCRIPTION
Points the antenna toward the sun for adjusting azimuth,elevation angles and
lead time. Adjustments get written to the configuration file.
'''

startrack_copyright = 'suntrack.py Copyright (c) 2020 Scott L. Williams ' + \
                      'released under GNU GPL V3.0'

import os
import sys
import math
import time

import configparser
import ephem

# our imports
from suntracker import suntracker
#from load_module import load_module

# track the sun for antenna positioning
class suntrack():  
    def __init__( self, config_file ): 

        # start configuration 
        self.config_file = config_file
        config = configparser.RawConfigParser()        
        config.read( config_file )  

        # read ground station location
        self.lat = config.get( 'location', 'latitude' )
        self.lon = config.get( 'location','longitude' ) 
        self.alt = config.getfloat( 'location','altitude' )

        self.configure_rotor( config_file )

    # dynamically load rotor module
    def configure_rotor( self, config_file ):
        config = configparser.RawConfigParser()
        config.read( config_file )  

        try:
            module_path = config.get('rotor','module')
        except:
            print( 'configure_rotor: could not read module path, exiting.',
                   file=sys.stderr, flush=True)
            sys.exit(1)
        try:
            module = load_module( module_path ) 
        except:
            print( 'configure_rotor: could not load module: ' + module_path + '  exiting.',
                   file=sys.stderr,flush=True)
            sys.exit(1)

        # FIXME: check for unreasonable numbers below

        try: 
            name = config.get('rotor','name')
        except:
            print( 'configure_rotor: No rotor name given, will set to "noname".', file=sys.stderr,flush=True)
            name = 'noname'

        # rotor elevation offset
        try: 
            el_offset = config.getfloat('rotor','el_offset')
        except: 
            print( 'configure_rotor: rotor elevation not given, setting to el_offset=0.0',
                   file=sys.stderr,flush=True)
            el_offset = 0.0

        # rotor azimuth offset
        try: 
            az_offset = config.getfloat('rotor','az_offset')
        except: 
            print( 'configure_rotor: rotor azimuth offset not given, setting to az_offset=0.0', file=sys.stderr, flush=True)
            az_offset = 0.0

        # rotor command lead time
        try: 
            lead = config.getfloat('rotor','lead')
        except: 
            print( 'configure_rotor: rotor lead time not given, setting to  lead=1.0',file=sys.stderr,flush=True)
            lead = 1.0

        # instantiate the rotor class with above attribute values
        try:
            self.rotor = module.instantiate( name, el_offset, az_offset, lead )
        except:
            print( 'configure_rotor: could not instantiate rotor module, exiting.', file=sys.stderr,flush=True )
            sys.exit(1)

    # write offsets to configuration file
    def write_offsets( self ):

        # FIXME: write out to backup file

        # start configuration 
        config = configparser.RawConfigParser()        
        config.read( self.config_file )

        config.has_section( 'rotor' )
        try: 
            config.set( 'rotor', 'lead', str( self.rotor.lead ))
        except: 
            print('cannot write lead to parser',
                  file=sys.stderr,flush=True)

        try: 
            config.set( 'rotor', 'az_offset', str( self.rotor.az_offset ))
        except: 
            print('cannot write az offset to parser',
                  file=sys.stderr,flush=True)

        try: 
            config.set( 'rotor', 'el_offset', str( self.rotor.el_offset ))
        except: 
            print('cannot write el offset to parser',
                  file=sys.stderr,flush=True)

        try: 
            file = open( self.config_file, 'w' )
        except: 
            print('cannot open configuration file: ', 
                  self.config_file,file=sys.stderr,flush=True)

        try:
            config.write( file )  
        except: 
            print('cannot write configuration file: ', 
                  self.config_file)

    def print_offsets( self ):
        print('current offsets: lead,az,el: ', 
              self.rotor.lead,      
              self.rotor.az_offset, 
              self.rotor.el_offset)
        
    # main loop 
    def start( self ):

        print('spawning suntracker thread')

        # spawn a thread to track the sun
        tracker = suntracker( self.lat, self.lon, self.alt, self.rotor )
        tracker.start()

        print('adjust offsets with type and value.')
        print('eg. to adjust lead time: l 0.5')
        print('eg. to adjust azimuth offset: a 5.0')
        print('eg. to adjust elevation offset: e 1.0')
        print('to save values use: s')
        print('exit with "q" and return')

        self.print_offsets()

        while True:

            # check for user input
            string = input()
            if len(string) == 0:
                print('>,')
                continue

            if string[0] == 'l':
                try:
                    self.rotor.lead = float( string[1:] )
                    self.print_offsets()
                except: 
                    print('bad number given, try again.', string)

            if string[0] == 'a':
                try:
                    self.rotor.az_offset = float( string[1:] )
                    self.print_offsets()
                except: 
                    print('bad number given, try again.', string)

            if string[0] == 'e':
                try:
                    self.rotor.el_offset = float( string[1:] )
                    self.print_offsets()
                except: 
                    print('bad number given, try again.', string)

            if string == 's':          # set the values
                try:
                    self.write_offsets()
                    print('values have been written to ' + self.config_file)
                except: print('cannot write to file.')

            if string == 'q':          # quit program
                print('please wait...')
                tracker.stop()
                tracker.join()
                print('done')
                break
	    
if __name__ == '__main__':                    # user entry point  

    if len( sys.argv ) > 1:                   # check for configuration file
        config_file = sys.argv[1]
    else:
        print('suntrack: config file: not given, exiting...', file=sys.stderr)
        print('usage: ./suntrack.py configure_file', file=sys.stderr)
        sys.exit(1)

 
    if not os.path.isfile( config_file ):
        print('suntrack: config file: ' +  config_file + ' does not exist', file=sys.stderr)
        print('exiting...', file=sys.stderr)
        sys.exit(1)

    try:
        suntrack = suntrack( config_file )
    except:
        print('suntrack.py: configuration file given: '  + config_file + ' does not load.', file=sys.stdout)
        print('exiting...', file=sys.stderr)
        sys.exit(1)

    suntrack.start()

# end suntrack.py
