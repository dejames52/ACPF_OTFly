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
import sys, os

#
arcpy.env.overwriteOutput = True

# Local

def makeOutputDir(procDir, prjName, HUC8, inHUC):
    # create the acpf HUC12 fgdb in the right place -- prjFolder
    
    prjFolder = os.path.join(procDir, prjName)
    fldrHUC8 = os.path.join(prjFolder, "huc%s" % HUC8)
    FileGDB = os.path.join(fldrHUC8, "acpf%s.gdb" % inHUC)
    
    #arcpy.AddMessage(fldrHUC8)
    #arcpy.AddMessage(FileGDB)
        
    if arcpy.Exists(prjFolder):
        arcpy.AddMessage("Exists %s" % prjFolder)
    else:
        arcpy.CreateFolder_management(procDir, prjName)

    if arcpy.Exists(fldrHUC8):
        arcpy.AddMessage("Exists %s" % fldrHUC8)
    else:
        arcpy.CreateFolder_management(prjFolder, "huc%s" % HUC8)
        
    if arcpy.Exists(FileGDB):
        arcpy.Delete_management(FileGDB)
                    
    arcpy.AddMessage("Create fileGDB: " + FileGDB)
    arcpy.CreateFileGDB_management(fldrHUC8, "acpf%s.gdb" % inHUC) 
    
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

    # make a feature layer of the CA field boundary FC and select fields
    arcpy.MakeFeatureLayer_management (FBsrc, "FBselect")
    arcpy.SelectLayerByLocation_management ("FBselect", "INTERSECT" , "HUCselect")
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
    
    # Fiddle the fields
    
    #arcpy.AddField_management(FBFrame, "FBndID", "text", "25")
    #arcpy.AddField_management(FBFrame, "Acres", "float", "12", "1") 
    #arcpy.AddField_management(FBFrame, "updateYr", "text", "6") 

    #Fstr = "\"F" + inHUC + "_!OBJECTID!\""
    #arcpy.CalculateField_management(FBFrame, "FBndID", Fstr, "PYTHON_9.3") 
    #arcpy.CalculateField_management(FBFrame, "Acres", "!shape.area@acres!", "PYTHON") 
    #arcpy.CalculateField_management(FBFrame, "updateYr", "2018", "PYTHON") 
    
    arcpy.management.AddIndex(FBFrame, ["FBndID"] , 'FBidx')


##------------------------------------------------------------------------------
##------------------------------------------------------------------------------

if __name__ == "__main__":
    
    inHUC = sys.argv[1]
    prjName = sys.argv[2]
        
    HUC12status = r"D:\ACPFdevelop\ACPF_OTFly\nationalACPF\ACPF2023_Basedata.gdb\US48_HUC12_2023"
    #FBsrc =  r"D:\ACPFdevelop\ACPF_OTFly\nationalACPF\ACPF2023_HUC2_Fields.gdb\US48_ACPFfieldBoundaries"
    FBsrc =  r"D:\ACPFdevelop\ACPF_OTFly\nationalACPF\ACPF2023_HUC2_Fields.gdb\US48_ACPFfieldBoundaries"
    procDir = r"D:\ACPFdevelop\ACPF_OTFly\processingDir"

    for row in arcpy.da.SearchCursor(HUC12status, ["HUC8","HUC12"], ''' "HUC12" = '%s' ''' %(inHUC) ):
        HUC8 = row[0]

        FileGDB = makeOutputDir(procDir,prjName, HUC8, inHUC)
        env.workspace = FileGDB

        ExtFBToHUC(HUC12status, FBsrc, inHUC, FileGDB)

        CreateFBfeatures(inHUC, FileGDB)
    

        env.workspace = ''


