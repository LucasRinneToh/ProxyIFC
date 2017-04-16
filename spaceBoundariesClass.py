# -*- coding: utf-8 -*-
##Copyright 2017 Lucas Rinne Toh (lucasrinnetoh@gmail.com)
##
##This file is an example on working with PythonOCC and ifcopenshell for the purposes of working with ifc-proxy models.
##
######################
import ifcopenshell
import ifcopenshell.geom

import OCC.gp
import OCC.BRepBuilderAPI

import math
######################


def space_boundaries(_ifcSpace_,_ifcSite_):
    """
    This function takes a list of IFCspaces (flattened) and the ifcsite which the spaces are located in
    and finds the polylines for each bounding surface
    """
    
    #Get the location of the ifcSite
    siteLoc = _ifcSite_[0].ObjectPlacement.RelativePlacement.Location.Coordinates
    #Get the boundaries for the ifcspace
    spaceBounds = _ifcSpace_.BoundedBy
    #Get the origin point for the boundaries
    O = [bound.ConnectionGeometry.SurfaceOnRelatingElement.BasisSurface.Position.Location.Coordinates for bound in spaceBounds]
    
    
    def spaceElevation(_ifcSpace_):
        elevation = []
        for i in _ifcSpace_:
            elevation.append(i.Decomposes[0].RelatingObject.Elevation)
        return elevation
    elevate = spaceElevation(_ifcSpace_)        
    #Translate the origin point of boundaries relative to the site
    O_loc = [[((siteLoc[0]+O[i][j][0])/1000,(siteLoc[1]+O[i][j][1])/1000,(siteLoc[2]+O[i][j][2]+elevate[i])/1000) for j in range(len(O[i]))] for i in range(len(O))]
    #Get the Normal and Primary axis of the plane that the boundary is located on    
    N = [bound.ConnectionGeometry.SurfaceOnRelatingElement.BasisSurface.Position.Axis.DirectionRatios for bound in spaceBounds]
    H = [bound.ConnectionGeometry.SurfaceOnRelatingElement.BasisSurface.Position.RefDirection.DirectionRatios for bound in spaceBounds]
    #Translate the primary axis to an OCC point 
    ax1 = [OCC.gp.gp_Ax1((OCC.gp.gp_Pnt(O_loc[i][0],O_loc[i][1],O_loc[i][2])),(OCC.gp.gp_Dir(H[i][0],H[i][1],H[i][2]))) for i in range(len(O_loc))]
    #Define the rotation axis as OCC axis 
    rotAxis = [OCC.gp.gp_Ax1((OCC.gp.gp_Pnt(O_loc[i][0],O_loc[i][1],O_loc[i][2])),(OCC.gp.gp_Dir(N[i][0],N[i][1],N[i][2]))) for i in range(len(O_loc))]
    ax2 = ax1
    #Rotate the secondary axis into place
    [ax2[i].Rotate(rotAxis[i],math.pi/2) for i in range(len(ax1))]
    #Get the secondary axis for local planes
    K = [pnt.Direction().Coord() for pnt in ax2]
    #Get the points defining the boundaries
    connectGeometry = [bound.ConnectionGeometry for bound in spaceBounds]
    relElement = [geo.SurfaceOnRelatingElement for geo in connectGeometry]
    outBound = [elem.OuterBoundary for elem in relElement]
    outBoundPts = [bou.Points for bou in outBound]
    outBoundPtsCord = [[pt.Coordinates for pt in pts] for pts in outBoundPts]
    #Calculate the translated points and redefine them as OCC points
    globalXYZpts = [[(O_loc[i][0] + outBoundPtsCord[i][j][0]/1000 * H[i][0] + outBoundPtsCord[i][j][1]/1000 * K[i][0],O_loc[i][1] + outBoundPtsCord[i][j][0]/1000 * H[i][1] + outBoundPtsCord[i][j][1]/1000 * K[i][1],O_loc[i][2] + outBoundPtsCord[i][j][0]/1000 * H[i][2] + outBoundPtsCord[i][j][1]/1000 * K[i][2]) for j in range(len(outBoundPtsCord[i]))]for i in range(len(O_loc))]
    globalPts = [[OCC.gp.gp_Pnt(globalXYZpts[i][j][0],globalXYZpts[i][j][1],globalXYZpts[i][j][2]) for j in range(len(globalXYZpts[i]))] for i in range(len(globalXYZpts))]
    
    #Convert point lists into closed polygons
    def make_closed_polygon(*args):
        poly = OCC.BRepBuilderAPI.BRepBuilderAPI_MakePolygon()
        for pt in args:
            if isinstance(pt, list) or isinstance(pt, tuple):
                for i in pt:
                    poly.Add(i)
            else:
                poly.Add(pt)
        poly.Build()
        poly.Close()
        result = poly.Wire()
        return result

    poly = [make_closed_polygon(globalPts[i]) for i in range(len(globalPts))]
    return poly