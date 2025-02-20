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
        
    ProcDir = r"D:\Data\ACPFdevelop\CAbuildout\UTMtemp"
        
    d12 = 1
    env.workspace = ProcDir
    
    Wlist = arcpy.ListWorkspaces("*", "FileGDB")
    for gdb in Wlist:
        arcpy.management.Compact(gdb)
        print("fgdb %s: %s" %(gdb, d12))
    
        d12 += 1
    print("Total: %s" % d12)




