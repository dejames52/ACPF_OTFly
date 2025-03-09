# ---------------------------------------------------------------------------
# acpfOTF3.py -- Soils data
# Created on: 04.2015  DE James
#
# A component of the ACPF On-The-Fly thats extracts the soils data for an 
#  individual watershed; the gSSURGO 10m rtaster and three soils tables -
#  SoilsProfile, SurfaceHorizon, and SurfaceTexture
#
#  02/20 - Add IA CornSuitabilityRating field to MUAGGATT collection as IACORNSR
#  03/21 - Add OCprodIdx, OCprodIdxSrc to MUAGGATT using NCCPIall (*100) field 
#          populate initially.Follow on to populate with other state-based productivity 
#          indicies to support the ACPF Financial Analysis tool.
#  03/21 - Remove all NCCPI subclasses, Corn, Soy, Cotton, Small Grain
#  02/2025: modify to work with ACPF On-The-Fly script set
# ---------------------------------------------------------------------------

# Import arcpy module
import arcpy
from arcpy import env
from arcpy.sa import *
import sys, os
from util import get_install_base

# Set extensions & environments 
arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("Spatial")

# Local

def ext_gSSURGO(inHUC, ACPFsoilRas, FileGDB):

    if arcpy.Exists("%s\\gSSURGO" %(FileGDB)):
        arcpy.Delete_management("%s\\gSSURGO" %(FileGDB))
                
    print("---extract gSSURGO")
    env.extent = FileGDB + "\\buf" + inHUC
    
    gSSRUGOByMask = ExtractByMask(ACPFsoilRas, FileGDB + "\\buf" + inHUC)  
    gSSRUGOByMask.save("%s\\gSSURGO" %(FileGDB))
    
    arcpy.AddField_management(gSSRUGOByMask, "mukey", "text", 30)
    arcpy.CalculateField_management(gSSRUGOByMask, "mukey", '!VALUE!', "PYTHON_9.3")

    arcpy.BuildPyramids_management(gSSRUGOByMask)
    #arcpy.AddIndex_management(gSSRUGOByMask, "mukey", "muIdx", "UNIQUE", "NON_ASCENDING")
    
    muRows = "HUC12MUROWS"
    arcpy.CopyRows_management(gSSRUGOByMask, muRows)
    
    return(muRows)
    
    
def makeACPFsoilsTables(ACPFsoilDB, muRows, FileGDB,inHUC):

    print("---extract tables")
    ## ------------- Soil Profile  ------------- 

    if arcpy.Exists( "SoilProfile%s" % inHUC):
        arcpy.Delete_management("SoilProfile%s" % inHUC)

    SoilPROFTable = ACPFsoilDB + "\\usACPF_SoilProfilesTable"
    profileList = ["aws0_20","aws20_50","aws50_100","soc0_20","soc20_50","soc50_100","OM0_100","KSat50_150","Coarse50_150"]
    
    arcpy.TableToTable_conversion(muRows, FileGDB, "SoilProfile%s" % inHUC)
    arcpy.JoinField_management("SoilProfile%s" %(inHUC), "mukey", SoilPROFTable, "mukey", profileList) 
    arcpy.DeleteField_management("SoilProfile%s" %(inHUC), ["Value", "Count","gSSURGOversion"] )
    #arcpy.AddIndex_management("SoilProfile%s" %(inHUC), "mukey", "muIdx", "UNIQUE", "NON_ASCENDING")

    
    ## ------------- Surface Horizon  -------------
    if arcpy.Exists( "SurfHrz%s" % inHUC):
        arcpy.Delete_management("SurfHrz%s" % inHUC)
        
    SurfHorizonTable = ACPFsoilDB + "\\usACPF_SurfHorizonTable"
    HrzList = ["cokey","chkey","CompPct","CompName","CompKind","TaxCls","HrzThick","OM","KSat","Kffact","Kwfact","totalSand","totalSilt","totalClay","VFSand","DBthirdbar"]

    arcpy.TableToTable_conversion(muRows, FileGDB,"SurfHrz%s" %( inHUC))
    arcpy.JoinField_management("SurfHrz%s"  %(inHUC), "mukey", SurfHorizonTable, "mukey", HrzList) 
    arcpy.DeleteField_management("SurfHrz%s"  %(inHUC), ["Value", "Count","gSSURGOversion"]) 
    #arcpy.AddIndex_management("SurfHrz%s" %(inHUC), ["mukey","cokey"], "muIdx", "UNIQUE", "NON_ASCENDING")
      
    
    ## ------------- Surface Texture  ------------- 
    if arcpy.Exists( "SurfTex%s" % inHUC):
        arcpy.Delete_management("SurfTex%s" % inHUC)
        
    SurfTextureTable = ACPFsoilDB + "\\usACPF_SurfTextureTable"
    TexList = ["comppct_r","Texture","TextCls","ParMatGrp","ParMatKind"]
    
    arcpy.TableToTable_conversion(muRows, FileGDB, "SurfTex%s"  % inHUC)   
    arcpy.JoinField_management("SurfTex%s" %(inHUC), "mukey", SurfHorizonTable, "mukey", ["cokey"]) 
    arcpy.JoinField_management("SurfTex%s" %(inHUC), "cokey", SurfTextureTable, "cokey", TexList) 
    arcpy.DeleteField_management("SurfTex%s" %(inHUC), ["Value", "Count", "mukey","gSSURGOversion"]) 
    #arcpy.AddIndex_management("SurfTex%s" %(inHUC), "cokey", "coIdx", "UNIQUE", "NON_ASCENDING")
    

    ## ------------- MUAgg  ------------- 
    MUAggTable = ACPFsoilDB + "\\usACPF_MUAggTable"
    muaggList = ["gSSURGOversion","MUsymbol","MUname","WTDepAprJun","FloodFreq","PondFreq","DrainCls","DrainClsWet","HydroGrp","Hydric","OCprodIdx","OCprodIdxSrc","NCCPIall","RootZnDepth","RootZnAWS","Droughty","PotWetandSoil"]

    arcpy.JoinField_management(FileGDB + "\\gSSURGO", "mukey", MUAggTable, "mukey", muaggList)
    #arcpy.AddIndex_management(FileGDB + "\\gSSURGO", "mukey", "muIdx", "UNIQUE", "NON_ASCENDING")


    #Cleanup    
    if arcpy.Exists( muRows):
        arcpy.Delete_management(muRows)
    
    del(muaggList,profileList,TexList,HrzList)



##------------------------------------------------------------------------------
##------------------------------------------------------------------------------
    
def main(inHUC, prjProcFolder):
    base = get_install_base()
    HUC12status = base + r"\nationalACPF\ACPF_Basedata.gdb\US48_HUC12_2023"
    ACPFsoilRas =  base + r"\nationalACPF\ACPF_Soils\US_gSSURGOmosaic.gdb\ua4810m"
    ACPFsoilDB =  base + r"\nationalACPF\ACPF_Soils\US_ACPFsoilsTables.gdb"

    env.snapRaster = ACPFsoilRas
    
    # process  

    FileGDB = prjProcFolder + "\\acpf" + inHUC + ".gdb"

    arcpy.AddMessage("")
    arcpy.AddMessage("Soils: " + FileGDB)

    env.workspace = FileGDB
    env.extent = "buf" + inHUC

    muRows = ext_gSSURGO(inHUC, ACPFsoilRas, FileGDB)
            
    makeACPFsoilsTables(ACPFsoilDB, muRows, FileGDB ,inHUC)
                
    arcpy.management.Compact(FileGDB)
    env.workspace = ""
    env.extent = ""

            
if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

