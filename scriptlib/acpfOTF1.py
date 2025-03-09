# ---------------------------------------------------------------------------
# acpfOTF1.py -- Build the boundaries
# DE James 02.2025
# Description: Build an ACPF HUC12 watershed file-geodatabase using traditional ACPF naming, i.e. acpf<HUC12>
#  - Create an output FGDB in project folder that will eventuall be archived for delivery
#  - Save the HUC12 boundary, bnd<HUC12>, to the ACPF FGDB
#  - Extract & assemble field boundary features from the US 48 collection: US48_ACPFfieldBoundaries > FB<HUC12>
#  - Union the HUC12 BND fc and the FB fc and buffer to 1km > buf<HUC12>
# ---------------------------------------------------------------------------
#
# 02.2025 - modify to work with ACPF On-The-Fly script set

#Import 
import arcpy
from arcpy import env
import sys, os
from .util import get_install_base

arcpy.env.overwriteOutput = True

#Local

def makeOutputDir(prjProcFolder, inHUC):
    # create the acpf HUC12 fgdb in the right place -- prjProcFolder
    #  all data are in Albers to begin with
    
    FileGDB = os.path.join(prjProcFolder, "acpf%s.gdb" % inHUC)
                    
    arcpy.AddMessage("")
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

 
def main(inHUC, prjProcFolder):
    base = get_install_base()
    HUC12status = base + r"\nationalACPF\ACPF_Basedata.gdb\US48_HUC12_2023"
    FBsrc =  base + r"\nationalACPF\ACPF_HUC2_Fields.gdb\US48_ACPFfieldBoundaries"

    FileGDB = makeOutputDir(prjProcFolder, inHUC)
    env.workspace = FileGDB

    ExtFBToHUC(HUC12status, FBsrc, inHUC, FileGDB)

    CreateFBfeatures(inHUC, FileGDB)
    
    env.workspace = ""
    env.extent = ""


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

