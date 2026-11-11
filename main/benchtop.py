'''
@file benchtop.py
@author Scott L. Williams
@package STaR
@brief top wxPanel for STaR components
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
Top level panel for STaRgui, the graphical interface for STaR 
(Satellite Track and Read) command line program. 
'''

benchtop_copyright = 'benchtop.py Copyright (C) 2020-2026 Scott L. Williams, released under GNU GPL V3.0'

import os
import wx
import sys
import time
import ephem
import datetime

from ezprint import eprint
from path_panel import path_panel

## @todo double click on pass selection gives as much info as pyephem can give

## Create the top panel for stargui.py
# @param parent main frame
class benchtop( wx.Panel ): 
    def __init__( self, parent ):
        wx.Panel.__init__( self, parent, 
                           style=wx.SUNKEN_BORDER )
        self.stargui = parent
        self.star = parent.star
        self.next_pass = None
        self.setup_benchtop()

    # layout benchtop
    def setup_benchtop( self ):

        # use equal size font
        font = self.Parent.GetFont()
        font.SetFamily(wx.MODERN)
        font.SetStyle(wx.NORMAL)
        font.SetPointSize( 9 )
        font.SetWeight(wx.FONTWEIGHT_LIGHT)

        vsizer = wx.BoxSizer( wx.VERTICAL )
        vsizer.Add( (457,5) )                 # spacer
        hsizer = wx.BoxSizer( wx.HORIZONTAL ) # setup pass list and rotor panel

        vvsizer = wx.BoxSizer( wx.VERTICAL )
        text = " {:14s} {:19s}  {:19s} {:5s}".format('satellite',
                                                     'rise time',
                                                     'set time',
                                                     'length' )

        label = wx.StaticText( self, -1, text, size=(457,20) )
        label.SetFont( font )
        vvsizer.Add( label, 0 ) 

        self.passlist = wx.ListBox( self, choices=[], style=wx.LB_SINGLE,
                                    size=(457,160))

        # use equal size font
        self.passlist.SetFont(font)
        
        self.passlist.Bind(wx.EVT_LISTBOX, self.on_select)
        vvsizer.Add( self.passlist )
        vvsizer.Add( (457,5) )

        hsizer.Add( vvsizer )
        hsizer.Add( (3,155) )

        # setup rotor graphics
        self.path_panel = path_panel( self, self.star )
        hsizer.Add( self.path_panel )
        vsizer.Add( hsizer, 0 )

        hsizer = wx.BoxSizer( wx.HORIZONTAL )
        label = wx.StaticText( self, -1, '  log messages:', size=(377,20) )
        hsizer.Add( label )
        label = wx.StaticText( self, -1, 'offsets: ', size=(50,20) )
        hsizer.Add( label )

        label = wx.StaticText( self, -1, ' lead', size=(35,20) )
        hsizer.Add( label )
        self.lead_t = wx.TextCtrl( self, size=(40,15), style=wx.TE_RIGHT )
        self.lead_t.Bind( wx.EVT_KEY_DOWN, self.on_key_down )
        hsizer.Add( self.lead_t )

        label = wx.StaticText( self, -1, ' az ', size=(25,20) )
        hsizer.Add( label,0 )
        self.az_t = wx.TextCtrl( self, size=(40,15), style=wx.TE_RIGHT )
        self.az_t.Bind( wx.EVT_KEY_DOWN, self.on_key_down )
        hsizer.Add( self.az_t,0 )

        label = wx.StaticText( self, -1, ' el ', size=(20,20) )
        hsizer.Add( label, 0 )
        self.el_t = wx.TextCtrl( self, size=(40,15), style=wx.TE_RIGHT )
        self.el_t.Bind( wx.EVT_KEY_DOWN, self.on_key_down )
        hsizer.Add( self.el_t,0 )

        vsizer.Add( hsizer, 0 )

        # setup message panel
        self.messages = wx.TextCtrl( self, style=wx.TE_MULTILINE | 
                                     wx.TE_READONLY | wx.HSCROLL,
                                     size=(635,212) )
        vsizer.Add( self.messages, 0 )
        self.SetSizer( vsizer )
        self.get_rotor_offsets()

    def get_rotor_offsets( self ):
        self.lead_t.SetValue( str(self.star.rotor.lead) )
        self.az_t.SetValue( str(self.star.rotor.az_offset) )
        self.el_t.SetValue( str(self.star.rotor.el_offset) )

    def on_key_down( self, event ):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_RETURN:
            try:
                self.star.rotor.lead = float( self.lead_t.GetValue() )
                self.star.rotor.az_offset = float( self.az_t.GetValue() )
                self.star.rotor.el_offset = float( self.el_t.GetValue() )
                self.get_rotor_offsets()
            except:
                eprint("offset input error, try again." )

        event.Skip() # pass along event

    def on_select( self, event ):
        index = self.passlist.GetSelection()

        # multiple selection gives -1
        if index >= 0 and index < len( self.star.sched.passes ):
            passes = self.star.sched.passes
            self.path_panel.set_pass( passes[index] )  # redraw pass plot

    def update_passlist( self ):
        passes = self.star.sched.passes
        
        if passes == None:                      # FIXME: sometimes wants to
            self.star.update_passlist = True    #        update before getting
            return                              #        passes. try again.

        self.star.update_passlist = False
        self.passlist.Clear()
        for i in range( len(passes) ):
            n = len( passes[i] ) - 1 
            aos = ephem.localtime( passes[i][0][1] ) 
            los = ephem.localtime( passes[i][n][1] )
            diff = los-aos
            
            # add 1 second, an example diff outputs:0:13:29.999934
            # want to round-up to get 0:13:30
            diff = diff + datetime.timedelta(0,1) # days, seconds
                                                  # then other fields.
            name = passes[i][0][0]
            name = f"{name:<14}"
            aos = str(aos)[:19]
            los = str(los)[:19]
            diff = str(diff)[2:7]
            text = "{:14s} {:19s}  {:19s}  {:5s}".format(name, aos, los, diff)

            self.passlist.Append( str(text) )
            if i == 0:
                self.stargui.mstatus.SetStatusText( text[:34], 4 )
                self.next_pass = passes[i][0][1]

        self.passlist.SetSelection( 0 )
        self.path_panel.set_pass( passes[0] )
        
    def update_messages( self, text ):
        self.messages.AppendText( text )

# end benchtop.py
