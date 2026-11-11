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

from importlib.util import spec_from_file_location, module_from_spec

# our imports
from scheduler import scheduler

# ground station attribute
class station():
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
        self.myname = None
        self.sats = None

    def report_error( self, e, message ):        
        eprint( self.myname + str(e) )
        logging.error( e )

        eprint( self.myname + message )
        logging.error( message )
        sys.exit( 1 )

    def report_warning( self, message ):
        eprint( self.myname + message )
        logging.error( message )
        sys.exit( 1 )

    def try_loading( self, name, path ):

        # fancier path joining
        mpath = os.path.join(path, f'{name}.py')

        logging.info( 'locating rotor module file: ' + mpath )
        spec = spec_from_file_location( name, mpath ) # does this throw an exception?
        if spec != None:
 
            try:
                module = module_from_spec( spec )
                spec.loader.exec_module( module )
            except Exception as e:
                eprint( self.myname + e )
                logging.error( e )
                
                message = 'could not load module: ' + name + ' ... exiting'
                eprint( self.myname + message )
                logging.error( message )
                
                sys.exit( 2 )
                
            logging.info( 'dynamically loaded module: ' + name )
            return module
        
        else:
            message = 'could not find rotor module: ' + name + ' ... exiting'
            logging.error( message )
            eprint( self.myname + message )
            sys.exit( 2 )

    # rotor lead time
    def get_rotor_lead( self, config ):

        try:
            logging.info( 'getting rotor response lead time ... ' )
            lead = config.getfloat('rotor','lead')

        except:
            message = 'rotor lead time not given, setting to lead = 1.0'
            self.report_warning( message )
            lead = 1.0
            
        logging.info( 'using rotor response time lead = ' + str( lead ) )

        return lead
        
    # rotor azimuth offset
    def get_rotor_azimuth_offset( self, config ):

        try:
            logging.info( 'getting rotor azimuth offset ... ')
            az_offset = config.getfloat('rotor','az_offset')
            
            if az_offset < 0:
                # TODO: really true?
                message = 'rotor azimuth offset cannot be < 0, given: ' + \
                          str( az_offset ) + ' setting az_offset = 0.0'
                self.report_warning( message )
                az_offset = 0.0

            if az_offset > 10.0:
                message = 'rotor azimuth offset is set high, given: ' + \
                          str( az_offset ) + ' ... continuing'
                self.report_warning( message )

            logging.info( 'using rotor azimuth offset = ' + str( az_offset ) )
            
        except:
            message = 'rotor azimuth offset not given, setting to az_offset = 0.0'
            eprint( self.myname + message )
            logging.warning( message )
            az_offset = 0.0

        return( az_offset )

    # rotor elevation offset
    def get_rotor_elevation_offset( self, config ):
        
        try:
            logging.info( 'getting rotor elevation offset ... ' )
            el_offset = config.getfloat('rotor','el_offset')
            if el_offset < 0:
                
                # TODO: really true?
                message = 'rotor elevation offset cannot be < 0, given: ' + \
                          str(el_offset) + ' setting el_offset = 0.0'
                self.report_warning( message )
                el_offset = 0.0
            
            if el_offset > 10.0:
                message = 'rotor elevation offset is set high, given: ' + \
                          str(el_offset) + ' ... continuing'
                self.report_warning( message )

            logging.info( 'using rotor elevation offset = ' + str( el_offset ) )
 
        except:
            message = 'rotor elevation offset not given, setting to el_offset = 0.0'
            self.report_warning( message )
            el_offset = 0.0
            
        return el_offset
    
    # dynamically load rotor module
    def configure_rotor( self, config_file ):

        logging.info( 'configuring rotor using file: ' + config_file  )
        
        try:
            config = configparser.RawConfigParser()
            config.read( config_file )  

        except Exception as e:
            message = 'could not open rotor configure file: ' + config_file
            self.report_error( e, message )
         
        try:
            logging.info( 'getting rotor module path ... ' )
            module_path = config.get('rotor','module')
            logging.info( 'using module_path: ' + module_path  )
            name = os.path.basename( module_path )
            
        except Exception as e:
            message = 'could not read rotor module path: ' + \
                       module_path + ' ... exiting.'
            self.report_error( e, message )

        name = os.path.basename( module_path )
        logging.info( 'loading rotor module: ' + module_path )
        
        module = self.try_loading( 'dummy', module_path )
        logging.info( 'using rotor module: ' + module_path  )

        # FIXME: check for unreasonable numbers below

        el_offset = self.get_rotor_elevation_offset( config )
        az_offset = self.get_rotor_azimuth_offset( config )
        lead = self.get_rotor_lead( config )
                          
        # instantiate the rotor class with above attribute values
        try:
            self.rotor = module.instantiate( name, el_offset, az_offset, lead )
            
        except Exception as e:
            message( 'could not instantiate rotor module: ' + name + ' ... exiting' )
            self.report_error( e, message )

    # read elevation to start and stop reading signal
    def get_read_elevation( self, config ):
              
        try:
            logging.info( 'getting start read elevation ... ' )
            self.sig_elev = config.getfloat( 'satellites', 'sig_elev' )
            if self.sig_elev < 0:
                message = 'start read elevation cannot be < 0, given: ' + \
                          str( self.sig_elev ) + ' setting sig_elev = 15.0'
                self.report_warning( message )
                self.sig_elev = 15.0
                          
        except:
            message = 'no read start signal elevation given, setting sig_elev = 15.0'
            eprint( self.myname + message )
            logging.warning( message )
            self.sig_elev = 15.0
                          
        logging.info( 'using start signal_elevation = ' + str( self.sig_elev ) )

    # read minimum zenith threshold for satellite passes
    def get_minimum_zenith( self, config ):
                
        try:
            logging.info( 'getting minimum zenith threshold ... ' )
            self.zenith_min = config.getfloat( 'satellites', 'zenith_min' )
            if self.sig_elev < 0:
                message = 'minimum elevation cannot be < 0, given: ' + \
                           str( self.zenith_min ) + ' setting zenith_min = 25.0'
                self.report_warning( message )
                self.zenith_min = 25.0
                          
        except:
            message = 'no zenith minimum given, setting zenith_min=25.0'
            self.report_warning( message )
            self.zenith_min = 25.0
            
        logging.info( 'using zenith minimum = ' + str( self.zenith_min ) )

    # read number of passes to predict per satellite
    def get_number_passes( self, config ):
        
        try:
            logging.info( 'getting number of passes per satellite ...' )
            self.num_passes = int(config.getfloat('satellites','num_passes')) # ??
            
        except:
            message = 'no number of passes given, setting num_passes=3'
            eprint( self.myname + message )
            logging.warning( message )
            self.num_passes = 3

        logging.info( 'using number of passes per satellite = ' + str( self.num_passes ) )

    # read list of active satellites
    def get_active_satellites( self, config ):
           
        try:
            logging.info( 'getting active satellites ... ' )
            slist = config.get( 'satellites', 'active' )
            active = slist.split( ',' )

        except Exception as e:
            message = 'could not read active satellites ...  exiting.'
            self.report_error( e, message )
            
        logging.info( 'active satellites: ' + str( slist ) )

        return active

    # get the two line element file to read from
    def get_tle( self, index, active, config ):

        try:
            logging.info( ' ' )
            logging.info( 'getting TLE filename for satellite: ' +
                          self.sats[index].name + ' ... ' )
            
            self.sats[index].tlef = config.get( active[index], 'tle_file' )
                
        except Exception as e:
            message = 'satellite TLE file not given ... exiting.'
            self.report_error( e, message )
            
        logging.info( 'using TLE file: ' + self.sats[index].tlef +
                      ' for satellite: ' + self.sats[index].name )
                          
    # make satellite class array and fill in attributes
    def populate_satellites( self, active, config ):
        
        logging.info( 'populating active satellite attributes ... ')
        self.sats = []
        
        for i in range( len( active ) ):

            self.sats.append( sat() )
            self.sats[i].name = active[i]   

            self.get_tle( i, active, config )
            
            try:
                logging.info( 'getting acquistion read signal script filename ... ' )
                self.sats[i].read = config.get( active[i],'read_script' )
                
            except Exception as e:
                message = 'no acquisition signal read script filename given for satellite: ' + \
                          active[i] + ' ... exiting.'
                self.report_error( e, message )
                
            logging.info( 'using aquisition signal read script file: ' + self.sats[i].read )
            
            try:
                logging.info( 'getting post acquistion processing script ... ' )
                self.sats[i].proc = config.get( active[i], 'proc_script' )
                
            except Exception as e:
                message = 'no post acquisition processing script filename given for satellite: ' + \
                          active[i] + ' ... exiting.'
                self.report_error( e, message )
                
            logging.info( 'using post acquisition processing script: ' + self.sats[i].proc  )
            
        logging.info( ' ' )

    # get ground station attributes
    def get_station_attributes( self, config ):
        
        self.station = station()
        
        try:
            logging.info( 'getting ground station name ... ' )
            self.station.name = config.get( 'station', 'name' )
            
        except Exception as e:
            message = 'ground station name not given ... exiting'
            self.report_error( e, message )
            
        logging.info( 'using ground station name: ' + self.station.name )

        try:
            logging.info( 'getting ground station latitude ... ' )
            self.station.lat = config.get( 'station', 'latitude' )
            
        except Exception as e:
            message = 'ground station latitude not given ... exiting'
            self.report_error( e, message )
            
        logging.info( 'using ground station latitude = ' +  self.station.lat )      

        try:
            logging.info( 'getting ground station longtitude ... ' )
            self.station.lon = config.get( 'station', 'longitude' )

        except Exception as e:
            message = 'ground station latitude not given ... exiting'
            self.report_error( e, message )
            
        logging.info( 'using ground station longitude = ' +  self.station.lon )

        try:
            logging.info( 'getting station altitude ... ' )
            self.station.alt = config.getfloat( 'station', 'altitude' )
            
        except Exception as e:
            message = 'ground station altitude not given ... exiting'
            self.report_error( e, message )
            
        logging.info( 'using ground station altitude = ' +  str( self.station.alt ) )
        logging.info( ' ' )
        
    def configure( self, config_file ):

        logging.info( 'configuring star using file: ' + config_file )

        try:
            config = configparser.RawConfigParser()
            config.read( config_file )  

        except Exception as e:
            message = 'could not read file: ' + config_file + ' ... exiting.'
            self.report_error( e, message )

        self.get_read_elevation( config )
        self.get_minimum_zenith( config )
        self.get_number_passes( config )
        
        active = self.get_active_satellites( config )

        self.populate_satellites( active, config )

        self.get_station_attributes( config )
        
        self.configure_rotor( config_file )
        self.rotor.park()
        
    def start( self ):

        self.myname = os.path.basename(__file__)[:-3] + ': ' # no need for .py suffix
        
        # declare versions
        logging.info( 'python version = ' + sys.version[0:6] )
        
        # spawn a thread to schedule AOS, LOS and rotor events
        self.sched = scheduler( self )
        self.sched.start()

######################################################################

if __name__ == '__main__':   # user entry point  

    # FIXME: put help option, arg flags

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

    star = star() # instantiate non-graphics worker bee 
    
    try:
        logging.info( 'configuring with ' + config_file )
        star.configure( config_file )

    except Exception as e:
        message = 'check log file "star.log" for details.'
        eprint( 'star.py: ERROR: ' + message )
        logging.error( message )

        message = 'star.py: configuration file given: ' + config_file + \
                  ' does not load ... exiting'

        eprint( 'star.py: ERROR: ' + message )
        star.report_error( message )
 
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
