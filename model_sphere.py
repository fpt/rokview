#!/usr/bin/env python
# ----------------------------------------------------------------------------
# Pyglet GLSL Demo Phong Shader on http://www.pythonstuff.org
# pythonian_at_gmx_dot_at  (c) 2010
#
# based on the "graphics.py" batch/VBO demo by
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------

from math import pi, sin, cos, sqrt
from euclid import *

import pyglet
from pyglet.gl import *

class Sphere(object):
    vv = []            # vertex vectors
    vcount = 0
    vertices = []
    normals = []
    textureuvw = []
    tangents = []
    indices  = []

    def myindex( self, list, value ):
        for idx, obj in enumerate(list):
            if abs(obj-value) < 0.0001:
              return idx
        raise ValueError # not found

    def splitTriangle(self, i1, i2, i3, new):
        '''
        Interpolates and Normalizes 3 Vectors p1, p2, p3.
        Result is an Array of 4 Triangles
        '''
        p12 = self.vv[i1] + self.vv[i2]
        p23 = self.vv[i2] + self.vv[i3]
        p31 = self.vv[i3] + self.vv[i1]
        p12.normalize()
        try:
            if new[0] == "X":
                ii0 = self.myindex(self.vv, p12)
            else:
                self.vv.append( p12 )
                ii0 = self.vcount
                self.vcount += 1
        except ValueError:
            print "This should not happen 1"
        p23.normalize()
        try:
            if new[1] == "X":
                ii1 = self.myindex(self.vv, p23)
            else:
                self.vv.append( p23 )
                ii1 = self.vcount
                self.vcount += 1
        except ValueError:
            print "This should not happen 2"
        p31.normalize()
        try:
            if new[2] == "X":
                ii2 = self.myindex(self.vv, p31)
            else:
                self.vv.append( p31 )
                ii2 = self.vcount
                self.vcount += 1
        except ValueError:
            print "This should not happen 3"
        rslt = []
        rslt.append([i1,  ii0, ii2])
        rslt.append([ii0, i2,  ii1])
        rslt.append([ii0, ii1, ii2])
        rslt.append([ii2, ii1,  i3])
        return rslt

    def recurseTriangle(self, i1, i2, i3, level, new):
        if level > 0:                     # split in 4 triangles
            p1, p2, p3, p4 = self.splitTriangle( i1, i2, i3, new )
            self.recurseTriangle( *p1, level=level-1, new=new[0]+"N"+new[2] )
            self.recurseTriangle( *p2, level=level-1, new=new[0]+new[1]+"N" )
            self.recurseTriangle( *p3, level=level-1, new="XNX" )
            self.recurseTriangle( *p4, level=level-1, new="X"+new[1]+new[2] )
        else:
           self.indices.extend( [i1, i2, i3] ) # just MAKE the triangle

    def flatten(self, x):
        result = []

        for el in x:
            #if isinstance(el, (list, tuple)):
            if hasattr(el, "__iter__") and not isinstance(el, basestring):
                result.extend(self.flatten(el))
            else:
                result.append(el)
        return result

    def __init__(self, radius, slices, batch, group=None):
        print "Creating Sphere... please wait"
        # Create the vertex array.
        self.vv.append( Vector3( 1.0, 0.0, 0.0) ) # North
        self.vv.append( Vector3(-1.0, 0.0, 0.0) ) # South
        self.vv.append( Vector3( 0.0, 1.0, 0.0) ) # A
        self.vv.append( Vector3( 0.0, 0.0, 1.0) ) # B
        self.vv.append( Vector3( 0.0,-1.0, 0.0) ) # C
        self.vv.append( Vector3( 0.0, 0.0,-1.0) ) # D
        self.vcount = 6

        self.recurseTriangle( 0, 2, 3, slices, "NNN" ) # N=new edge, X=already done
        self.recurseTriangle( 0, 3, 4, slices, "XNN" )
        self.recurseTriangle( 0, 4, 5, slices, "XNN" )
        self.recurseTriangle( 0, 5, 2, slices, "XNX" )
        self.recurseTriangle( 1, 3, 2, slices, "NXN" )
        self.recurseTriangle( 1, 4, 3, slices, "NXX" )
        self.recurseTriangle( 1, 5, 4, slices, "NXX" )
        self.recurseTriangle( 1, 2, 5, slices, "XXX" )

        print "Sphere Level ", slices, " with ", self.vcount, " Vertices"

        for v in range(self.vcount):
            self.normals.extend(self.vv[v][:])
        self.vv = [(x * radius) for x in self.vv]
        self.vertices = [x[:] for x in self.vv]
        self.vertices = self.flatten( self.vertices )

        self.vertex_list = batch.add_indexed(len(self.vertices)//3,
                                             GL_TRIANGLES,
                                             group,
                                             self.indices,
                                             ('v3f/static', self.vertices),
                                             ('n3f/static', self.normals))

    def delete(self):
        self.vertex_list.delete()
