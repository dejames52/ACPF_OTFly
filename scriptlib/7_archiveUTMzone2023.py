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
import sys, string, os, time
from datetime import datetime

env.overwriteOutput = True

# Set extensions & environments 
arcpy.CheckOutExtension("Spatial")


##------------------------------------------------------------------------------
##------------------------------------------------------------------------------

def Archive7Z(outFGDB, inHUC):
    arcName = r"D:\Data\ACPFdevelop\CAbuildout\CA_HUC12_7zLib\acpf_huc%s.7z" %(inHUC)
    if os.path.exists(arcName):
        os.remove(arcName)
                    
    callStr = '"C:\\Program Files\\7-Zip\\7z.exe" a %s %s' %(arcName, outFGDB )
                    
    call(callStr, shell=True, stdout=open(os.devnull, 'wb'))
    
    del (arcName, callStr)

        

def fgdbProject(FGDBList, outDirectory):
    # Select & go
    for FileGDB in FGDBList:
        #print(" fgdb: " + FileGDB)
        env.workspace = FileGDB
        inHUC = os.path.split(FileGDB)[1][4:16]

        newFGDB = "acpf%s.gdb" % inHUC
        
        # grab the output UTM zone
        # WKID UTM = 269(14|15|16|17)
        rows =  arcpy.da.SearchCursor(acpfHUC12,["zoneUTM"], "\"HUC12\" = '%s'" %(inHUC),)
        for row in rows:
            outUTMz = int("269%s" %(row[0]))
        del row
        del rows            
        
        outSR = arcpy.SpatialReference(outUTMz)
                    
        if arcpy.Exists(os.path.join(outDirectory, newFGDB)):
            arcpy.Delete_management(os.path.join(outDirectory, newFGDB))
            
        arcpy.CreateFileGDB_management(outDirectory, newFGDB)
        outFGDB = os.path.join(outDirectory, newFGDB)


        print("Projecting %s... " %(FileGDB))
        env.workspace = FileGDB

        FeatureList = arcpy.ListFeatureClasses()
        RasterList = arcpy.ListRasters()
        TableList = arcpy.ListTables()

        #-------------------------------------------------------------------------------------
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

        
            
        #-------------------------------------------------------------------------------------
        # Archive
        print("Archiving...")
        Archive7Z(outFGDB, inHUC)
        
       
        #-------------------------------------------------------------------------------------
        # Keep Trak
        UpdStatus(acpfHUC12, inHUC)

        
        #----------------
        # Cleanup
        del (inHUC, FeatureList, RasterList, TableList, outFGDB, outSR)
            
                

##------------------------------------------------------------------------------
##------------------------------------------------------------------------------

if __name__ == "__main__":

    ProcDir = r"D:\Data\ACPFdevelop\CAbuildout\CAHUC12lib"
    acpfHUC12 = r"D:\Data\ACPFproc\ACPF2023\acpf_Database\ACPF_Basedata.gdb\procHUC12_CA"
    outDirectory = r"D:\Data\ACPFdevelop\CAbuildout\UTMtemp" 
    

    fCnt = 0 
        

    for row in arcpy.da.SearchCursor(HUC12status, ["HUC8","HUC12"], ''' "HUC12" = '%s' ''' %(inHUC) ):
        HUC8 = str(row[0])

        ProcDir = acpfDir + "\\huc" + HUC8
        FileGDB = ProcDir + "\\acpf" + inHUC + ".gdb"
            
        fgdbProject(FGDBList, outDirectory)

        
        del(FGDBList,HUC8)


        

    
