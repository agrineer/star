'''
@file suntracker.py
@author Scott L. Williams
@package STaR
@brief Class to track the sun.
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
Class to track the sun for alignment purposes. Used by the suntrack.py program.
'''
# embed copyright in binary
suntracker_copyright = 'suntracker.py Copyright (c) 2020 Scott L. Williams ' + \
                 'released under GNU GPL V3.0'

import os
import math
import time
import ephem

from threading import Thread

# satellite tracker thread
class suntracker( Thread ):
    def __init__ ( self, lat, lon, alt, rotor ):
        Thread.__init__( self )

        self.lat = lat
        self.lon = lon
        self.alt = alt

        self.rotor = rotor           # antenna control
        self.running = False

    def stop( self ):
        self.running = False

    def run ( self ):
        self.running = True

        obs = ephem.Observer()
        obs.lat = self.lat
        obs.lon = self.lon
        obs.elevation = self.alt     # OJO: swapped alt and elevation
        obs.pressure = 0

        sun = ephem.Sun()

        # go to start position
        obs.date = ephem.now() + self.rotor.lead*ephem.second
        sun.compute( obs )
        sun_az = math.degrees(sun.az)
        sun_el = math.degrees(sun.alt)
        last_az = '%5.1f'%sun_az
        last_el = '%5.1f'%sun_el

        print('moving to: ' + last_az + ' ' + last_el)
        self.rotor.move_azel( sun_az, sun_el )

        while self.running:

            obs.date = ephem.now() + self.rotor.lead*ephem.second
            sun.compute( obs )
            sun_az = math.degrees( sun.az )
            sun_el = math.degrees( sun.alt )
            az = '%5.1f'%sun_az
            el = '%5.1f'%sun_el
            if (az != last_az) or (el != last_el): 
                last_az = az
                last_el = el
                print('moving to: ' + last_az + ' ' + last_el)
                self.rotor.move_azel( sun_az, sun_el )
                
            time.sleep(1)

        self.rotor.park()
        self.running = False

# end suntracker.py
