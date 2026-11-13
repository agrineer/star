#!/usr/bin/env python3
'''
@file stargui.py
@author Scott L. Williams
@package STaR
@brief GUI interface for the STaR program.
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
A GUI interface for the Satellite Track and Read (STaR) program using a 
modular antenna motion control and signal reception approach.
'''

copyright = 'stargui.py Copyright (c) 2020-2026 Scott L. Williams, released under GNU GPL V3.0'

import os
import wx
import sys
import time
import logging

#from load_module import load_module

# our modules
from star import star
from calib import calib
from ezprint import eprint
from monitor import monitor
from benchtop import benchtop

class stargui( wx.Frame ):    # frame container class for stargui window
    
    def __init__(self, log_file, config_file ):
        
        wx.Frame.__init__( self, None, -1, "" )

        self.mon_thread = None        # monitor thread

        self.logger = logging.getLogger( 'star_logger' )

        # use command line star class
        self.star = star( log_file, config_file ) # instantiate
        self.star.start()

        cfile = os.path.basename( config_file )
        self.SetTitle( "Satellite Track and Read (STaR) - " + cfile )
        self.SetMinSize( (640,480) ) # homage to old school format
        self.SetMaxSize( (640,480) ) 
  
        # FIXME: get some icon and show
        # self.SetIcon( wx.Icon('star.ico', wx.BITMAP_TYPE_ICO))

        self.build_menu()
        self.benchtop = benchtop( self )
                                       
        self.setup_status()    # status bar

    def setup_status( self ):
        self.mstatus = self.CreateStatusBar()
        self.mstatus.SetFieldsCount(7) 

        styles = [ wx.SB_FLAT,
                   wx.SB_FLAT, wx.SB_FLAT,
                   wx.SB_FLAT, wx.SB_FLAT, 
                   wx.SB_FLAT, wx.SB_FLAT ]
        self.mstatus.SetStatusStyles( styles )

        widths = [ 1, 80, 78, 40, 238, 75, 80 ] # KLUDGE: on first width to
                                                # stop overwrite on menu mouse
                                                # hover. 
        self.mstatus.SetStatusWidths( widths )
        
        self.mstatus.SetStatusText( ' antenna is', 1 )
        self.mstatus.SetStatusText( 'pass:', 3 )

    def build_menu( self ):
        menu_bar = wx.MenuBar()     

        # file menu
        file_menu = wx.Menu()   
        '''
        item = file_menu.Append( wx.ID_OPEN, "&Open" )
        self.Bind( wx.EVT_MENU, self.on_open, item )

        self.m_file_save = file_menu.Append( wx.ID_SAVE, "&Save" )
        self.m_file_save.Enable( False )
        self.Bind( wx.EVT_MENU, self.on_save, self.m_file_save )

        self.m_file_saveas = file_menu.Append( wx.ID_SAVEAS, "&SaveAs" )
        self.m_file_saveas.Enable( False )
        self.Bind( wx.EVT_MENU, self.on_saveas, self.m_file_saveas )
        '''

        item = file_menu.Append( wx.ID_EXIT, "Quit") 
        self.Bind( wx.EVT_MENU, self.on_quit, item )     
        menu_bar.Append( file_menu, "&File" )

        # antenna menu
        antenna_menu = wx.Menu()

        ID_ANTENNA_INITIALIZE = wx.NewIdRef()
        item = antenna_menu.Append( ID_ANTENNA_INITIALIZE, "Initialize" )
        self.Bind( wx.EVT_MENU, self.on_antenna_initialize, item )

        ID_ANTENNA_PARK = wx.NewIdRef()
        item = antenna_menu.Append( ID_ANTENNA_PARK, "Park" )
        self.Bind( wx.EVT_MENU, self.on_antenna_park, item )

        ID_ANTENNA_INFO = wx.NewIdRef()
        item = antenna_menu.Append( ID_ANTENNA_INFO, "Info" )
        self.Bind( wx.EVT_MENU, self.on_antenna_info, item )

        menu_bar.Append( antenna_menu, "&Antenna" )

        # help menu
        help_menu = wx.Menu()

        ID_HELP_ABOUT = wx.NewIdRef()
        item = help_menu.Append( ID_HELP_ABOUT, "About" )
        self.Bind( wx.EVT_MENU, self.on_about, item )

        menu_bar.Append( help_menu, "&Help" )

        self.SetMenuBar( menu_bar )

        # respond to exit symbol 'x' on frame title bar
        self.Bind( wx.EVT_CLOSE, self.on_close )

    def on_about( self, event=None ):      # about dialog
        pass

    def on_close( self, event ):           # really exit 

        # clean up before exiting
        if self.mon_thread != None:
            self.mon_thread.stop()
            self.mon_thread.join()

        self.star.sched.stop()
        self.star.sched.join()

        logging.info( 'stargui: exiting program.' )
        event.Skip()

    def on_quit( self, event=None ):
        self.Close()                       # exit application

    def on_antenna_initialize( self, event=None ):
        if self.star.sched.tracking:       # FIXME: or close to tracking
            self.message( 'Antenna is tracking...try later', 
                          'Cannot Initialize Antenna', wx.ICON_EXCLAMATION )
            return

        logging.info( 'stargui: initializing rotors' )

        self.Enable( False )               # no access to frame
        self.mon_thread.enable( False )    # won't be able to read rotor
                                           # while initializing anyway.

        # spawn a thread to initialize rotor; kills itself when done
        calib_thread = calib( self.star.rotor )
        calib_thread.start()

        calib_progress( self.star.rotor )  # calib progress dialog.
                                           # 
        self.mon_thread.enable( True )
        self.Enable( True )                # give access to frame

        logging.info( 'stargui: rotors initialized' )
        
    def on_antenna_park( self, event=None ):
        if self.star.sched.tracking:
            self.message( 'Antenna is tracking...try later', 
                          'Cannot Park Antenna', wx.ICON_EXCLAMATION )
            return

        self.star.rotor.park()

    def on_antenna_info( self, event=None ):
        info = self.star.rotor.get_info()
        self.message( info, 'Antenna Information', wx.ICON_INFORMATION )
        
    def message( self, text, title, icon ):
        dia = wx.MessageDialog( self, text, title, 
                                style=wx.OK|icon )
        dia.SetSize( (200,150) )
        dia.ShowModal()
        dia.Destroy()
            
