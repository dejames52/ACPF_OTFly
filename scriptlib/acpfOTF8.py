# -----------------------------------------------------------------------------
# acpfOTF8.p-y -- Archive
import arcpy
import sys, string, os, time, subprocess

def main(archiveFolder,prjArchiveFolder,prjName): 

    print("")
    print("Archiving")
    arcName = r"%s\acpf_archive%s.7z" %(archiveFolder,prjName)
    if os.path.exists(arcName):
        os.remove(arcName)
                      
    callStrA = '"C:\\Program Files\\7-Zip\\7z.exe" a %s %s' %(arcName, prjArchiveFolder)
    procA = subprocess.run(callStrA, shell=True)
    
    if procA.returncode == 0:
        print('Archive OK')
    else:
        print('{0} FGDB failed!'.format(prjName))
        sys.exit()
    
    del (arcName, callStrA)
    
    
if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
