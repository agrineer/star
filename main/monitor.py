'''
@file monitor.py
@author Scott L. Williams
@package STaR
@brief Antenna monitor position thread.
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
Monitors antenna position on a separate thread.
'''

monitor_copyright = 'monitor.py Copyright (c) 2020 Scott L. Williams ' + \
            'released under GNU GPL V3.0'

#  provide monitor thread for star

import wx
import os
import sys
import time
import ephem
from threading import Thread

# monitor antenna position on a separate thread
class monitor( Thread ):
    def __init__ ( self, stargui, log_file ):
        Thread.__init__( self )
        self.running = False
        self.active = True                      # used to suspend monitoring  

        self.stargui = stargui
        
        self.log_file = log_file
        self.last_modified = 0
        self.num_messages = 0

    def report_messages( self ):
        try:
          file = open( self.log_file, 'r' )      # open for read
          for i in range( self.num_messages ):   # step to valid message
              file.readline()

          line = file.readline()                      
          while line:
              self.num_messages += 1
              wx.CallAfter( self.stargui.benchtop.update_messages, '  ' + line )
              line = file.readline()
        except:
            print( 'report_messages: log file i/o error',
                   file=sys.stderr, flush=True)

    def report_status( self ):
        tracking = self.stargui.star.sched.tracking
        if tracking == True:         # is antenna tracking?
            status = ' tracking'     # fill in status 
            label  = ' elapsed '
        else:
            status = 'waiting for'
            label  = 'arrives in '
  
        # FIXME: how to right align status text
        # FIXME: how to color text in status bar?
        wx.CallAfter( self.stargui.mstatus.SetStatusText, status, 2 )
        wx.CallAfter( self.stargui.mstatus.SetStatusText, label, 5 )
      
        # update rotor position to path_panel
        wx.CallAfter( self.stargui.benchtop.path_panel.update_pos )
          
        # update next pass countdown
        arrives = self.stargui.benchtop.next_pass
        if arrives != None:
            arrives = ephem.localtime( arrives )
            now = ephem.localtime(ephem.now())

            if tracking == True:
                diff = now-arrives
            else:
                diff = arrives-now

            # FIXME: format diff value
            wx.CallAfter( self.stargui.mstatus.SetStatusText, str(diff)[:7], 6 )

    def stop( self ):
        self.running = False

    def enable( self, option ):  # workaround since stop/restart doesn't exist
        self.active = option     # FIXME: check for boolean

    def run ( self ):
        self.running = True
        while self.running:
            if self.active == True:
                self.report_status()    # report rotor status

                # check if pass list needs to be updated
                if self.stargui.star.update_passlist == True:
                    wx.CallAfter( self.stargui.benchtop.update_passlist )
            
                # check if log messages need to be updated
                time_modified = os.stat(self.log_file).st_mtime
                if time_modified > self.last_modified:
                    self.report_messages()
                    self.last_modified = time_modified

            time.sleep( 2.0 )           # refresh every 2 seconds.
                                        # reports are not actually
                                        # 2 secs, probably has to
                                        # to do with "CallAfter" timing.

# end monitor.py
