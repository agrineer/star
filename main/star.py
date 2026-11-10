#!/usr/bin/env python3
'''
@file star.py
@author Scott L. Williams
@package STaR
@brief Command line core STaR program.
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
Satellite Track and Read (STaR) program using a modular antenna motion 
control and signal reception approach.
'''

star_copyright = 'star.py Copyright (c) 2020-2026 Scott L. Williams, released under GNU GPL V3.0'

import os
import sys
import time 
import logging

import configparser
from ezprint import eprint, eprints
from threading import Thread
#from load_module import load_module
from importlib.util import spec_from_file_location, module_from_spec

# our imports
from scheduler import scheduler

# ground station location
class loc():
    def __init__(self): 
        self.name= None        # station name
        self.lat = None        # latitude
        self.lon = None        # longitude
        self.alt = None        # altitude

# satellite properties
class sat():
    def __init__(self): 
        self.name = None       # satellite name as given in TLEs
        self.tlef = None       # TLE file
        self.tle1 = None       # keplerian two line elements
        self.tle2 = None
        self.read = None       # read script
        self.proc = None       # process script

# sets up satellite scheduler which triggers 
# externals scripts and rotor tracking
class star():  
    def __init__( self ):
        self.update_passlist = True
        self.rotor = None
        self.sig_elev = None
        self.zenith_min = None
        self.num_passes = None
        self.sats = None
        self.loc = None
        self.sched = None

    def try_loading( self, name, path ):

        # fancier path joining
        mpath = os.path.join(path, f'{name}.py')
        
        spec = spec_from_file_location( name, mpath )
        if spec != None:

            # If a spec was found but the file is invalid,
            # let exceptions propagate
            module = module_from_spec( spec )

            try:
                spec.loader.exec_module( module )
            except Exception as e:
                eprint( e )
                eprint( 'could not load module: ' + name + ' .. exiting' )
                sys.exit( 2 )
                
            eprint( 'dynamically loaded module: ' + name )
            return module
        
        raise ModuleNotFoundError

    # dynamically load rotor module
    def configure_rotor( self, config_file ):
        
        config = configparser.RawConfigParser()
        config.read( config_file )  

        try:
            eprints( 'getting rotor module path ... ' )
            module_path = config.get('rotor','module')
            eprint( module_path )
        except:
            logging.error( 'configure_rotor: could not read module path, exiting.' )
            sys.exit(1)
        try:
            eprint( 'loading rotor module' + module_path )
            #module = load_module( module_path )
            module = self.try_loading( 'dummy', module_path )
        except:
            eprint( 'could not load module: ' + module_path )
            logging.error( 'configure_rotor: could not load module: ' + 
                           module_path + '  exiting.' )
            sys.exit(1)

        # FIXME: check for unreasonable numbers below

        try:
            eprints( 'getting module name ... ' )
            name = config.get('rotor','name')
            eprint( name )
        except:
            logging.warning( 'configure_rotor: No rotor name given, will set to "noname".')
            name = 'noname'

        # rotor elevation offset
        try:
            eprints( 'getting elevation offset ... ' )
            el_offset = config.getfloat('rotor','el_offset')
            eprint( el_offset )
        except: 
            logging.warning( 'configure_rotor: rotor elevation not given, setting to el_offset=0.0')
            el_offset = 0.0

        # rotor azimuth offset
        try:
            eprints( 'getting azimuth offset ... ')
            az_offset = config.getfloat('rotor','az_offset')
            eprint( az_offset )
        except: 
            logging.warning( 'configure_rotor: rotor azimuth offset not given, setting to az_offset=0.0')
            az_offset = 0.0

        # rotor command lead time
        try:
            eprints( 'getting response lead time ... ' )
            lead = config.getfloat('rotor','lead')
            eprint( lead )
        except: 
            logging.warning( 'configure_rotor: rotor lead time not given, setting to  lead=1.0')
            lead = 1.0

        # instantiate the rotor class with above attribute values
        try:
            module = self.try_loading( name, module_path )
            self.rotor = module.instantiate( name, el_offset, az_offset, lead )
            
        except Exception as e:
            logging.error( e )
            logging.error( 'configure_rotor: could not instantiate rotor module, exiting.' )
            sys.exit(1)

    def configure( self, config_file ):

        # start configuration 
        config = configparser.RawConfigParser()
        config.read( config_file )

        # FIXME: check for negative, unreasonable values (validate)

        # read elevation to start and stop reading signal
        try:
            eprints( 'getting start read elev ... ' )
            self.sig_elev = config.getfloat('satellites','sig_elev')
            eprint( self.sig_elev )
        except: 
            logging.warning('No signal elevation given, setting sig_elev=15.0' )
            self.sig_elev = 15.0

        # read minimum zenith threshold for satellite passes
        try:
            eprints( 'getting minimum zenith threshold ... ' )
            self.zenith_min = config.getfloat('satellites','zenith_min')
            eprint( self.zenith_min )
        except: 
            logging.warning('No zenith minimum given, setting zenith_min=25.0' )
            self.zenith_min = 25.0

        # read number of passes to predict per satellite
        try:
            eprints( 'getting number of passes per satellite ...' )
            self.num_passes = int(config.getfloat('satellites','num_passes'))
            eprint( self.num_passes )
        except: 
            logging.warning( 'No number of passes given, setting num_passes=3' )
            self.num_passes = 3

        # read active satellites
        try:
            eprints( 'getting active satellites ... ' )
            list = config.get('satellites','active')
            active = list.split(',')
            eprint( active )
        except: 
            logging.warning( 'No active satellites give, exiting' )
            sys.exit(1)

        # make satellite list and fill in attributes
        self.sats = []
        for i in range(0,len(active)):

            self.sats.append( sat() )
            self.sats[i].name = active[i]   

            # get the two line element file to read from
            try:
                self.sats[i].tlef = config.get( active[i],'tle_file')
            except:
                logging.error( 'Satellite TLE file not given, exiting' )
                sys.exit(1)

            # get signal read script
            try:
                self.sats[i].read = config.get( active[i],'read_script')
            except:
                logging.warning('No read script given for satellite '+active[i])
                logging.warning('Satellite will be tracked but not read.')

            # get signal processing script
            try:
                self.sats[i].proc = config.get( active[i],'proc_script')
            except:
                logging.warning('No processing script given for satellite ' + active[i])
                logging.warning('Satellite signal will not be processed.')

        # get ground station location
        self.loc = loc()
        
        eprints( 'getting location name ... ' )
        self.loc.name = config.get('location','name')
        eprint( self.loc.name )

        eprints( 'getting location latitude ... ' )
        self.loc.lat = config.get('location','latitude')
        eprint( self.loc.lat )

        eprints( 'getting location longtitude ... ' )
        self.loc.lon = config.get('location','longitude')
        eprint( self.loc.lon )

        eprints( 'getting location altitude ... ' )
        self.loc.alt = config.getfloat('location','altitude')
        eprint( self.loc.alt )
        
        self.configure_rotor( config_file )
        self.rotor.park()
        
    def start( self ):

        # report location
        names = 'station: ' + self.loc.name +           \
                '     antenna: ' + self.rotor.name

        logging.info( names )
        
        location = 'location:  lat=' + '%8.4f'%float(self.loc.lat) + \
                   ' lon=' + '%8.4f'%float(self.loc.lon) + \
                   ' alt=' + '%6.1f'%self.loc.alt 

        logging.info( location )

        # report active satellites
        active = 'active satellites: '
        for i in range( len(self.sats) ):
            active += self.sats[i].name + ', '

        logging.info( active[:-2] )     # removes last ', '

        # report signal elevations
        signal_elevs ='signal elevations:' + \
                      ' zenith min = ' + '%5.1f'%self.zenith_min + \
                      ', signal elev =' + '%5.1f'%self.sig_elev
        
        logging.info( signal_elevs )
        
        # spawn a thread to schedule AOS, LOS and rotor events
        self.sched = scheduler( self )
        self.sched.start()

