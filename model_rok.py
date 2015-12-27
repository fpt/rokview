import sys
import pprint
from math import *

import pyglet
from pyglet.gl import *


class vertex_node:
    def __init__(self, _group_id, _b_display, _pos):
        self.group_id = _group_id
        self.b_display = _b_display
        self.pos = _pos

        self.b_selected = False;
        self.normal = (.0, .0, .0)
        self.color = (.0, .0, .0)
        self.uvcoord = (.0, .0)

    def __repr__(self):
        return "(%f, %f, %f)" % self.pos

class line_node:
    def __init__(self, _id, _group_id, _b_disp, _begin_idx, _end_idx):
        self.id = _id
        self.group_id = _group_id
        self.b_display = _b_disp
        self.begin_idx = _begin_idx
        self.end_idx = _end_idx

        self.type = 0
        self.mat_id = 0
        self.width = 1.0
        self.b_selected = False

    def __repr__(self):
        return "(%d, %d)" % (self.begin_idx, self.end_idx)

class facet_node:
    def __init__(self, _facet_id, _mat_id):
        self.id = _facet_id
        self.mat_id = _mat_id

        self.b_selected = False
        self.vec_vertex_idx = []
        self.vec_line_idx = []
        self.normal = (.0, .0, .0)

    def flip():
        for i in range(3):
            normal[i] = -normal[i]
        swap_time = len(vec_vertex) / 2;
        last = len(vec_vertex) - 1;

        for i in range(swap_time):
            tmp = vec_vertex[i];
            vec_vertex[i] = vec_vertex[last-i];
            vec_vertex[last-i] = tmp;

class material:
    def __init__(self):
        self.diffuse = (.0, .0, .0, .0)
        self.ambient = (.0, .0, .0, .0)
        self.specular = (.0, .0, .0, .0)

    def __repr__(self):
        return "(%f, %f, %f)" % (self.diffuse[0], self.diffuse[1], self.diffuse[2])


def read_int(ifs, line = None):
    if line is None:
        line = ifs.readline()
    return int(line.strip())

def read_float(ifs):
    line = ifs.readline()
    return float(line.strip())

def array_extend(arr, size):
    while len(arr) < size:
        arr.append(None) 

def sort_chain(chain):
    arr = []

    # debug
    chain = chain[:]

    link = chain[0]
    chain.remove(link)
    arr.append(link.begin_idx)
    tail_idx = link.end_idx

    while len(chain) > 0:
        for link in chain:
            if link.begin_idx == tail_idx:
                chain.remove(link)
                arr.append(tail_idx)
                if link.end_idx in arr:
                    return arr
                else:
                    tail_idx = link.end_idx
                    break
            elif link.end_idx == tail_idx:
                chain.remove(link)
                arr.append(tail_idx)
                if link.begin_idx in arr:
                    return arr
                else:
                    tail_idx = link.begin_idx
                    break

    if tail_idx != arr[0]:
        pprint.pprint(tail_idx)
        pprint.pprint(arr)
        raise Exception("not a circular chain")

    # Can't happen
    raise Exception("CAN_NOT_HAPPEN")


