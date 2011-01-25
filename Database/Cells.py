﻿# -*- coding: utf-8 -*-

# Copyright (C) 2009 PSchem Contributors (see CONTRIBUTORS for details)

# This file is part of PSchem Database
 
# PSchem is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# PSchem is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public License
# along with PSchem Database.  If not, see <http://www.gnu.org/licenses/>.

from Database.Primitives import *
from xml.etree import ElementTree as et

class CellView():
    def __init__(self, name):
        self._name = 'cell_view'
        self._attribs = {}
        self._designs = set()
        self._cell = None

    def installUpdateHook(self, design):
        self._designs.add(design)
        ##view.addElements()
        #for elem in self._elems:
        #    elem.addToView(view)

    def updateDesigns(self):
        for d in self._designs:
            d.updateDesign()
            #v.updateItem()
            
    def attributeLabels(self):
        return filter(lambda e: isinstance(e, AttributeLabel), self._elems)

    def pins(self):
        return filter(lambda e: isinstance(e, Pin), self._elems)

    def name(self):
        return self._name

    def cell(self):
        return self._cell

    def attribs(self):
        return self._attribs

    def setCell(self, cell):
        self._cell = cell

    def setParent(self, parent):
        self.setCell(parent)

    def parent(self):
        return self.cell()

    #def cell(self):
    #    return self._parent
        
    def library(self):
        return self.cell().library()
        
    def database(self):
        return self.cell().database()
        
    def save(self):
        pass
        
    def restore(self):
        pass

    def remove(self):
        self._cell = None
        self._views = set()

