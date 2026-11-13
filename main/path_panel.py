'''
@path_panel.py
@author Scott L. Williams
@package STaR
@brief Shows the satellite path in a panel.
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
GUI panel showing the path of the satellite across the horizon. Contains
circles indication 0,30,60,90 degrees plus the minimum elevation for reading
and signal acquisition.
'''
# 
path_panel_copyright = 'path_panel.py Copyright (c) 2020-2026 Scott L. Williams, released under GNU GPL V3.0'

import wx
import sys
import math
import logging
from ezprint import eprint

class path_panel( wx.Panel ):
    def __init__( self, benchtop, star ):
        wx.Panel.__init__( self, benchtop )
 
        self.sched = star.sched
        self.benchtop = benchtop
        self.zenith_min = star.zenith_min
        self.sig_elev = star.sig_elev
        self.rotor = star.rotor
        self.coord = None

        self.setup()
        self.reset()

        # use the same logger name
        self.logger = logging.getLogger( 'star_logger' )
        self.logger.info( 'logger initialized in path_panel' )

    def reset( self ):
        az,el = self.rotor.get_azel()
        self.cnv_x,self.cnv_y = self.angles2scrn( az, el ) # from rotor
                                                           # to canvas pixels
        self.Refresh()

    def setup( self ):

        self.SetToolTip(
            'hover mouse for position. press left button to move antenna')
        
        #self.SetBackgroundColour( wx.WHITE )

        vsizer = wx.BoxSizer( wx.VERTICAL )
        hsizer = wx.BoxSizer( wx.HORIZONTAL )

        label = wx.StaticText( self, -1, 'az: ', size=(20,18) )
        hsizer.Add( label, 0 )
        self.t_az = wx.StaticText( self, -1, '     ', 
                                   style=wx.ALIGN_RIGHT,size=(35,18) )
        hsizer.Add( self.t_az, 0 )
        hsizer.Add( (23,18 ) )
        label = wx.StaticText( self, -1, '  N', size=(30,18) )
        hsizer.Add( label )
        hsizer.Add( (20,18 ) )
        label = wx.StaticText( self, -1, 'el: ', size=(20,18) )
        hsizer.Add( label, 0 )
        self.t_el = wx.StaticText( self, -1, '     ', 
                                   style=wx.ALIGN_RIGHT,size=(35,18) )
        hsizer.Add( self.t_el, 0 )

        vsizer.Add( hsizer )
        vsizer.Add( (175,2) )

        self.canvas = wx.Panel( self,style=wx.SUNKEN_BORDER, size=(175,155) )
        self.canvas.Bind( wx.EVT_MOTION, self.on_motion )
        self.canvas.Bind( wx.EVT_LEFT_UP, self.on_left_up )
        self.canvas.Bind( wx.EVT_ENTER_WINDOW, self.on_enter )
        self.canvas.Bind( wx.EVT_LEAVE_WINDOW, self.on_leave )
        self.canvas.Bind( wx.EVT_PAINT, self.on_paint )

        self.canvas.SetBackgroundColour( wx.WHITE )
        vsizer.Add( self.canvas )
        vsizer.Add( (175,3) )

        hsizer = wx.BoxSizer( wx.HORIZONTAL )

        self.l_maz = wx.StaticText( self, -1, '    ', size=(20,18) )
        hsizer.Add( self.l_maz, 0 )
        self.t_maz = wx.StaticText( self, -1, '     ', 
                                   style=wx.ALIGN_RIGHT,size=(35,18) )
        hsizer.Add( self.t_maz, 0 )
        hsizer.Add( (53,18 ) )

        self.l_mel = wx.StaticText( self, -1, '    ', size=(20,18) )
        hsizer.Add( self.l_mel, 0 )
        self.t_mel = wx.StaticText( self, -1, '     ', 
                                   style=wx.ALIGN_RIGHT,size=(35,18) )
        hsizer.Add( self.t_mel, 0 )
        vsizer.Add( hsizer )

        self.SetSizer( vsizer )        

    def on_enter( self, event ):           # elvis has entered the panel
        self.l_maz.SetLabel( 'az: ' )
        self.l_mel.SetLabel( 'el: ' )

    def on_leave( self, event ):           # elvis has left the panel
        self.l_maz.SetLabel( '    ' )
        self.l_mel.SetLabel( '    ' )
        self.t_maz.SetLabel( '    ' )
        self.t_mel.SetLabel( '    ' )

    def on_left_up( self, event ):         # move antenna
        point= event.GetPosition()  
        az,el = self.scrn2angles( point[0], point[1] )

        if el >= 0.0:
            if self.sched.tracking:
                self.message( 'antenna is tracking; cannot comply',
                              'Antenna Move Request', wx.ICON_EXCLAMATION )
            else:
                self.logger.info( 'path_panel: moving antenna to ' + '%.1f'%az +
                              ',' + '%.1f'%el )
                self.rotor.move_azel( az, el )

    def on_motion( self, event ):      # 
        point = event.GetPosition()        
        az,el = self.scrn2angles( point[0], point[1] )

        if el >= 0.0:
            self.t_maz.SetLabel( '%5.1f'%az )
            self.t_mel.SetLabel( '%5.1f'%el ) 
        
    def find_az( self, x, y ): # FIXME: gotta be a better way
        if x==0.0 and y==0.0:
            return 0.0

        r = math.sqrt( x*x + y*y )
        if x > 0.0:
            if (y >= 0.0):
                return math.acos(y/r)
            else:
                return math.pi/2 + math.acos(x/r)

        if (y <= 0.0):
            return math.pi + math.acos(-y/r)

        return 3*math.pi/2.0 + math.acos(-x/r)
 
    def find_el( self, x, y ):
        if x==0.0 and y==0.0:
            return math.pi/2.0

        r = math.sqrt( x*x + y*y )
        return math.pi/2.0 - r*math.pi/2.0
        
    def scrn2angles( self, px, py ):

        # transform to -1.2,1.2
        sizex,sizey = self.canvas.GetClientSize()
        p = sizex/float(sizey)
        x = ((px-(sizex-sizey)/2)*p-sizex/2.0)*(2.4/sizex) # make proportional
        y = (sizey/2.0-py)*(2.4/sizey)                     # to x,y size diff
        
        az = math.degrees(self.find_az(x,y))
        el = math.degrees(self.find_el(x,y))

        return az,el

    def find_x( self, az, el ):
        r = 1.0 - el/(math.pi/2)  # r is proportional to elevation (inclination)
        az %= 2*math.pi           # FIXME: review thie

        if az >= 0 and az < math.pi/2:
            return r*math.cos(math.pi/2-az)

        if az >= math.pi/2 and az < math.pi:
            return r*math.cos(az-math.pi/2)
            
        if az >= math.pi and az < 3*math.pi/2:
            return -r*math.cos(3*math.pi/2-az)

        if az >= 3*math.pi/2 and az <= 2*math.pi:
            return -r*math.cos(az-3*math.pi/2)

        eprint( 'find_x: unknown azimuth: ', az )
        return None
    
    def find_y( self, az, el ):
        r = 1.0 - el/(math.pi/2)  # r is proportional to elevation (inclination)
        az %= 2*math.pi           # FIXME: review this

        if az >= 0 and az < math.pi/2:
            return r*math.cos(az)

        if az >= math.pi/2 and az < math.pi:
            return -r*math.cos(math.pi-az)
            
        if az >= math.pi and az < 3*math.pi/2:
            return -r*math.cos(az-math.pi)

        if az >= 3*math.pi/2 and az <= 2*math.pi:
            return r*math.cos(2*math.pi-az)

        eprint( 'find_y: unknown azimuth: ', az )
        return None

    def angles2scrn( self, az, el ):
        raz = math.radians( az )                      # make radians
        rel = math.radians( el )

        x = self.find_x( raz, rel )                   # centered coordinates
        y = self.find_y( raz, rel )

        # transform to screen coordinates
        sizex,sizey = self.canvas.GetClientSize()     # make proportional
        p = sizex/float(sizey)                        # to x,y size diff
        px = int( (x/(2.4/sizex) + sizex/2.0)/p + 
                      (sizex-sizey)/2.0 + 0.5 )   
        py = int( sizey/2.0 - y/(2.4/sizey) ) #+ 0.5 )   
        
        return px, py
    
    def plot_circle( self, dc, color, elev ):

        dc.SetPen( wx.Pen(color) )            # built in circle generator
        dc.SetBrush( wx.TRANSPARENT_BRUSH )   # makes better circles than below

        sx,sy = self.angles2scrn( 90.0, elev )        # get radius to use
        sizex,sizey = self.canvas.GetClientSize()     # calculate origin

        dc.DrawCircle( int(sizex/2),
                       int(sizey/2),
                       int(sx-sizex/2) )

    def set_pass( self, coord ):
        self.coord = coord
        self.Refresh()

    def plot_path( self, dc, color ):  
        if self.coord == None:
            return

        # get and save start point
        sx,sy = self.angles2scrn( self.coord[0][2], 
                                  self.coord[0][3] )
        ix,iy = sx,sy 

        # draw the path
        dc.SetPen( wx.Pen(color) )
        n = len(self.coord)
        for i in range( 1, n ):
            ex,ey = self.angles2scrn( self.coord[i][2], 
                                      self.coord[i][3] )
            dc.DrawLine( sx, sy, ex, ey )
            sx = ex
            sy = ey

        # draw start point
        dc.SetPen( wx.Pen(wx.GREEN) )
        dc.SetBrush( wx.Brush(wx.GREEN,wx.SOLID) )
        dc.DrawCircle( ix, iy, 3 )                

        # draw end point
        dc.SetPen( wx.Pen(wx.RED) )        
        dc.SetBrush( wx.Brush(wx.RED,wx.SOLID) ) 
        dc.DrawCircle( ex, ey, 3 )               

    def draw_cursor( self, dc, color, size, x, y ):
        dc.SetPen( wx.Pen(color,1) )    
        #dc.SetLogicalFunction( wx.XOR )

        dc.DrawLine( x-size, y, x+size, y )  
        dc.DrawLine( x, y-size, x, y+size )

        # draw line to center
        #cx,cy = self.angles2scrn( 0.0,90.0 )
        #dc.DrawLine( cx, cy, x, y )  

    def update_pos( self ):
        az,el = self.rotor.get_azel()

        # sometimes on startup the client canvas size == 0
        try:
            cx,cy = self.angles2scrn( az, el )   # map angles to canvas
        except:
            return
        
        # redraw if position has changed
        if abs(cx-self.cnv_x)>0 or abs(cy-self.cnv_y)>0:

            self.t_az.SetLabel( '%5.1f'%az ) # report
            self.t_el.SetLabel( '%5.1f'%el )

            # refresh whole panel instead XORing cursor.
            # has to do with wxwidget and GTK3
            # broken SetLogicalFunctions
            self.cnv_x = cx
            self.cnv_y = cy

            self.Refresh() 
            '''
            dc = wx.ClientDC( self.canvas )
            self.draw_cursor( dc, wx.GREEN, 10,
                              self.cnv_x, self.cnv_y )
            self.draw_cursor( dc, wx.GREEN, 10, 
                              cx, cy )
            self.cnv_x = cx
            self.cnv_y = cy
            '''
            
    def on_paint( self, event ):
        dc = wx.PaintDC( self.canvas )

        # draw cross in middle of panel
        cx, cy = self.angles2scrn( 0.0, 90.0 )
        self.draw_cursor( dc, wx.Colour( 'black'), 80, cx, cy )

        # plot elevation circles
        self.plot_circle( dc, wx.Colour('black'), 0.0 )
        self.plot_circle( dc, wx.Colour('black'), 30.0 )
        self.plot_circle( dc, wx.Colour('black'), 60.0 )
        self.plot_circle( dc, wx.Colour('brown'), self.sig_elev )
       
        self.plot_path( dc, wx.Colour('blue') )

        # draw current rotor position
        self.draw_cursor( dc, wx.Colour('red'), 10, self.cnv_x, self.cnv_y )

        if event != None:
            event.Skip()

    def message( self, text, title, icon ):
        dia = wx.MessageDialog( self, text, title, style=wx.OK|icon )
        dia.SetSize( (100,150) )
        dia.ShowModal()
        dia.Destroy()
            
# end path_panel.py
