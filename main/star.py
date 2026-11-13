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
from threading import Thread
from ezprint import eprint, eprints

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
    
    def __init__( self, log_file, config_file ):
        
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

        # setup the logger
        self.logger = self.setup_logger( 'star_logger', log_file, False )

        self.logger.info( 'star: using log file: ' + log_file )
        self.logger.info( 'star: initializing star version: 2026.000' )
        self.logger.info( 'star: python version = ' + sys.version[0:6] )

        self.myname = os.path.basename(__file__)[:-3] + ': ' 
        self.configure( config_file )
        
    def setup_logger( self, logger_name, log_file, console ):

        # clobber the old file
        if os.path.exists( log_file):
            os.remove( log_file )

        logger = logging.getLogger( logger_name )
        logger.setLevel( logging.DEBUG )
        formatter = logging.Formatter(
            # uncomment below to get line number
            #fmt="%(asctime)s - %(levelname)s - %(lineno)d - %(message)s",
            fmt="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S" )
        #formatter = logging.Formatter( '%(asctime)s - %(levelname)s - %(message)s' )
        
        # create file handler
        fh = logging.FileHandler( log_file )
        fh.setLevel( logging.DEBUG )
        fh.setFormatter( formatter )
        logger.addHandler( fh )
        
        if console:
            
            # create console handler
            ch = logging.StreamHandler()
            ch.setLevel( logging.DEBUG )
            ch.setFormatter( formatter )
            logger.addHandler( ch )
    
        return logger

    def report_error( self, e, message ):        
        eprint( self.myname + str(e) )
        self.logger.error( e )

        eprint( self.myname + message )
        self.logger.error( message )
        sys.exit( 1 )

    def report_warning( self, message ):
        eprint( self.myname + message )
        self.logger.error( message )
        sys.exit( 1 )

    def try_loading( self, name, path ):

        # fancier path joining
        mpath = os.path.join(path, f'{name}.py')

        #self.logger.info( 'star: locating rotor module file: ' + mpath )
        spec = spec_from_file_location( name, mpath ) # does this throw an exception?
        if spec != None:
 
            try:
                module = module_from_spec( spec )
                spec.loader.exec_module( module )
            except Exception as e:
                eprint( self.myname + e )
                self.logger.error( e )
                
                message = 'star: could not load module: ' + name + \
                          ' ... exiting'
                eprint( self.myname + message )
                self.logger.error( message )
                
                sys.exit( 2 )
                
            self.logger.info( 'star: dynamically loaded rotor module: ' + name )
            return module
        
        else:
            message = 'star: could not find rotor module: ' + name + ' ... exiting'
            self.logger.error( message )
            eprint( self.myname + message )
            sys.exit( 2 )

    # rotor lead time
    def get_rotor_lead( self, config ):

        try:
            #self.logger.info( 'star: getting rotor response lead time ... ' )
            lead = config.getfloat('rotor','lead')

        except:
            message = 'star: rotor lead time not given, setting to lead = 1.0'
            self.report_warning( message )
            lead = 1.0
            
        self.logger.info( 'star: using rotor response time lead = ' +
                          str( lead ) )
        self.logger.info( ' ' )
        return lead
        
    # rotor azimuth offset
    def get_rotor_azimuth_offset( self, config ):

        try:
            #self.logger.info( 'star: getting rotor azimuth offset ... ')
            az_offset = config.getfloat('rotor','az_offset')
            
            if az_offset < 0:
                # TODO: really true?
                message ='star: rotor azimuth offset cannot be < 0, given: ' + \
                          str( az_offset ) + ' setting az_offset = 0.0'
                self.report_warning( message )
                az_offset = 0.0

            if az_offset > 10.0:
                message = 'star: rotor azimuth offset is set high, given: ' + \
                          str( az_offset ) + ' ... continuing'
                self.report_warning( message )

            self.logger.info( 'star: using rotor azimuth offset = ' +
                              str( az_offset ) )
            
        except:
            message = 'star: rotor azimuth offset not given, setting to az_offset = 0.0'
            eprint( self.myname + message )
            self.logger.warning( message )
            az_offset = 0.0

        return( az_offset )

    # rotor elevation offset
    def get_rotor_elevation_offset( self, config ):
        
        try:
            #self.logger.info( 'star: getting rotor elevation offset ... ' )
            el_offset = config.getfloat('rotor','el_offset')
            if el_offset < 0:
                
                # TODO: really true?
                message = 'star: rotor elevation offset cannot be < 0, given: ' + \
                          str(el_offset) + ' setting el_offset = 0.0'
                self.report_warning( message )
                el_offset = 0.0
          
            if el_offset > 10.0:
                message = 'star: rotor elevation offset is set high, given: ' + \
                          str(el_offset) + ' ... continuing'
                self.report_warning( message )

            self.logger.info( 'star: using rotor elevation offset = ' + \
                              str( el_offset ) )
 
        except:
            message = 'star: rotor elevation offset not given, setting to el_offset = 0.0'
            self.report_warning( message )
            el_offset = 0.0
            
        return el_offset
    
    # dynamically load rotor module
    def configure_rotor( self, config_file ):

        self.logger.info( 'star: configuring rotor using file: ' +
                          config_file  )
        
        try:
            config = configparser.RawConfigParser()
            config.read( config_file )  

        except Exception as e:
            message = 'star: could not open rotor configure file: ' + \
                       config_file
            self.report_error( e, message )
         
        try:
            #self.logger.info( 'star: getting rotor module path ... ' )
            get = config.get( 'rotor','module' )
            module_path = os.path.expandvars( get )

            # file path check
            #self.logger.info( 'star: checking if file: ' + module_path + ' exists ... ' )
            if not os.path.exists( module_path ):
                message = 'star: rotor module file does not exist ... exiting'
                eprint( 'ERROR: ' + message )
                self.report_info( ' ', message )
                            
        except Exception as e:
            message = 'star: could not read rotor module path: ' + \
                       module_path + ' ... exiting.'
            self.report_error( e, message )

        self.logger.info( 'star: using module_path: ' + module_path  )

        name = os.path.basename( module_path )
        #self.logger.info( 'star: loading rotor module: ' + module_path )
        
        module = self.try_loading( 'dummy', module_path )
        self.logger.info( 'star: using rotor module: ' + module_path  )

        el_offset = self.get_rotor_elevation_offset( config )
        az_offset = self.get_rotor_azimuth_offset( config )
        lead = self.get_rotor_lead( config )
                          
        # instantiate the rotor class with above attribute values
        try:
            self.rotor = module.instantiate( name, el_offset, az_offset, lead )

        except Exception as e:
            message( 'could not instantiate rotor module: ' +
                     name + ' ... exiting' )
            self.report_error( e, message )

    # read elevation to start and stop reading signal
    def get_read_elevation( self, config ):
              
        try:
            #self.logger.info( 'star: getting start read elevation ... ' )
            self.sig_elev = config.getfloat( 'satellites', 'sig_elev' )
            if self.sig_elev < 0:
                message = 'start read elevation cannot be < 0, given: ' + \
                          str( self.sig_elev ) + ' setting sig_elev = 15.0'
                self.report_warning( message )
                self.sig_elev = 15.0
                          
        except:
            message = 'star: no read start signal elevation given, setting sig_elev = 15.0'
            eprint( self.myname + message )
            self.logger.warning( message )
            self.sig_elev = 15.0
                          
        self.logger.info( 'star: using start signal_elevation = ' +
                          str( self.sig_elev ) )

    # read minimum zenith threshold for satellite passes
    def get_minimum_zenith( self, config ):
                
        try:
            #self.logger.info( 'star: getting minimum zenith threshold ... ' )
            self.zenith_min = config.getfloat( 'satellites', 'zenith_min' )
            if self.sig_elev < 0:
                message = 'star: minimum elevation cannot be < 0, given: ' + \
                           str( self.zenith_min ) + ' setting zenith_min = 25.0'
                self.report_warning( message )
                self.zenith_min = 25.0
                          
        except:
            message = 'star: no zenith minimum given, setting zenith_min=25.0'
            self.report_warning( message )
            self.zenith_min = 25.0
            
        self.logger.info( 'star: using zenith minimum = ' +
                          str( self.zenith_min ) )

    # read number of passes to predict per satellite
    def get_number_passes( self, config ):
        
        try:
            #self.logger.info( 'star: getting number of passes per satellite ...' )
            self.num_passes = int(config.getfloat('satellites','num_passes')) # ??
            
        except:
            message = 'star: no number of passes given, setting num_passes=3'
            eprint( self.myname + message )
            self.logger.warning( message )
            self.num_passes = 3

        self.logger.info( 'star: using number of passes per satellite = ' + str( self.num_passes ) )

    # read list of active satellites
    def get_active_satellites( self, config ):
           
        try:
            #self.logger.info( 'star: getting active satellites ... ' )
            slist = config.get( 'satellites', 'active' )
            active = slist.split( ',' )

        except Exception as e:
            message = 'star: could not read active satellites ... exiting.'
            self.report_error( e, message )
            
        self.logger.info( 'star: active satellites: ' + str( slist ) )

        return active

    # get the two line element file to read from
    def get_tle( self, index, active, config ):

        try:
            self.logger.info( ' ' )
            #self.logger.info( 'star: getting TLE filename for satellite: ' +
            #                  self.sats[index].name + ' ... ' )

            get = config.get( active[index], 'tle_file' )
            self.sats[index].tlef = os.path.expandvars( get )
            
            #self.logger. info( 'star: checking if file: ' + self.sats[index].tlef +
            #                   ' exists ... ' )
            
            if not os.path.exists( self.sats[index].tlef ):
                self.report_error( ' ' +
                                   self.sats[index].tlef +
                                   'star: does not exist ... exiting' )
                
        except Exception as e:
            message = 'star: satellite TLE file not given ... exiting.'
            self.report_error( e, message )
            
        self.logger.info( 'star: using TLE file: ' + self.sats[ index ].tlef +
                     ' for satellite: ' + self.sats[ index ].name )
                          
    # make satellite class array and fill in attributes
    def populate_satellites( self, active, config ):
        
        self.logger.info( 'star: populating active satellite attributes ... ')
        self.sats = []
        
        for i in range( len( active ) ):

            self.sats.append( sat() )
            self.sats[i].name = active[i]   

            self.get_tle( i, active, config )
            
            try:
                #self.logger.info('star: getting acquisition read signal script filename ... ')
                get = config.get( active[i],'read_script' )
                self.sats[i].read = os.path.expandvars( get )
                
            except Exception as e:
                message = 'no acquisition signal read script filename given for satellite: ' + \
                          active[i] + ' ... exiting.'
                self.report_error( e, message )
                
            self.logger.info('star: using aquisition signal read script file: ' +
                              self.sats[i].read )
            
            try:
                #self.logger.info( 'star: getting post acquistion processing script ... ' )
                get = config.get( active[i], 'proc_script' )
                self.sats[i].proc = os.path.expandvars( get )
                
            except Exception as e:
                message = 'star: no post acquisition processing script given for satellite: ' \
                          + active[i]
                eprint( 'ERROR: ' + message )
                self.logger.error( message )
                
                message = 'star: use the "dummy_process" for no post-processing ... exiting'
                self.report_error( e, message )
                
            self.logger.info( 'star: using post acquisition processing script: ' + self.sats[i].proc  )
            
        self.logger.info( ' ' )

    # get ground station attributes
    def get_station_attributes( self, config ):
        
        self.station = station()
        
        try:
            #self.logger.info( 'star: getting ground station name ... ' )
            self.station.name = config.get( 'station', 'name' )
            
        except Exception as e:
            message = 'star: ground station name not given ... exiting'
            self.report_error( e, message )
            
        self.logger.info( 'star: using ground station name: ' +
                          self.station.name )

        try:
            #self.logger.info( 'star: getting ground station latitude ... ' )
            self.station.lat = config.getfloat( 'station', 'latitude' )
            
        except Exception as e:
            message = 'star: ground station latitude not given ... exiting'
            self.report_error( e, message )
            
        self.logger.info( 'star: using ground station latitude = ' +
                      str( self.station.lat ) )
        
        try:
            #self.logger.info( 'star: getting ground station longtitude ... ' )
            self.station.lon = config.getfloat( 'station', 'longitude' )

        except Exception as e:
            message = 'star: ground station latitude not given ... exiting'
            self.report_error( e, message )
            
        self.logger.info( 'star: using ground station longitude = ' +
                           str( self.station.lon) )

        try:
            #self.logger.info( 'star: getting station altitude ... ' )
            self.station.alt = config.getfloat( 'station', 'altitude' )
            
        except Exception as e:
            message = 'star: ground station altitude not given ... exiting'
            self.report_error( e, message )
            
        self.logger.info( 'star: using ground station altitude = ' +
                          str( self.station.alt ) )
        self.logger.info( ' ' )
        
    def configure( self, config_file ):

        self.logger.info( 'star: configuring star using file: ' + config_file )

        try:
            config = configparser.RawConfigParser()
            config.read( config_file )  

        except Exception as e:
            message = 'star: could not read file: ' + config_file + \
                      ' ... exiting.'
            self.report_error( e, message )

        self.get_read_elevation( config )
        self.get_minimum_zenith( config )
        self.get_number_passes( config )

        self.logger.info( ' ' )
        active = self.get_active_satellites( config )

        self.populate_satellites( active, config )
        self.get_station_attributes( config )
        
        self.configure_rotor( config_file )
        self.rotor.park()
        
    def start( self ):

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
            eprint( 'star: config file: ' +  config_file + ' does not exist' )
            sys.exit( 1 )
    else:
        eprint( 'star: no config file given ... exiting.' )
        eprint( 'star: usage:star.py config_file [log_file]' )
        sys.exit( 1 )

    star_home = os.environ[ 'STAR_HOME' ]
    if len( sys.argv ) > 2:  # check for log file
        log_file = star_home + '/log/' + sys.argv[2]
    else:
        log_file = star_home + '/log/' + 'star.log'

    try:
        star = star( log_file, config_file ) # instantiate non-graphics 

    except Exception as e:
        message = 'star: check log file "star.log" for details.'
        eprint( 'ERROR: ' + message )
        star.logger.error( message )

        message = 'star.py: configuration file given: ' + config_file + \
                  ' does not load ... exiting'

        eprint( 'ERROR: ' + message )
        star.report_error( message )
 
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