class Diagram(CellView):
    def __init__(self, name):
        CellView.__init__(self, name)
        self._elems = set()
        self._lines = set()
        self._rects = set()
        self._labels = set()
        #self._uu = 160 # default DB units per user units
        self._attribs['uu'] = 160 # default DB units per user units
        self._name = 'diagram'
        
    def setUU(self, uu):
        self._attribs['uu'] = uu

    def elems(self):
        return self._elems

    def addElem(self, elem):
        self._elems.add(elem)
        for design in self._designs:
            design.addElem(elem)
        #    elem.addToView(view)

    def removeElem(self, elem):
        for design in self._designs:
            design.removeElem(elem)
        #elem.removeFromView()
        self._elems.remove(elem)

    def lines(self):
        return filter(lambda e: isinstance(e, Line), self.elems())

    def rects(self):
        return filter(lambda e: isinstance(e, Rect), self.elems())

    def labels(self):
        return filter(lambda e: isinstance(e, Label), self.elems())

    def uu(self):
        return self._attribs['uu']

    def remove(self):
        for e in list(self._elems):
            self.removeElem(e)
        CellView.remove(self)

    def save(self):
        root = et.Element(self._name)
        tree = et.ElementTree(root)
        for a in sorted(self.attribs()):
            root.attrib[str(a)] = str(self.attribs()[a])
        for e in sorted(self.elems(), key=Element.name):
            xElem = e.toXml()
            root.append(xElem)
        self._indentET(tree.getroot())
        et.dump(tree)
        #return tree
        
    def restore(self):
        pass
    
    def _indentET(self, elem, level=0):
        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self._indentET(elem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
    
class Schematic(Diagram):
    def __init__(self, name):
        Diagram.__init__(self, name)
        self._name = 'schematic'

    def components(self):
        components = map(lambda i: i.cell(), self.instances())
        return components.sort()

    def instances(self):
        return filter(lambda e: isinstance(e, Instance), self.elems())

    def nets(self):
        return filter(lambda e: isinstance(e, Net), self.elems())

    def netSegments(self):
        return filter(lambda e: isinstance(e, NetSegment), self.elems())

    def solderDots(self):
        return filter(lambda e: isinstance(e, SolderDot), self.elems())

    def checkNetSegments(self, segments = None):
        if not segments:
            segments = self.netSegments()
        origNetSegments = segments
        for n in origNetSegments:
            splitPoints = set()
            for n2 in origNetSegments:
                if n.containsInside(n2.x1(), n2.y1()):
                    splitPoints.add((n2.x1(), n2.y1()))
                    #print n.x1(), n.y1()
                if n.containsInside(n2.x2(), n2.y2()):
                    splitPoints.add((n2.x2(), n2.y2()))
                    #print n.x2(), n.y2()
            if splitPoints:
                splitPoints.add((n.x1(), n.y1()))
                splitPoints.add((n.x2(), n.y2()))
                pointList = list(splitPoints)
                if (n.x1() != n.x2()):
                    pointList.sort(lambda p1, p2: cmp(p1[0], p2[0]))
                else:
                    pointList.sort(lambda p1, p2: cmp(p1[1], p2[1]))
                prevPoint = pointList[0]
                for p in pointList[1:]:
                    newSegment = NetSegment(n.parent(), n.layers(), prevPoint[0], prevPoint[1], p[0], p[1])
                    self.addElem(newSegment)
                    #print prevPoint[0], p[0], prevPoint[1], p[1]
                    prevPoint = p
                self.removeElem(n)

    def checkSolderDots(self, segments = None):
        if not segments:
            segments = self.netSegments()
        origNetSegments = segments
        origSolderDots = self.solderDots()
        for n in origNetSegments:
            count1 = -1
            count2 = -1
            solder1 = filter(lambda sd: sd.x() == n.x1() and sd.y() == n.x2, origSolderDots)
            solder2 = filter(lambda sd: sd.x() == n.x1() and sd.y() == n.x2, origSolderDots)
            for n2 in origNetSegments:
                if ((n.x1() == n2.x1() and n.y1() == n2.y1()) or
                    (n.x1() == n2.x2() and n.y1() == n2.y2())):
                    count1 += 1
                if ((n.x2() == n2.x1() and n.y2() == n2.y1()) or
                    (n.x2() == n2.x2() and n.y2() == n2.y2())):
                    count2 += 1
            if count1 > 1:
                if not solder1:
                    solder = SolderDot(n.parent(), n.layers(), n.x1(), n.y1())
                    self.addElem(solder)
            elif solder1:
                    self.removeElem(solder1)
            if count2 > 1:
                if not solder2:
                    solder = SolderDot(n.parent(), n.layers(), n.x2(), n.y2())
                    self.addElem(solder)
            elif solder2:
                    self.removeElem(solder2)
                
class Symbol(Diagram):
    def __init__(self, name):
        Diagram.__init__(self, name)
        self._name = 'symbol'

class Netlist(CellView):
    def __init__(self, name):
        CellView.__init__(self, name)
        self._name = 'netlist'


class Cell():
    def __init__(self, name):
        self._views = set()
        self._viewNames = {}
        self._name = name
        self._parent = None

    def addView(self, cellView):
        self._views.add(cellView)
        cellView.setParent(self)
        self._viewNames[cellView.name()] = cellView
        self.database().updateDatabaseViews()

    def removeView(self, cellView):
        cellView.remove()
        self._views.remove(cellView)
        del(self._viewNames[cellView.name()])
        self.database().updateDatabaseViews()

    def views(self):
        return self._views

    def viewNames(self):
        return self._viewNames.keys()

    def viewByName(self, viewName):
        if self._viewNames.has_key(viewName):
            return self._viewNames[viewName]
        else:
            return None

    def name(self):
        return self._name

    def implementation(self):
        return self.viewByName('schematic')  #currently assume it is 'schematic'

    def symbol(self):
        return self.viewByName('symbol')  #currently assume it is 'symbol'

    def setParent(self, parent):
        self._parent = parent
        
    def parent(self):
        return self._parent

    def library(self):
        return self._parent
        
    def database(self):
        return self._parent.database()

class Library():
    def __init__(self, name):
        self._cells = set()
        self._cellNames = {}
        self._name = name
        self._parent = None

    def addCell(self, cell):
        self._cells.add(cell)
        cell.setParent(self)
        self._cellNames[cell.name()] = cell
        self.database().updateDatabaseViews()

    def cells(self):
        return self._cells

    def cellNames(self):
        return self._cellNames.keys()

    def cellByName(self, cellName):
        if self._cellNames.has_key(cellName):
            return self._cellNames[cellName]
        else:
            return None

    def viewByName(self, cellName, viewName):
        cell = self.cellByName(cellName)
        if cell:
            return cell.viewByName(viewName)
        else:
            return None

    def name(self):
        return self._name

    def setParent(self, parent):
        self._parent = parent
        
    def parent(self):
        return self._parent
        
    def database(self):
        return self._parent

    

class Database():
    def __init__(self):
        self._libraries = set()
        self._libraryNames = {}
        self._databaseViews = set()
        self._hierarchyViews = set()
        self._designs = set()
        self._layers = None

    def installUpdateDatabaseViewsHook(self, view):
        self._databaseViews.add(view)

    def installUpdateHierarchyViewsHook(self, view):
        self._hierarchyViews.add(view)

    def updateDatabaseViews(self):
        for v in self._databaseViews:
            v.update()

    def updateHierarchyViews(self):
        for v in self._hierarchyViews:
            v.update()

    def addLibrary(self, library):
        self._libraries.add(library)
        library.setParent(self)
        self._libraryNames[library.name()] = library
        self.updateDatabaseViews()

    def libraries(self):
        return self._libraries

    def libraryNames(self):
        return self._libraryNames.keys()

    def libraryByName(self, libraryName):
        if self._libraryNames.has_key(libraryName):
            return self._libraryNames[libraryName]
        else:
            return None

    def cellByName(self, libraryName, cellName):
        lib = self.libraryByName(libraryName)
        if lib:
            return lib.cellByName(cellName)
        else:
            return None

    def viewByName(self, libraryName, cellName, viewName):
        lib = self.libraryByName(libraryName)
        if lib:
            return lib.viewByName(cellName, viewName)
        else:
            return None

    def addDesign(self, design):
        self._designs.add(design)
        self.updateHierarchyViews()

    def removeDesign(self, design):
        self._designs.remove(design)
        self.updateHierarchyViews()

    def designs(self):
        return self._designs

    def setLayers(self, layers):
        self._layers = layers
        #self.updateViews()

    def layers(self):
        return self._layers


class Importer:
    def __init__(self, database):
        self._database = database
        self.reset()

    def reset(self):
        self._importedCellsView = set()
        self._reader = None
        self._fileList = []
        self._targetLibrary = 'work'
        self._overwrite = False
        self._recursive = True