######################################################################         
if __name__ == '__main__':   # user entry point  

    # FIXME: put help option

    # use configuration file as argument
    if len( sys.argv ) > 1:  # check for configuration file
        config_file = sys.argv[1]

        # check if file exists; exit if not
        if not os.path.isfile( config_file ) :
            eprint('star: config file: ' +  config_file + ' does not exist' )
            sys.exit(1)
    else:
        eprint('no config file given.')
        eprint('usage:star.py config_file [log_file]' )
        sys.exit(1)

    if len( sys.argv ) > 2:  # check for log file
        log_file = sys.argv[2]
    else:
        log_file = 'star.log'

    # start log file
    logging.basicConfig( filename=log_file, 
                         filemode='w',
                         format='%(asctime)s %(message)s', 
                         datefmt='%Y-%m-%d %H:%M:%S -',
                         level=logging.DEBUG )

    logging.info( 'starting star command line version 2026.000' )
    logging.info( 'configuration file: ' + config_file )

    star = star()
    try:
        eprint( 'configuring with' + config_file )
        star.configure( config_file )
        eprint( "CONFIGURED" )
    except Exception as e:
        eprint( e )
        err = 'star.py: configuration file given: ' + config_file +\
              ' does not load. exiting program.'

        logging.error( err )
        eprint( err )
        eprint('check log file "star.log" for details.' )
        sys.exit(1)

    eprint( 'Starting star' )
    star.start()

    # main loop     
    eprint( 'exit with "q" and return' )
    while True:

        # check for user input
        c = input()
        if c == 'q':
            star.sched.stop()
            star.sched.join()
            break
        
# end star.py
