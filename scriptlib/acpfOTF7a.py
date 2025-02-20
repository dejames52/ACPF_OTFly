# ACPF_ArchiveUTMzone.py
# For each HUC12 fgdb, project all data to a local UTM, place in the utmTemp folder
#  also, take the projected output and archive in a 7zip format for evenrual download
#
# May 2019 - Use a new HUC12 processing feature class (procHUC12_v2019)-- fields are now HUC8, HUC12
# March 2020 - Use a new HUC12 processing feature class (procHUC12_v2020)-- fields are HUC8, HUC12\
# Feb 2024 - Update to 2023 paths

# Import system modules
import arcpy
from arcpy import env
from arcpy.sa import *
from subprocess import call
import sys, string, os, time, shutil
from datetime import datetime

env.overwriteOutput = True

# Set extensions & environments 
arcpy.CheckOutExtension("Spatial")


##------------------------------------------------------------------------------
##------------------------------------------------------------------------------


def fgdbProject(FGDBList, outProjectDir):
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
        print("Projecting %s... " %(FileGDB))
        env.workspace = FileGDB

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
        # Cleanup
        del (FeatureList, RasterList, TableList, outSR)
        env.workspace = ""
            
                

##------------------------------------------------------------------------------
##------------------------------------------------------------------------------

if __name__ == "__main__":
    
    prjName = sys.argv[1]
    prjProcFolder = sys.argv[2]

    acpfHUC12 = r"D:\ACPFdevelop\ACPF_OTFly\nationalACPF\ACPF2023_Basedata.gdb\US48_HUC12_2023"
    outProjectDir = r"D:\ACPFdevelop\ACPF_OTFly\outgoingDir\%s" %(prjName)
    
    fCnt = 0 
        
    env.workspace = prjProcFolder
    FGDBList = arcpy.ListWorkspaces("acpf*", "FileGDB")
    
    if arcpy.Exists(outProjectDir):
        shutil.rmtree(outProjectDir)
        os.mkdir(outProjectDir)
    else:
        os.mkdir(outProjectDir)    
        
    fgdbProject(FGDBList, outProjectDir)
    
    del(FGDBList)


        

    