class RokModel:
    def __init__(self):
        self.camera_pos = (.0, .0, .0)
        self.camera_target = (.0, .0, .0)

        self.light0_pos = (.0, .0, .0)
        self.light1_pos = (.0, .0, .0)
        self.light2_pos = (.0, .0, .0)

        self.x_min, self.x_max = (.0, .0)
        self.y_min, self.y_max = (.0, .0)
        self.z_min, self.z_max = (.0, .0)

        self.vec_facet = []
        self.vec_vertex = []
        self.vec_line = []
        self.vec_material = []

    def idx2pos(self, idx):
        return self.vec_vertex[idx].pos

    def idx2norm(self, idx):
        return self.vec_vertex[idx].normal

    def calcNormal(self):
        for fac in self.vec_facet:
            n = [.0, .0, .0]

            vvx = fac.vec_vertex_idx

            for j in range(len(vvx)):

                v = self.idx2pos(vvx[j])

                if j == 0:
                    v0 = self.idx2pos(vvx[len(vvx) - 1])
                    v1 = self.idx2pos(vvx[j + 1])
                elif j == len(vvx) - 1:
                    v0 = self.idx2pos(vvx[j - 1])
                    v1 = self.idx2pos(vvx[0])
                else:
                    v0 = self.idx2pos(vvx[j - 1])
                    v1 = self.idx2pos(vvx[j + 1])

                a = [.0, .0, .0]
                b = [.0, .0, .0]
                for k in range(3):
                    a[k] = v0[k] - v[k]
                    b[k] = v1[k] - v[k]

                # Facet normal (Cross product)
                n[0] += a[1] * b[2] - b[1] * a[2]
                n[1] += b[0] * a[2] - a[0] * b[2]
                n[2] += a[0] * b[1] - b[0] * a[1]

            # normalize
            ln = sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2])

            n[:] = [i / ln for i in n]

            fac.normal = n
        return


    def _update_min_max(self, x, y, z):
        if x < self.x_min:
            self.x_min = x
        else:
            if x > self.x_max:
                self.x_max = x

        if y < self.y_min:
            self.y_min = y
        else:
            if y > self.y_max:
                self.y_max = y

        if z < self.z_min:
            self.z_min = z
        else:
            if z > self.z_max:
                self.z_max = z

    def _load_roku(self, ifs):
        rmat_pp = read_float(ifs)
        rmat_pq = read_float(ifs)
        rmat_pr = read_float(ifs)
        rmat_dx = read_float(ifs)
        rmat_dy = read_float(ifs)
        rmat_dz = read_float(ifs)
        rmat_bx = read_float(ifs)
        rmat_by = read_float(ifs)
        rmat_pers = read_int(ifs)
        direction = read_int(ifs)
        zoom_x = read_float(ifs)
        zoom_y = read_float(ifs)
        move_x = read_float(ifs)
        move_y = read_float(ifs)
        return ifs.readline()

    def _load_point(self, ifs):
        carry = None
        cnt = 0
        while True:
            point_id = read_int(ifs, carry);
            group_id = read_int(ifs);
            b_display = read_int(ifs);
            dummy = read_int(ifs);
            sym_id = read_int(ifs);
            x = read_float(ifs);
            y = -read_float(ifs);
            z = -read_float(ifs);

            current = vertex_node(group_id, b_display, (x, y, z))
            array_extend(self.vec_vertex, point_id)
            self.vec_vertex[point_id - 1] = current

            self._update_min_max(x, y, z)
            cnt += 1

            carry = ifs.readline()
            if carry is None or carry[0] != ' ':
                print("Total %d points" % (cnt))
                return carry

    def _load_line(self, ifs):
        carry = None
        cnt = 0
        id = 1;

        while True:
            line_begin = read_int(ifs, carry);
            line_end = read_int(ifs);
            group_id = read_int(ifs);
            b_display = read_int(ifs);

            current = line_node(id, group_id, b_display, line_begin - 1, line_end - 1)

            self.vec_line.append(current);
            id += 1
            cnt += 1

            carry = ifs.readline()
            if carry is None or carry[0] != ' ':
                print("Total %d lines" % (cnt))
                return carry

    def _load_face(self, ifs):
        carry = None
        cnt = 0

        while True:
            num_vertex = read_int(ifs, carry)
            mat_id = read_int(ifs)
            facet_id = read_int(ifs)

            current = facet_node(facet_id, mat_id)

            edge_line = []
            for i in range(num_vertex):
                idx = read_int(ifs)
                edge_line.append(self.vec_line[idx - 1])

            current.vec_line_idx = edge_line
            current.vec_vertex_idx = sort_chain(edge_line)

            # debug
            if len(current.vec_vertex_idx) < 3:
                pprint.pprint(num_vertex)
                pprint.pprint(edge_line)
                pprint.pprint(current.vec_vertex_idx)

            self.vec_facet.append(current);
            cnt += 1

            carry = ifs.readline()
            if carry is None or carry[0] != ' ':
                print("Total %d faces" % (cnt))
                return carry

    def _load_palc(self, ifs):
        num_color = read_int(ifs);
        dummy = read_int(ifs);
        for i in range(num_color):
            bri_r = read_int(ifs)
            bri_g = read_int(ifs)
            bri_b = read_int(ifs)
            drk_r = read_int(ifs)
            drk_g = read_int(ifs)
            drk_b = read_int(ifs)
            reserved = read_int(ifs)

            mat = material()
            mat.specular = ( float(bri_r) / 255.0
                            ,float(bri_r) / 255.0
                            ,float(bri_r) / 255.0
                            ,1.0 )
            mat.diffuse = (  float(drk_r) / 255.0
                            ,float(drk_g) / 255.0
                            ,float(drk_b) / 255.0
                            ,1.0  )
            self.vec_material.append(mat);
        return ifs.readline()

    def _load_bakc(self, ifs):
        num_color = read_int(ifs);
        color_sel = read_int(ifs);
        for i in range(num_color):
            red = read_int(ifs)
            green = read_int(ifs)
            blue = read_int(ifs)
            reserved = read_int(ifs)
        return ifs.readline()

    def _load_lit(self, ifs):
        num_light = read_int(ifs)
        selected_light = read_int(ifs)
        for i in range(num_light):
            x = read_float(ifs);
            y = read_float(ifs);
            z = read_float(ifs);
            reserved = read_int(ifs);

            if i == 0:
                light0_pos = (x, y, z)
            elif i == 1:
                light1_pos = (x, y, z)
            elif i == 2:
                light2_pos = (x, y, z)

    def _load_view(self, ifs):
        bool_show_line = read_int(ifs)
        bool_show_facet = read_int(ifs)
        reserved = read_int(ifs)
        reserved = read_int(ifs)


    def _load_line2(self, ifs):
        carry = None
        while True:
            line_id = read_int(ifs, carryover)
            line_type = read_int(ifs)
            line_mat_id = read_int(ifs)
            line_width = read_int(ifs)

            line = self.vec_line[line_id - 1]
            line.type = line_type
            line.mat_id = line_mat_id
            line.width = line_width

            carry = ifs.readline()
            if carry is None or carry[0] != ' ':
                return carry

    def load(self, filename):

        with open(filename, 'rU') as ifs:

            cmd = ifs.readline()
            while cmd:
                cmd = cmd.strip()
                print(cmd)
                if cmd == "ROKU4":
                    cmd = self._load_roku(ifs)
                elif cmd == "POINT":
                    cmd = self._load_point(ifs)
                elif cmd == "LINE0":
                    cmd = self._load_line(ifs)
                elif cmd == "FACE0":
                    cmd = self._load_face(ifs)
                elif cmd == "PALC0":
                    cmd = self._load_palc(ifs)
                elif cmd == "BAKC0":
                    cmd = self._load_bakc(ifs)
                elif cmd == "LIT00":
                    cmd = self._load_lit(ifs)
                elif cmd == "VIEW0":
                    cmd = self._load_view(ifs)
                elif cmd == "LINE2":
                    cmd = self._load_line2(ifs)
                elif cmd == "END00":
                    cmd = ifs.readline()
                elif cmd == "ENDP0":
                    cmd = ifs.readline()
                elif cmd == "ENDB0":
                    cmd = ifs.readline()
                else:
                    raise Exception("chunk too long.")

        self.calcNormal()

        return 0

    SelectedColor = (1.0, .0, .0, .0)

    def render(self, b_poly = True, b_line = False, b_point = False):
        facet_normal = True

        glInitNames();

        # Poly
        #glPushName(SE_POLY);

        if b_poly:
            glEnable(GL_LIGHTING);
            #glEnable(GL_POLYGON_OFFSET_FILL);
            glPolygonOffset(.5, 1.0);

            for fac in self.vec_facet:
                #glPushName(i);
                glBegin(GL_POLYGON);

                if (fac.b_selected):
                    glMaterialfv(GL_FRONT, GL_DIFFUSE, SelectedColor)
                else:
                    mat = self.vec_material[fac.mat_id]
                    glMaterialfv(GL_FRONT, GL_SPECULAR, (GLfloat * 4)(*mat.specular))
                    glMaterialfv(GL_FRONT, GL_DIFFUSE, (GLfloat * 4)(*mat.diffuse))
                    glMaterialfv(GL_FRONT, GL_AMBIENT, (GLfloat * 4)(*mat.ambient))

                if (facet_normal):
                    glNormal3fv((GLfloat * 3)(*fac.normal))

                for vi in fac.vec_vertex_idx:
                    if not facet_normal:
                        glNormal3fv(self.idx2norm(vi))
                    glVertex3fv((GLfloat * 3)(*self.idx2pos(vi)))
                glVertex3fv((GLfloat * 3)(*self.idx2pos(fac.vec_vertex_idx[0])))
                glEnd();

                # reverse side
                glBegin(GL_POLYGON)

                if facet_normal:
                    glNormal3f(-fac.normal[0], -fac.normal[1], -fac.normal[2])

                rev_vec_vertex_idx = list(reversed(fac.vec_vertex_idx))
                for vi in rev_vec_vertex_idx:
                    if not facet_normal:
                        n = idx2norm(vi)
                        glNormal3f(-n[0],
                                -n[1],
                                -n[2])
                    glVertex3fv((GLfloat * 3)(*self.idx2pos(vi)))
                glVertex3fv((GLfloat * 3)(*self.idx2pos(rev_vec_vertex_idx[0])))
                glEnd()
                #glPopName()

            #glDisable(GL_POLYGON_OFFSET_FILL)
            glDisable(GL_LIGHTING)

        #glPopName()

        # Line
        #glPushName(SE_LINE)
        # Lines
        if b_line:
            glDisable(GL_LIGHTING)
            for ln in self.vec_line:
                #glPassThrough(i);
                #glPushName(i);
                glBegin(GL_LINE_STRIP);
                glLineWidth(ln.width);

                if ln.b_display:
                    if ln.b_selected:
                        glColor3f(1.0, 0.0, 0.0);
                        glLineWidth(ln.width * 2.0);
                    else:
                        glColor3fv((GLfloat * 3)(*self.vec_material[ln.mat_id].diffuse))
                else:
                    glColor3f(.5, .5, .5);

                glVertex3fv((GLfloat * 3)(*self.idx2pos(ln.begin_idx)))
                glVertex3fv((GLfloat * 3)(*self.idx2pos(ln.end_idx)))
                glEnd()

                #glPopName()

            glEnable(GL_LIGHTING)

        #glPopName();

        # Point
        #glPushName(SE_VERTEX)
        if b_point:
            glDisable(GL_LIGHTING)

            for i in range(len(vec_vertex)):
                #glPassThrough(i);
                #glPushName(i);

                if vec_vertex[i].b_selected:
                    glPointSize(5.0);
                else:
                    glPointSize(3.0);

                glBegin(GL_POINTS);

                if vec_vertex[i].b_display:
                    if vec_vertex[i].b_selected:
                        glColor3f(1.0, 0.0, 0.0)
                    else:
                        glColor3f(0.0, 0.0, 0.0)
                else:
                    glColor3f(.5, .5, .5)

                glVertex3fv(vec_vertex[i].pos)
                glEnd()

                #glPopName()

            glEnable(GL_LIGHTING);

        #glPopName();
# end of MeshObj
