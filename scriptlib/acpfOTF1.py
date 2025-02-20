# ---------------------------------------------------------------------------
# bld_HUCFB_feature.py
# Created on: 2012-03-20
#   DE James
# Description: Build a HUC12 watershed set of field boundary features based upon a
# list of Iowa counties that intersect the HUC12 boundary.
#  - Create an output FGeoDB in the H12_FBlib  070802051002
#  - Make a list of field boundary feature classes - i.e. FB_19101 -- to match county list
#  - Extract & assemble intermediate field boundary features that intersect the HUC12 boundary
#  - Buffer the HUC12 field boundaries to 1km for ancillary data processing
#  - Finalize the field boundarys:
#     + eliminate MAJORITY 2009 LU that IS NULL
#     + eliminate polygons lt 2.5 acres
#     + remove artifact columns
#     + add and populate FBndID and Acres fields
# ---------------------------------------------------------------------------
#
# 09/2015 - Add union of FB & BND to create 1,000m buffer aka buf

# Import arcpy module
import arcpy
from arcpy import env
import sys, os, shutil

arcpy.env.overwriteOutput = True

# Local

def makeOutputDir(prjProcFolder, inHUC):
    # create the acpf HUC12 fgdb in the right place -- prjProcFolder
    #  all data are in Albers to begin with
    
    FileGDB = os.path.join(prjProcFolder, "acpf%s.gdb" % inHUC)
                    
    arcpy.AddMessage("Create fileGDB: " + FileGDB)
    arcpy.CreateFileGDB_management(prjProcFolder, "acpf%s.gdb" % inHUC) 
    
    return(FileGDB)
    
    
def ExtFBToHUC(HUC12status, FBsrc, inHUC, FileGDB):
    # for the HUC12, save a copy of the bnd to the HUC12 fgdb;
    # extract those fields that intersect the Bnd -- Append; Buffer
    # the assembled field boundaries by 1,000m as the Buf.
    
    theBnd = "bnd%s" % inHUC
    theFB = "FB%s" % inHUC
    theBuf = "buf%s" % inHUC
        
    # Make a feature layer of the HUC12 submitted
    arcpy.AddMessage("---Assemble the field boundary features...")
    arcpy.MakeFeatureLayer_management (HUC12status, "HUCselect", "\"HUC12\" = '" + inHUC + "'")
    arcpy.CopyFeatures_management("HUCselect", theBnd)

    # make a feature layer of the field boundary FC and select fields
    arcpy.MakeFeatureLayer_management (FBsrc, "FBselect")
    arcpy.SelectLayerByLocation_management("FBselect", "HAVE_THEIR_CENTER_IN" , "HUCselect")
    arcpy.CopyFeatures_management("FBselect", theFB)
    
    arcpy.AddMessage('---Buffering...')
    toBuff = "toBuff"
    arcpy.Union_analysis([theFB, theBnd], toBuff, "ONLY_FID",1, "NO_GAPS")
    arcpy.Buffer_analysis(toBuff, theBuf, "1000 meters", "FULL", "", "ALL")

    arcpy.Delete_management("HUCselect")
    arcpy.Delete_management("FBselect")
    arcpy.Delete_management(toBuff)
    del(theBnd, theFB, theBuf)

    
def CreateFBfeatures(inHUC, FileGDB):
    # Create a Feature Layer from the source
    
    arcpy.AddMessage("---Finalize features...")
    FBFrame = "FB%s" % inHUC
    
    arcpy.management.AddIndex(FBFrame, ["FBndID"] , 'FBidx')


##------------------------------------------------------------------------------
##------------------------------------------------------------------------------

 
def main(inHUC, prjName):
        
    HUC12status = r"D:\ACPFdevelop\ACPF_OTFly\nationalACPF\ACPF2023_Basedata.gdb\US48_HUC12_2023"
    FBsrc =  r"D:\ACPFdevelop\ACPF_OTFly\nationalACPF\ACPF2023_HUC2_Fields.gdb\US48_ACPFfieldBoundaries"
    processingFolder = r"D:\ACPFdevelop\ACPF_OTFly\processingDir"
    prjProcFolder = os.path.join(processingFolder, prjName)


    FileGDB = makeOutputDir(prjProcFolder, inHUC)
    env.workspace = FileGDB

    ExtFBToHUC(HUC12status, FBsrc, inHUC, FileGDB)

    CreateFBfeatures(inHUC, FileGDB)
    
    env.workspace = ''


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