# end stargui class
 
class calib_progress( wx.ProgressDialog ):
    def __init__( self, rotor ):
        wx.ProgressDialog.__init__( self, 'Antenna Initialization', 
                                   'calibrating...', 
                                   1000, style=wx.PD_ELAPSED_TIME )        
        start = time.time()                        # timeout start
        while rotor.is_calibrating():
            self.Pulse()
            now = time.time()

            if (now-start) > rotor.calib_duration: # timed out?
                message = 'Initialization of rotor ' + rotor.name + ' has timed out.'
                dia = wx.MessageDialog( self, message, 'Timeout Error', 
                                        style=wx.OK|wx.ICON_ERROR )
                dia.SetSize( (100,150) )
                dia.ShowModal()
                dia.Destroy()
                break

            time.sleep( 0.1 )

        self.Destroy()

#################################################################
  
if __name__ == '__main__':   # user entry point  

    # use configuration file as argument
    if len( sys.argv ) > 1:  # check for configuration file
        config_file = sys.argv[1]

        # check if file exists; exit if not
        if not os.path.isfile( config_file ) :
            eprint( 'stargui: config file: ' + config_file +
                    ' does not exist ... exiting.' )
            sys.exit(1)
    else:
        eprint( 'no config file given ... exiting.' )
        eprint( 'usage:stargui.py config_file [log_file]' )
        sys.exit( 1 )

    if len( sys.argv ) > 2:  # check for log file
        log_file = sys.argv[2]
    else:
        log_file = 'star.log'

    app = wx.App()        
    frame = stargui( log_file, config_file  )
    frame.Show()

    # spawn a thread to monitor rotor status
    frame.mon_thread = monitor( frame, log_file )
    frame.mon_thread.start()

    app.MainLoop()
    
# end stargui.py
