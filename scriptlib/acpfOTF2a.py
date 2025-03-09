# -----------------------------------------------------------------------------
# acpfOTF2a.py -- Land Use 1
#
#  Extract a HUC12 watersheds lNASS CDL landuse raster for each of the selected years.
#   This is a subset of the original bulk processing script for land use and is limited
#   to the extraction by the buffered boundary feature class, buf<HUC12>. The sister script,
#   acpfOTF2b.py, adds ACPF attribution, created the by-field crop history (CH) table and
#   the by-field land use summary table (LU6).
# -----------------------------------------------------------------------------
#  Orginal coding: D.James 08/2012
#  02.2025 - modify to work with ACPF On-The-Fly script set
# -----------------------------------------------------------------------------

# Import system modules
import arcpy
from arcpy import env
from arcpy.sa import *

import sys, string, os, time
from util import get_install_base

# Set extensions & environments
arcpy.CheckOutExtension("Spatial")
env.overwriteOutput = True

#----------------------------------------------------------------------------------------------
# Remove early CDL data to trim to 8 years as core - 7/2024
# Add 2024, remove 2016??

def DeleteCDLByYear(YrDelete):
    # Process the new framework through each year
    arcpy.AddMessage("...deleting %s" % YrDelete)
    for Yr in YrDelete:
        theLUdelete = "wsCDL20" + Yr
        if arcpy.Exists(theLUdelete):
            arcpy.Delete_management(theLUdelete)


#----------------------------------------------------------------------------------------------
# Extract the CDL to the buffered boundary (buf) for each year

def AddCDLByYear(CDLroot, inHUC, YrList):
    for Yr in YrList:

        CDL_Data = CDLroot + Yr + ".tif"
        theLUras = "wsCDL20" + Yr
 
        arcpy.AddMessage("Extract 20%s by mask" % Yr)
        env.snapRaster = CDL_Data
        env.extent = "buf" + inHUC
        bufMask = "buf" + inHUC
            
        wsCDL = ExtractByMask(CDL_Data, bufMask)
        wsCDL.save(theLUras)
        
    del(CDL_Data,theLUras,bufMask)
                   
   
##------------------------------------------------------------------------------
##------------------------------------------------------------------------------


def main(inHUC, prjProcFolder):

    # Input data
    base = get_install_base()
    HUC12status = base + r"\nationalACPF\ACPF_Basedata.gdb\US48_HUC12_2023"
    CDLroot = base + r"\nationalACPF\ACPF_LandUse\US_CDL20"

    # Years
    YrList = ["17","18","19","20","21","22","23","24"]
    
    FileGDB = prjProcFolder + "\\acpf" + inHUC + ".gdb"

    arcpy.AddMessage("")
    arcpy.AddMessage("Land use: " + FileGDB)

    env.workspace = FileGDB
    env.extent = "buf" + inHUC
    
    AddCDLByYear(CDLroot, inHUC, YrList)
    
    env.workspace = ""
    env.extent = ""
    del [inHUC, prjProcFolder, FileGDB]

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
