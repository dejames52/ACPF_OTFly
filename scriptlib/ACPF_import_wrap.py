# ---------------------------------------------------------------------------
# ACPF\ACPF2017\scriptLib\extractFromTables_ACPF2_gSSURGO.py
# Created on: 04.2015
#   DE James
#
#  02/20 - Add IA CornSuitabilityRating field to MUAGGATT collection as IACORNSR
#  03/21 - Add OCprodIdx, OCprodIdxSrc to MUAGGATT using NCCPIall (*100) field 
#          populate initially.Follow on to populate with other state-based productivity 
#          indicies to support the ACPF Financial Analysis tool.
#  03/21 - Remove all NCCPI subclasses, Corn, Soy, Cotton, Small Grain
#  01/22 - Add new field in thegSSURGO.VAT, 'gSSURGOversion', to track the version of  
#          soils data. This field will reference the NRCS declared version using the fiscal 
#           year in which the data were published. e.g. 2022 for data published in October 2021.
# ---------------------------------------------------------------------------

# Import modules
import arcpy
import subprocess
import sys, os, shutil

from .acpfOTF1 import main as main1
from .acpfOTF2a import main as main2a

#arcpy.SetLogHistory(False)
# Local

##------------------------------------------------------------------------------
##------------------------------------------------------------------------------


def main(prjName, inHUC12list):
    prjName = sys.argv[1]
    inHUC12list = list(sys.argv[2].split(','))
    #inHUC12list = inHUC12list.replace(" ", "")
    print(inHUC12list)

    processingFolder = r"D:\ACPFdevelop\ACPF_OTFly\processingDir"
    prjProcFolder = os.path.join(processingFolder, prjName)
    
    outgoingFolder = r"D:\ACPFdevelop\ACPF_OTFly\outgoingDir"
    prjOutFolder = os.path.join(outgoingFolder, prjName)
    
    archiveFolder = r"D:\ACPFdevelop\ACPF_OTFly\archiveDir"

    if arcpy.Exists(prjProcFolder):
        shutil.rmtree(prjProcFolder)
        os.mkdir(prjProcFolder)
    else:
        os.mkdir(prjProcFolder)    
    
    #-----------------------------------------    
    for inHUC in inHUC12list:
        if len(inHUC) == 12:
    
            print("Processsing: %s" % inHUC)
            
            ##------------------------------------------------------------------------------
            # Select HUC12 BND, create FGDB, extract FB from Master, build BUF
            arcpy.AddMessage(prjProcFolder)
            main1(inHUC, prjName)
            
            ##------------------------------------------------------------------------------
            # Use BUF to extract 8 years of land use from nationalACPF
            main2a(inHUC, prjProcFolder)

            ##------------------------------------------------------------------------------
            # Use BUF to extract 8 years of land use from nationalACPF
            callstr3 = "python D:\\ACPFdevelop\\ACPF_OTFly\\scriptlib\\2b_assignHUC12_byFieldLandUse.py %s %s" %(inHUC,prjProcFolder)
            proc3 = subprocess.run(callstr3, shell=True)
            
            if proc3.returncode == 0:
                print('LU2 OK')
            else:
                print('{0} procLU failed!'.format(inHUC))
                sys.exit()

            del(proc3)
            
            ##------------------------------------------------------------------------------
            # Use BUF to extract soils data from nationalACPF
            callstr4 = "python D:\\ACPFdevelop\\ACPF_OTFly\\scriptlib\\3_extract_ACPFgSSURGO.py %s %s" %(inHUC,prjProcFolder)
            proc4 = subprocess.run(callstr4, shell=True)
            
            if proc4.returncode == 0:
                print('gSSURGO OK')
            else:
                print('{0} soils failed!'.format(inHUC))
                sys.exit()

            del(proc4)

            ##------------------------------------------------------------------------------
            # Update Metadata
            callstr5 = "python D:\\ACPFdevelop\\ACPF_OTFly\\scriptlib\\5_ACPF_MetadataImporterPro.py %s %s" %(inHUC,prjProcFolder)
            proc5 = subprocess.run(callstr5, shell=True)
            
            if proc5.returncode == 0:
                print('metadata OK')
            else:
                print('{0} meta failed!'.format(inHUC))
                sys.exit()
                
            del(proc5)
                
            del(inHUC)
        else:
            print("Named Watershed is improperly formed: %s" % inHUC)


    ##########################################################################
    # Project
    callstr6 = "python D:\\ACPFdevelop\\ACPF_OTFly\\scriptlib\\7a_prjUTMzone.py %s %s" %(prjName, prjProcFolder)
    proc6 = subprocess.run(callstr6, shell=True)
    
    if proc6.returncode == 0:
        print('Project OK')
    else:
        print('{0} Project FGDBs failed!'.format(prjName))
        sys.exit()
        
    del(proc6)



    ##########################################################################
    # archive the project folder for download
    arcName = r"%s\acpf_archive%s.7z" %(archiveFolder,prjName)
    if os.path.exists(arcName):
        os.remove(arcName)
                    
    callStrA = '"C:\\Program Files\\7-Zip\\7z.exe" a %s %s' %(arcName, prjProcFolder)
                    
    #call(callStr, shell=True, stdout=open(os.devnull, 'wb'))
    procA = subprocess.run(callStrA, shell=True)

    if procA.returncode == 0:
        print('Archive OK')
    else:
        print('{0} Project FGDB failed!'.format(prjName))
        sys.exit()
    
    del (arcName, callStrA)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

