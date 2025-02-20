# -----------------------------------------------------------------------------
# BULK_KS_Landuse0614.py
#
#  Create the tables in the HUC12 FileGDB that contains field-level landuse
#  information as derived from the NASS Crop Data Layer including the Crop
#  History table (CH_*) and the Six-year Land Use table (LU6_*)- 2015-2020.
#  Included are:
#   - crop rotation string (CropRotatn) using a single letter to represent
#     each year's majpority crop type..additonally, if the majority is Corn
#     or soyBean and the majority is LT 75%, check to see if the second
#     highest class is soyBean or Corn, if true assign as corn/soybean (D)
#   - crop rotation summary (CropSumry) a string using the single letter
#     of the majority crop followed by the number of occurances of that ctop
#     over the rotation span
#   - a count of the number of occurances of corn-after-corn 'CC' in the
#     crop rotation string - CCCount
#   - a count of the number of occurances of the majority crop percent of the
#     field less than 75% - MixCount
#   - for each year in the span, the majority crop (majYR) and the percent
#     of the field that it represents (pctYR)
#   - a General Land Use assignment based on the 6-yr crop rotation string and
#     the other derived fields.
# -----------------------------------------------------------------------------
#  Orginal coding: D.James 08/2012
#    - 07/2013: update to 6-year rotation
#    - 11/2013: update to extend Pasture to include pasture woodlots; add class
#        for flood-prone cropland (1 year of Ag field as water)
#    - 04/2014: updated to ad the full crop history to 2000, table name: CH_inHUC
#    - 04/2014: made the full commitment to in_memory processing, 
#        reduce ptroc time by 60%!
#    - 09/2015: restructure the prograam to include Kansas data; expand rotations
#        to include wheat and stand-alone soybeans
#    - 02/2016: 2015 field season will include KS data...as a result
#       + remove the mixed field assigment for corn/soybeans to 'D'...let it roll
#       + use a new CDL lookup table - ACPF2015_CDLlkup
#    - 02/2018: 2017 field season will include 8,000+ watersheds
#       + move to use the generic land use assignment method, 
#       + use a new CDL lookup table - ACPF2017_CDLlkup
#     - 04/2018: add test for updating to new landuse schema or reprocessing to new LU schema
#     - 12/2021: minor updtes to support processing using puthon 3.x (ArcGIS Pro)
#       + use a new CDL lookup table - ACPF_CDLlkup_2021 -- moved to all upper case
#       + used the state-wide CA data for testing; 2,307 HUC12 watersheds
# -----------------------------------------------------------------------------

# Import system modules
import arcpy
from arcpy import env
from arcpy.sa import *

import sys, string, os, time

env.overwriteOutput = True

# Set extensions & environments
arcpy.CheckOutExtension("Spatial")

#----------------------------------------------------------------------------------------------
# Remove early CDL data to trim to 8 years as core - 7/2024

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
        #arcpy.AddMessage("")
        env.snapRaster = CDL_Data
        env.extent = "buf" + inHUC
        bufMask = "buf" + inHUC
            
        wsCDL = ExtractByMask(CDL_Data, bufMask)
        wsCDL.save(theLUras)
        
    del(CDL_Data,theLUras,bufMask)
                   
   
##------------------------------------------------------------------------------
##------------------------------------------------------------------------------

if __name__ == "__main__":

    inHUC = sys.argv[1]
    prjProcFolder = sys.argv[2]

    # Input data
    HUC12status = r"D:\ACPFdevelop\ACPF_OTFly\nationalACPF\ACPF2023_Basedata.gdb\US48_HUC12_2023"
    CDLroot = r"D:\ACPFdevelop\ACPF_OTFly\nationalACPF\ACPF_LandUse\US_CDL20"

    # Years
    YrList = ["16","17","18","19","20","21","22","23"]
    
    FileGDB = prjProcFolder + "\\acpf" + inHUC + ".gdb"

    arcpy.AddMessage("---" + FileGDB)

    env.workspace = FileGDB
    env.extent = "buf" + inHUC
    
    AddCDLByYear(CDLroot, inHUC, YrList)
    
    env.workspace = ""
    env.extent = ""
    del [inHUC, prjProcFolder, FileGDB]

