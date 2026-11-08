'''
@file load_module.py
@author Scott L. Williams
@package STaR
@brief Loads a rotor module.
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
Dynamically loads a rotor module specified in the configuration file.
'''

load_module_copyright = 'load_module.py Copyright (c) 2020 Scott L. Williams '+ \
            'released under GNU GPL V3.0'

import os
import sys
import imp

# retrieve and load module 
def load_module( package_path ):
    pathlist = [ package_path ] # only one path

    # parse package_path string to get package name
    module_name = os.path.basename( package_path )

    try:
        # find the principal module in package
        f, filename, descrip = imp.find_module( module_name, pathlist )
        try:
            return imp.load_module( module_name, f, filename, descrip )
        finally:
            if f:
                f.close()

    except Exception as e:  # TODO: find correct error exception
        print('load_module: ', e, file=sys.stderr, flush=True)

# end load_module
        
# end load_module.py
