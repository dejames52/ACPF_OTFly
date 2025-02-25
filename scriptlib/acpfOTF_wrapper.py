# ---------------------------------------------------------------------------
# acpfOTF_wrapper.py -- MAke the calls to individul processing scripts to 
#  create an ACPF HUC12 FGDB. For use as a geoprocessing service script.
# Created on: 02.2025
#   DE James
#
# ---------------------------------------------------------------------------

# Import modules
import arcpy
import sys, os, shutil

#
from acpfOTF1 import main as main1
from acpfOTF2a import main as main2a
from acpfOTF2b import main as main2b
from acpfOTF3 import main as main3
from acpfOTF5 import main as main5
from acpfOTF7a import main as main7a
from acpfOTF8 import main as main8

# Local

##------------------------------------------------------------------------------
##------------------------------------------------------------------------------

def main(prjName, inHUC12list):
    prjName = sys.argv[1]
    inHUC12list = list(sys.argv[2].split(';'))   ## use a ';' seperator due to tool parameter output

    processingFolder = r"D:\ACPFdevelop\ACPF_OTFly\processingDir"
    prjProcFolder = os.path.join(processingFolder, prjName)

    if arcpy.Exists(prjProcFolder):
        shutil.rmtree(prjProcFolder)
        os.mkdir(prjProcFolder)
    else:
        os.mkdir(prjProcFolder)    
    
    outgoingFolder = r"D:\ACPFdevelop\ACPF_OTFly\outgoingDir"
    prjOutFolder = os.path.join(outgoingFolder, prjName)
    
    if arcpy.Exists(prjOutFolder):
        shutil.rmtree(prjOutFolder)
        os.mkdir(prjOutFolder)
    else:
        os.mkdir(prjOutFolder)    
    
    archiveFolder = r"D:\ACPFdevelop\ACPF_OTFly\archiveDir"
    prjArchiveFolder = os.path.join(archiveFolder, prjName)

    if arcpy.Exists(prjArchiveFolder):
        shutil.rmtree(prjArchiveFolder)
        os.mkdir(prjArchiveFolder)
    else:
        os.mkdir(prjArchiveFolder)    
    
    #-----------------------------------------    
    for inHUC in inHUC12list:
        if len(inHUC) == 12:
    
            print("")
            print("Processsing: %s" % inHUC)
            
            ##------------------------------------------------------------------------------
            # Select HUC12 BND, create FGDB, extract FB from Master, build BUF
            arcpy.AddMessage(prjProcFolder)
            main1(inHUC, prjProcFolder)
            
            ##------------------------------------------------------------------------------
            # Use BUF to extract 8 years of land use from nationalACPF
            main2a(inHUC, prjProcFolder)

            ##------------------------------------------------------------------------------
            # Use 8 years of land use to creatre crop history (CH) and alnd use tables (LU6)
            main2b(inHUC, prjProcFolder)

            
            ##------------------------------------------------------------------------------
            # Use BUF to extract soils data from nationalACPF
            main3(inHUC, prjProcFolder)

            ##------------------------------------------------------------------------------
            # Update Metadata
            main5(inHUC, prjProcFolder)

        else:
            print("Named Watershed is improperly formed: %s" % inHUC)


    ##########################################################################
    # Project to local UTM
    main7a(prjName, prjProcFolder, prjOutFolder, prjArchiveFolder)


    ##########################################################################
    # archive the project folder for download
    main8(archiveFolder,prjArchiveFolder,prjName)    
    


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

