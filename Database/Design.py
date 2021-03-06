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

#print 'Design in'

#from Primitives import *
#from Cells import *
#from Attributes import *
from xml.etree import ElementTree as et

#print 'Design out'

class DesignUnit():
    def __init__(self, instance, parentDesignUnit):
        self._instance = instance
        self._parentDesignUnit = parentDesignUnit
        self._name = instance.name
        self._childDesignUnits = {} #set()
        self._sortedChildDesignUnits = None
        self._design = parentDesignUnit.design
        self._scene = None
        #self._index = Index()
        self.cellView.designUnitAdded(self)
        parentDesignUnit.childDesignUnitAdded(self)
 
    @property
    def name(self):
        return self._name

    @property
    def path(self):
        parent = self.parentDesignUnit
        if parent.parentDesignUnit:
            return parent.path + '.' + self.name
        return parent.path + ':' + self.name

    @property
    def childDesignUnits(self):
        """
        Get a dictionary of child design units (instance->designUnit)
        The dictionary is computed lazily by this function
        (so that it descends down the hierarchy only when the user wants to see it)
        and is cached for future invocations.
        """
        if len(self._childDesignUnits) > 0:   #cache
            return self._childDesignUnits
        schematic = self.cellView.cell.cellViewByName("schematic")
        
        if schematic:
            for i in schematic.instances:
                DesignUnit(i, self) # it should add itself to parent design unit
                #self._childDesignUnits[i] = DesignUnit(i, self)
        return self._childDesignUnits

    @property
    def sortedChildDesignUnits(self):
        """Cached list of designs units sorted by name."""
        if not self._sortedChildDesignUnits:
            self._sortedChildDesignUnits = sorted(self.childDesignUnits.values(), lambda a, b: cmp(a.instance.instanceCellName.lower(), b.instance.instanceCellName.lower()))
        #print self._sortedChildDesignUnits
        return self._sortedChildDesignUnits

    @property
    def parentDesignUnit(self):
        return self._parentDesignUnit

    @property
    def scene(self):
        return self._scene
    
    @property
    def instance(self):
        return self._instance

    @property
    def design(self):
        return self._design

    @property
    def cellView(self):
        return self.instance.instanceCell.implementation
        #schematic = self.instance.instanceCell.cellViewByName('schematic')
        #if schematic:
        #    return schematic
        #else:
        #    return self.instance.instanceCellView

    def sceneAdded(self, scene):
        self._scene = scene
        for e in self.cellView.elems:
            e.addToView(scene)
        
    def childDesignUnitAdded(self, designUnit):
        self._childDesignUnits[designUnit.instance] = designUnit
        self._sortedChildDesignUnits = None
        
    def childDesignUnitRemoved(self, designUnit):
        del self._childDesignUnits[designUnit.instance]
        self._sortedChildDesignUnits = None

    def updateItem(self):
        if self.scene:
            self.scene.updateItem()

    def addInstance(self, instance):
        #designUnit = self._childDesignUnits.get(instance)
        #if not designUnit:
        designUnit = DesignUnit(instance, self)
        self.childDesignUnits[instance] = designUnit
        self.scene.addInstance(designUnit)
    
    def removeInstance(self, instance):
        designUnit = self._childDesignUnits.get(instance)
        if designUnit:
            self.scene.removeInstance(designUnit)
            del self.childDesignUnits[instance]
    
    def remove(self):
        for co in self.childDesignUnits.values():
            co.remove()
        if self.scene:
            self.scene.instanceRemoved()
            self.cellView.DesignUnitRemoved(self)
        self.parentDesignUnit.childDesignUnitRemoved(self)
        
    def __repr__(self):
        return "<DesignUnit '" + self.path + "'>"

class Design(DesignUnit):
    def __init__(self, cellView, designs):
        self._cellView = cellView
        self._designs = designs
        self._name = cellView.path
        self._childDesignUnits = {}
        self._sortedChildDesignUnits = None
        self._scene = None
        self.cellView.designUnitAdded(self)
        designs.designAdded(self)
            
    @property
    def path(self):
        return self.cellView.path

    @property
    def cellView(self):
        return self._cellView

    @property
    def design(self):
        return self

    @property
    def parentDesignUnit(self):
        return None
    
    @property
    def designs(self):
        return self._designs
        
    def sceneAdded(self, scene):
        self._scene = scene
        for e in self.cellView.elems:
            e.addToView(scene)
            
    def sceneRemoved(self):
        self._scene = None
        self.cellView.designUnitRemoved(self)

    def cellViewRemoved(self):
        if self.scene:
            self.scene.designRemoved()
            
    def remove(self):
        for co in self.childDesignUnits.values():
            co.remove()
        if self.scene:
            self.scene.designRemoved()
        self.cellView.designUnitRemoved(self)
        self.designs.designRemoved(self)

    def __repr__(self):
        return "<Design '" + self.path + "'>"

class Designs():
    def __init__(self, database):
        self._database = database
        self._designs = set()
        self._designNames = {}
        self._hierarchyViews = set()
        self._sortedDesigns = []
       
    @property
    def designs(self):
        return self._designs
    
    @property
    def designNames(self):
        return self._designNames
    
    @property
    def database(self):
        return self._database
        
    @property
    def hierarchyViews(self):
        return self._hierarchyViews

    @property
    def sortedDesigns(self):
        """Preserve the order the designs were added."""
        return self._sortedDesigns

    def installUpdateHierarchyViewsHook(self, view):
        self.hierarchyViews.add(view)

    def updateHierarchyViews(self):
        "Notify views that the design hierarchy layout has changed"
        for v in self.hierarchyViews:
            v.update()

    def designAdded(self, design):
        #self.add(design)
        self.designs.add(design)
        self.designNames[design.name] = design
        #self.updateHierarchyViews()
        self._sortedDesigns.append(design)
        self.database.requestDeferredProcessing(self)

    def designRemoved(self, design):
        #self.remove(design)
        self.designs.remove(design)
        del self.designNames[design.name]
        #self.updateHierarchyViews()
        del self._sortedDesigns[self._sortedDesigns.index(design)]
        self.database.requestDeferredProcessing(self)
        
    def designUnitByPath(self, pathName):
        if pathName in self.designNames:
            return self.designNames[pathName]
        
    def runDeferredProcess(self):
        """Runs deferred processes."""
        self.updateHierarchyViews()
        
    def close(self):
        for d in list(self.designs):
            d.remove()
        
    def __repr__(self):
        return "<Designs " + repr(self.sortedDesigns) + ">"
