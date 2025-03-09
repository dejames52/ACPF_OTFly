# -----------------------------------------------------------------------------
# acpfOTF7a.py -- Project to local UTM
# For each HUC12 fgdb, project all data to a local UTM, 
#
# May 2019 - Use a new HUC12 processing feature class (procHUC12_v2019)-- fields are now HUC8, HUC12
# March 2020 - Use a new HUC12 processing feature class (procHUC12_v2020)-- fields are HUC8, HUC12\
# Feb 2024 - Update to 2023 paths

# Import system modules
import arcpy
from arcpy import env
from arcpy.sa import *
import sys, string, os, time, shutil
from datetime import datetime
from util import get_install_base

# Set extensions & environments 
arcpy.CheckOutExtension("Spatial")
env.overwriteOutput = True


##------------------------------------------------------------------------------
##------------------------------------------------------------------------------


def fgdbProject(FGDBList, acpfHUC12, outProjectDir, prjArchiveFolder):
    # Select & go
    for FileGDB in FGDBList:
        env.workspace = FileGDB
        inHUC = os.path.split(FileGDB)[1][4:16]

        newFGDB = "acpf%s.gdb" % inHUC
        
        # grab the output UTM zone
        # WKID UTM = 269(10|11|12|13|14|15|16|17|18|19)
        rows =  arcpy.da.SearchCursor(acpfHUC12,["zonesUTM"], "\"HUC12\" = '%s'" %(inHUC),)
        for row in rows:
            outUTMz = int("269%s" %(row[0]))
        del row
        del rows            
        
        outSR = arcpy.SpatialReference(outUTMz)
            
        arcpy.CreateFileGDB_management(outProjectDir, newFGDB)
        outFGDB = os.path.join(outProjectDir, newFGDB)

        #------------------------------------------------------------
        arcpy.AddMessage("Projecting %s... " %(FileGDB))

        FeatureList = arcpy.ListFeatureClasses()
        RasterList = arcpy.ListRasters()
        TableList = arcpy.ListTables()

        # Project data
        # Features
        print(" Projecting %s feature classes" % len(FeatureList))
        arcpy.BatchProject_management(FeatureList, outFGDB, outSR)

        # Raster
        print(" Projecting %s rasters" % len(RasterList))
        for ras in RasterList:
            arcpy.ProjectRaster_management(ras, os.path.join(outFGDB, ras), outSR, "NEAREST")
            
        # Tables
        print(" Copying %s tables" % len(TableList))
        for tab in TableList:
            arcpy.TableToTable_conversion(tab, outFGDB, tab)

        #----------------
        # Final
        arcpy.management.Compact(outFGDB)
        
        arcpy.Copy_management(outFGDB,os.path.join(prjArchiveFolder,newFGDB))

        # add final indicies to the files in the outFGDB
        env.workspace = newFGDB
        arcpy.AddMessage(newFGDB)
        theFB = "FB%s" % inHUC
        LU_table = "LU6_%s" % inHUC
        CH_table = "CH_%s" % inHUC
        arcpy.management.AddIndex(theFB, "FBndID", "FBidx")
        arcpy.management.AddIndex(LU_table, "FBndID", "FBidx")
        arcpy.management.AddIndex(CH_table, "FBndID", "FBidx")
        
        soilsRas = "gSSURGO"
        sProf = "SoilProfile%s" % inHUC
        sHrz = "SurfHrz%s" % inHUC
        sTex = "SurfTex%s" % inHUC
        arcpy.management.AddIndex(soilsRas, "mukey", "muIdx")
        arcpy.management.AddIndex(sProf, "mukey", "muIdx")
        arcpy.management.AddIndex(sHrz, ["mukey","cokey"], "muIdx")
        arcpy.management.AddIndex(sTex, "cokey", "coIdx")

        

        del (FeatureList, RasterList, TableList, outSR)
        env.workspace = ""
            
                

##------------------------------------------------------------------------------
##------------------------------------------------------------------------------

def main(prjName, prjProcFolder, outProjectDir, prjArchiveFolder):
    base = get_install_base()
    acpfHUC12 = base + r"\nationalACPF\ACPF_Basedata.gdb\US48_HUC12_2023"
    
    arcpy.AddMessage("")
    arcpy.AddMessage("ProjectING...")
        
    env.workspace = prjProcFolder
    FGDBList = arcpy.ListWorkspaces("acpf*", "FileGDB")
    
    fgdbProject(FGDBList, acpfHUC12, outProjectDir, prjArchiveFolder)
    
    env.workspace = ""
    env.extent = ""    
    del(FGDBList)

            
if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])


        

    
