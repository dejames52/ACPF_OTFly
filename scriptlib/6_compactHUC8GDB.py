# compact_fgdb.py
# 
#
# Import system modules
import arcpy
from arcpy import env
from arcpy.sa import *

import sys, string, os

env.overwriteOutput = True

# Set extensions & environments 
arcpy.CheckOutExtension("Spatial")


##------------------------------------------------------------------------------
##------------------------------------------------------------------------------

if __name__ == "__main__":
        
    ProcDir = r"D:\Data\ACPFdevelop\CAbuildout\CAHUC12lib"
        
    d12 = 0
    HUC8Paths = [os.path.join(ProcDir,fn) for fn in next(os.walk(ProcDir))[1]]
    
    for HUC8Dir in HUC8Paths:
        env.workspace = HUC8Dir
        
        Wlist = arcpy.ListWorkspaces("*", "FileGDB")
        for gdb in Wlist:
            arcpy.management.Compact(gdb)
            print("fgdb %s: %s" %(gdb, d12))
        
            d12 = d12 + 1
    print("Total: %s" % d12)




