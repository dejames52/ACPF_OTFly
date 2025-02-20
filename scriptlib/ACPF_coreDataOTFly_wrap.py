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

# Import arcpy module
import arcpy
#from arcpy import env
#from arcpy.sa import *
#arcpy.CheckOutExtension("Spatial")
import subprocess
import sys, os

#arcpy.SetLogHistory(False)
# Local

##------------------------------------------------------------------------------
##------------------------------------------------------------------------------

if __name__ == "__main__":
    
    prjName = sys.argv[1]
    inHUC12list = list(sys.argv[2].split(','))
    print(inHUC12list)

    fcounter = 1
    processingFolder = r"D:\ACPFdevelop\ACPF_OTFly\processingDir"
    prjFolder = os.path.join(processingFolder, prjName)
    
    for inHUC in inHUC12list:
        #print(inHUC)
        if len(inHUC) == 12:
    
            print("Processsing: %s" % inHUC)
            
            ##------------------------------------------------------------------------------
            # Select HUC12 BND, create FGDB, extract FB from Master, build BUF
            arcpy.AddMessage(prjFolder)
            callstr1 = "python D:\\ACPFdevelop\\ACPF_OTFly\\scriptlib\\1_bld_acpfFGDB.py %s %s" %(inHUC,prjName)
            proc1 = subprocess.run(callstr1, shell=True)
            
            if proc1.returncode == 0:
                print('FB OK')
            else:
                print('{0} FB failed!'.format(inHUC))
                sys.exit()
                
            proc1 = ''

            ##------------------------------------------------------------------------------
            # Use BUF to extract 8 years of land use from nationalACPF
            callstr2 = "python D:\\ACPFdevelop\\ACPF_OTFly\\scriptlib\\2a_getHUC12_CDL_Landuse.py %s %s" %(inHUC,prjFolder)
            proc2 = subprocess.run(callstr2, shell=True)
            
            if proc2.returncode == 0:
                print('LU1 OK')
            else:
                print('{0} getLU failed!'.format(inHUC))
                sys.exit()
                
            proc2 = ''

            ##------------------------------------------------------------------------------
            # Use BUF to extract 8 years of land use from nationalACPF
            callstr3 = "python D:\\ACPFdevelop\\ACPF_OTFly\\scriptlib\\2b_assignHUC12_byFieldLandUse.py %s %s" %(inHUC,prjFolder)
            proc3 = subprocess.run(callstr3, shell=True)
            
            if proc3.returncode == 0:
                print('LU2 OK')
                #arcpy.management.Compact(fgdb)                        
            else:
                print('{0} procLU failed!'.format(inHUC))
                sys.exit()

            ##------------------------------------------------------------------------------
            # Use BUF to extract soils data from nationalACPF
            callstr4 = "python D:\\ACPFdevelop\\ACPF_OTFly\\scriptlib\\3_extract_ACPFgSSURGO.py %s %s" %(inHUC,prjFolder)
            proc4 = subprocess.run(callstr4, shell=True)
            
            if proc4.returncode == 0:
                print('gSSURGO OK')
                #arcpy.management.Compact(fgdb)                        
            else:
                print('{0} soils failed!'.format(inHUC))
                sys.exit()

            ##------------------------------------------------------------------------------
            # Update Metadata
            callstr5 = "python D:\\ACPFdevelop\\ACPF_OTFly\\scriptlib\\5_ACPF_MetadataImporterPro.py %s %s" %(inHUC,prjFolder)
            proc5 = subprocess.run(callstr5, shell=True)
            
            if proc5.returncode == 0:
                print('metadata OK')
            else:
                print('{0} meta failed!'.format(inHUC))
                sys.exit()

                
            del(inHUC)
            fcounter += 1
        else:
            print("Named Watershed is improperly formed: %s" % inHUC)

    # archive the project folder for download
