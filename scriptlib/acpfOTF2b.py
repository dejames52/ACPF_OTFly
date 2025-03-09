# -----------------------------------------------------------------------------
# acpfOTF2b.py -- Land Use 2
# 
#  The Update Edited Field Boundaries tool will rebuild the land-use lookup 
#  tables based on the contents of an edited field boundary feature class, 
#  using the NASS CDL rasters present in the watershed's file geodatabase.
#  Included are:
#   - the CH_<HUC12> table - a summary of NASS CDL data by field for all 
#     land use raster available in the file-geodatabase
#   - the LU6_<HUC12> table - a 6 year summary of field land use
#   - crop rotation string (CropRotatn) using a single letter to represent 
#     each year's majpority crop type
#   - crop rotation summary (Cropsumry) a string using the single letter
#     of the majority crop followed by the number of occurances of that ctop 
#     over the rotation span
#   - a count of the number of occurances of corn-after-corn 'CC' in the 
#     crop rotation string - CCCount
#   - a count of the number of occurances of the majority crop percent of the 
#     field less than 75% - MixCount
#   - for each year in the span, the majority crop (majYR) and the percent 
#     of the field that it represents (pctYR)
#   - a General Land Use assignment based on the 6-yr crop rotation string and
#     the other derived fields.  
# -----------------------------------------------------------------------------
#  Orginal coding: D.James 08/2012
#    - 07/2013: update to 6-year rotation
#    - 11/2013: update to extend Pasture to include pasture woodlots; add class
#        for flood-prone cropland (1 year of Ag field as water)
#    - 04/2014: updated to ad the full crop history to 2000, table name: CH _inHUC
#    - 04/2014: made the full commitment to in_memory processing, reduce proc time by 60%!
#    - 08/2015: Repurpose the original script to update an edited field boundary 
#               feature class.
#    - BUG! 10/2015 FBndID should have a preceeding 'F' not 'FB'- Line 101
#    - 03/2016: remove the MixedOnly processing to exclude the c/s mixed landuse
#    - 10/2017: add test for isFeatureLayer to prevent examining non feature present
#               in the TOC, like web services, that cause a fail on testing
#    - 11/2017: Move to generic land use assignment
#               Ad new field, AgLandUse - a moire detailed listing of the 6-year string
#    - 05/2022: Account for sea water in the RI Sound thaat recieves a NASS CDL value of 0...line 254+: dictCDL[0] = 'X'
#    - 09/22: Add the use of updateYr as a requied field
#    - 11/22: Add anonymous OID identification to thwart FSA editing
#    - 01/2023: Fix updYear format to text(4) from short
#    - 02/2025: modify to work with ACPF On-The-Fly script set
# -----------------------------------------------------------------------------

# Import system modules
import arcpy
from arcpy import env
from arcpy.sa import *
import collections
import sys, string, os
from util import get_install_base

# Set extensions & environments 
arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True
arcpy.SetLogHistory(False)


##--------------------------------------------------------------------------------------
## Modules
## 

def mkOutputFrame(FBedit, StatFrame, TempFrame, inHUC, LTthresh):
    # Create the output frame
    if arcpy.Exists(TempFrame):
        arcpy.Delete_management(TempFrame)
    arcpy.CopyFeatures_management(FBedit, TempFrame)

    ## somehow there are FB that do not have the updatrYr field, so this workaround
    theFields = arcpy.ListFields(FBedit)
    theList = []
    for field in theFields:
        theList.append(field.name)
        
    if 'updateYr' in theList:
        theYr = [row[0] for row in arcpy.da.SearchCursor(FBedit, ["updateYr"])]
        fbUpdateYr = theYr[0]
        print(fbUpdateYr)
    else:
        print('no updateYr')
        fbUpdateYr = '2009'

    #Remove all unnecessary fields
    desc = arcpy.Describe(TempFrame)
    OID = desc.OIDFieldName
    
    reqFields = ['%s' % OID, 'SHAPE', 'SHAPE_Length', 'SHAPE_Area', 'Shape', 'Shape_Length', 'Shape_Area']
    delFields = []
    field_names = [f.name for f in arcpy.ListFields(TempFrame)]
    for f in field_names:
        if f not in reqFields:
            delFields.append(f)
    if len(delFields) != 0:
        arcpy.DeleteField_management(TempFrame, delFields)
    
    # Add core fields
    arcpy.AddField_management(TempFrame, "FBndID", "text", 255)
    arcpy.AddField_management(TempFrame, "Acres", "float")
    arcpy.AddField_management(TempFrame, "isAG", "short")
    arcpy.AddField_management(TempFrame, "updateYr", "text", 4)

    # add the LU6 fields
    arcpy.AddField_management(TempFrame, "GenLU", "text", 35)
    arcpy.AddField_management(TempFrame, "AgLandUse", "text", 35) 
    arcpy.AddField_management(TempFrame, "CropRotatn", "text", 20)
    arcpy.AddField_management(TempFrame, "CropSumry", "text", 20)
    arcpy.AddField_management(TempFrame, "CCCount", "text", 8)
    arcpy.AddField_management(TempFrame, "MixCount", "text", 8)
    
    # Calculate intitial values, except FBndID
    arcpy.CalculateField_management(TempFrame, "Acres", "!shape.area@acres!", "PYTHON_9.3")
    arcpy.CalculateField_management(TempFrame, "isAG", "0", "PYTHON_9.3")
    arcpy.CalculateField_management(TempFrame, "updateYr", fbUpdateYr, "PYTHON_9.3")
    
    # No fields LT 2.5 acres
    arcpy.MakeFeatureLayer_management(TempFrame, "TempLayer")
    arcpy.SelectLayerByAttribute_management("TempLayer", "NEW_SELECTION", '"Acres" < 2.5')
    arcpy.Eliminate_management("TempLayer", StatFrame, "AREA")

    arcpy.MakeFeatureLayer_management(StatFrame, "TempLayer2")
    arcpy.SelectLayerByAttribute_management("TempLayer2", "NEW_SELECTION", '"Acres" < 2.5')
    arcpy.DeleteFeatures_management("TempLayer2")

    # Update the edited FB to unique FBndID -- after the edits
    Desc = arcpy.Describe(StatFrame)
    OID = Desc.OIDFieldName
    calcFBStr = "F%s_!%s!" %(inHUC, OID)
    arcpy.CalculateField_management(StatFrame,"FBndID", "'%s'" %(calcFBStr), "PYTHON_9.3") 

    arcpy.Delete_management("TempLayer")
    arcpy.Delete_management("TempLayer2")
    if arcpy.Exists(TempFrame):
        arcpy.Delete_management(TempFrame)
        
    del(theFields,theList,desc,reqFields,delFields,field_names,Desc,OID,calcFBStr)
        

def calcMajPct(StatFrame, FileGDB, wsCDL, YrFld, PctFld): ###*** NEW NEW
    # Calculate FB majority percent
    # shout out to NNoman@esri.com
    zsMAj = FileGDB + "\\zsMAj"
    zsSum = FileGDB + "\\zsSum"
 
    FBmajority = ZonalStatistics(StatFrame, "FBndID", wsCDL, "MAJORITY", "DATA")
    isMajority = Con(FBmajority == wsCDL, 1)
    
    zsMajority = ZonalStatisticsAsTable(StatFrame, "FBndID", wsCDL, zsMAj, "DATA", "MAJORITY")
    sumMajority = ZonalStatisticsAsTable(StatFrame, "FBndID", isMajority, zsSum, "DATA", "SUM")
    
    arcpy.JoinField_management(StatFrame, "FBndID", zsMajority, "FBndID", ["MAJORITY","AREA"])
    arcpy.JoinField_management(StatFrame, "FBndID", sumMajority, "FBndID", ["AREA"])

    arcpy.AddField_management(StatFrame, YrFld, "long")
    arcpy.AddField_management(StatFrame, PctFld, "long")
    arcpy.CalculateField_management(StatFrame, YrFld, '!MAJORITY!', "PYTHON_9.3")
    arcpy.CalculateField_management(StatFrame, PctFld, '( !AREA_1! / !AREA! ) * 100', "PYTHON_9.3")
                
    arcpy.DeleteField_management(StatFrame,["AREA","AREA_1","MAJORITY"])
    arcpy.Delete_management(FBmajority)
    arcpy.Delete_management(isMajority)
    arcpy.Delete_management(zsMajority)
    arcpy.Delete_management(sumMajority)
    arcpy.Delete_management(zsMAj)
    arcpy.Delete_management(zsSum)
    

def ProcByYear(StatFrame, FileGDB, inHUC, YrList):
    # Process the new framework through each year
    # for each year, add the majority crop ROTVAL and majority percent
    #  unless of course, there is not data for that year...
    for Year in YrList:
        Yr = Year[-2:]
            
        arcpy.AddMessage("Assigning landuse for 20" + Yr  )     

        YrFld = "maj" + Yr
        PctFld = "pct" + Yr
        wsCDL = Raster(os.path.join(FileGDB, "wsCDL20" + Yr))
        
        #----------------------------------------------------------------------------------------------
        ## Use the existing NASS CDL data 
        #----------------------------------------------------------------------------------------------
        arcpy.env.snapRaster = wsCDL
        arcpy.env.extent = wsCDL
        
        calcMajPct(StatFrame, FileGDB, wsCDL, YrFld, PctFld)
            
        arcpy.env.extent = ""
        arcpy.env.snapRaster = ""
        
        del(Yr,YrFld,PctFld,wsCDL)


def popSummaries(StatFrame, YrList6, CDL_lkup, LTthresh):
    # make three dictionaries of the CDL lookup table
    ##------------------------------------------------------------------------- 
    dictCDL = {}
    dictValPrime = {}
    dictValOne = {}
    for row in arcpy.da.SearchCursor(CDL_lkup,["Value", "ROTVAL", "PrimeName", "OneName"]):
        dictCDL[row[0]] = row[1]
        dictValPrime[row[0]] = row[2]
        dictValOne[row[0]] = row[3]
    del row

    #None Keys...
    dictCDL["None"] = 'X'
    dictCDL[""] = 'X'
    dictCDL[0] = 'X'
    dictValPrime["None"] = 'X'
    dictValPrime[""] = 'X'
    dictValPrime[0] = 'X'
    dictValOne["None"] = 'X'
    dictValOne[""] = 'X'
    dictValOne[0] = 'X'


    ## Create tableview in memory
    ##-------------------------------------------------------------------------
    arcpy.MakeTableView_management(StatFrame, "TView", "", "in_memory")


    ## Initialize output fields
    ##-------------------------------------------------------------------------
    #arcpy.AddMessage("Reset...")
    
    crsr1 = arcpy.da.UpdateCursor("TView", ["GenLU","AgLandUse","CropRotatn","CropSumry","CCCount","MixCount","isAG"])
    for row in crsr1:
        row[0] = ""
        row[1] = ""
        row[2] = ""
        row[3] = ""
        row[4] = ""
        row[5] = ""
        row[6] = 0
        crsr1.updateRow(row)
    del row
    del crsr1


    ## Populate the Crop Rotation field
    ##-------------------------------------------------------------------------
    arcpy.AddMessage("Create crop rotation...")
    
    SelectMaj = '"Maj' + YrList6[0] +'" IS NOT NULL and "Maj' + YrList6[1] +'" IS NOT NULL and ' \
                '"Maj' + YrList6[2] +'" IS NOT NULL and "Maj' + YrList6[3] +'" IS NOT NULL and ' \
                '"Maj' + YrList6[4] +'" IS NOT NULL and "Maj' + YrList6[5] +'" IS NOT NULL'

    rotationfields = ["CropRotatn","Maj"+YrList6[0],"Maj"+YrList6[1],"Maj"+YrList6[2], \
                      "Maj"+YrList6[3],"Maj"+YrList6[4],"Maj"+YrList6[5]]

    crsr2 = arcpy.da.UpdateCursor("TView", rotationfields, SelectMaj)
    for row in crsr2:
        row[0] = dictCDL[row[1]] + dictCDL[row[2]] + dictCDL[row[3]] + dictCDL[row[4]] + dictCDL[row[5]] + dictCDL[row[6]]
        crsr2.updateRow(row)

    del row
    del crsr2

    ##-------------------------------------------------------------------------
    #arcpy.AddMessage("Indexing...")
    tabledescription = arcpy.Describe(StatFrame)
    for idx in tabledescription.indexes:
        if idx.fields[0].Name == "CropRotatn":
            arcpy.RemoveIndex_management(StatFrame, "CRIndex")

    arcpy.AddIndex_management(StatFrame, "CropRotatn", "CRIndex")


    ##-------------------------------------------------------------------------
    ## Populate the ancillary crop fields:
    ##      CropSumry
    ##      CCCount
    ##      MixCount
    ##-------------------------------------------------------------------------

    clist = list('ABCDEFGHIJKLMNOPQRTUVWX')

    theFields = ["CropRotatn", "CropSumry", "CCCount", "MixCount", \
                 "Pct"+YrList6[0],"Pct"+YrList6[1],"Pct"+YrList6[2], \
                 "Pct"+YrList6[3],"Pct"+YrList6[4],"Pct"+YrList6[5]]

    SelectStr =  "\"CropRotatn\" <> ''"

    #arcpy.AddMessage("Summarizing rotation...")
    #arcpy.AddMessage(SelectStr)

    rows = arcpy.da.UpdateCursor("TView", theFields, SelectStr)
    #arcpy.AddMessage(theFields)
    
    for row in rows:
        cstrng = ""

        #rotstr = "CropRotatn" 
        rotstr = str(row[0])

        # Calculate Crop Summary
        # -----------------------------------------------
        for chr in clist:
            cnt = rotstr.count(chr) #cnt = string.count(rotstr, chr)
            if cnt > 0:
                cstrng = cstrng + chr + str(cnt)
        row[1] = cstrng                                  # "CropSumry"

        # Calculate Corn-after-Corn count
        # -----------------------------------------------
        ccnt = 0
        for i in range(len(rotstr)-1):
            if 'CC' in rotstr[i:i+2]:
                ccnt += 1
        row[2] = str(ccnt)+':'+str(len(rotstr))          # "CCCount"

        # Calculate mixed field count
        # -----------------------------------------------
        thrshld = 75
        cmcnt = 0
        #print(row[4:10])
        for YRpct in row[4:10]:
            if YRpct == None:
                cmcnt = cmcnt
            elif YRpct < thrshld:
                cmcnt += 1
        row[3] = str(cmcnt)+':'+str(len(YrList6))        # mixcount

        rows.updateRow(row)

    del row
    del rows
    del [dictCDL, SelectMaj, rotationfields, theFields]


    ##-------------------------------------------------------------------------
    # Assign General Land Use and Detailed Land Use
    #  Must have Crop Rotation
    # -----------------------------------------------
    #arcpy.AddMessage("Assigning General Land Use...")

    SelectStr =  "\"CropRotatn\" <> ''"

    fldList = ["CropRotatn","GenLU","AgLandUse","CropSumry","CCCount", "MixCount","Acres","isAG","Maj"+YrList6[0],"Maj"+YrList6[1],"Maj"+YrList6[2],"Maj"+YrList6[3],"Maj"+YrList6[4],"Maj"+YrList6[5]]
    #              0           1        2         3            4         5         6       7         8-13  
    rowz = arcpy.da.UpdateCursor("TView", fldList, SelectStr)
    for roow in rowz:
        ## Extract land use count from rotation string
        rotstr = str(roow[0])
        
        corncount = rotstr.count("C")
        beancount = rotstr.count("B")
        pasturecount = rotstr.count("P")        
        
        forestcount = rotstr.count("F")
        urbancount = rotstr.count("U")
        watercount = rotstr.count("T")
        Xcount = rotstr.count("X")
        
        CBPcount = corncount + beancount + pasturecount
        NonAgcount = forestcount + urbancount + watercount + Xcount 
        
        # Count the value classes for the 6 years ----------------------------------
        valueList = []
        valueList = [roow[8], roow[9], roow[10], roow[11], roow[12], roow[13]]            #new
        
        # group the corn Values
        for e in range(6):
            if valueList[e] == 12 or valueList[e] == 13:
                valueList[e] = 1
        
        # Create a collection Counter for Values
        mcmn =collections.Counter(valueList).most_common()
        mcmn.sort(key=lambda x: x[0])
        mcmn.sort(key=lambda x: x[1], reverse=True)
            
        Vals = []
        Counts = []
        for e in mcmn:
            Vals.append(e[0])
            Counts.append(e[1])

        
        ## Assign General Land Use class ---------------------------
        ##  General Land Use class & handle special classes
        if roow[6] <= LTthresh:
            roow[1] = "LT %s ac" %(str(LTthresh))
            roow[2] = "LT %s ac" %(str(LTthresh))
        
        elif urbancount >= 4:
            roow[1] = "Urban"
            roow[2] = "nonAg-Developed"
        elif watercount >= 4:
            roow[1] = "Water/wetland"
            roow[2] = "nonAg-Water/Wetland"
        elif forestcount >= 4:
            roow[1] = "Forest"
            roow[2] = "nonAg-Forest"
        elif NonAgcount >= 4:
            roow[1] = "nonAg"
            roow[2] = "nonAg"
        elif pasturecount >= 5:
            roow[1] = "Pasture|Grass|Hay"
            roow[2] = "Pasture|Grass|Hay"
            roow[7] = 2
        elif forestcount + pasturecount >= 5:
            roow[1] = "Pasture|Grass|Hay"
            roow[2] = "Pasture|Grass|Hay"
            roow[7] = 2
        elif forestcount + pasturecount + watercount >= 5:
            roow[1] = "Pasture|Grass|Hay"
            roow[2] = "Pasture|Grass|Hay"
            roow[7] = 2
        elif watercount >= 2:
            roow[1] = "Flood-prone Cropland"
            roow[2] = "Flood-prone " + dictValOne.get(Vals[0])
            roow[7] = 2
        elif beancount > 0 and corncount > 0 and pasturecount > 0 and CBPcount == 6 and roow[4] != '0:6':
            roow[1] = "Corn/Soybeans"
            roow[2] = "CntCorn/Soybeans/Perennial"
            roow[7] = 1
        elif beancount > 0 and corncount > 0 and pasturecount > 0 and CBPcount == 6:
            roow[1] = "Corn/Soybeans"
            roow[2] = "Corn/Soybeans/Perennial"
            roow[7] = 1
        elif beancount > 0 and corncount > 0 and beancount + corncount == 6 and roow[4] != '0:6':
            roow[1] = "Corn/Soybeans"
            roow[2] = "CntCorn/Soybeans"
            roow[7] = 1
        elif beancount > 0 and corncount > 0 and beancount + corncount >= 5:   ## change from base:  '== 6'
            roow[1] = "Corn/Soybeans"
            roow[2] = "Corn/Soybeans"
            roow[7] = 1


        # Assign Crop Rotations using Value Counts, PrimeName, and OneName
        #  discrete breakouts for double crop and perennial classes
        #  - 6 Continuous Crop
        #
        #  - 5,1 Crop rotation || Double Crop rotation
        #
        #  - 4,2 Crop0/Crop1 || Double Crop rotation | Crop0/Double Crop |  Crop0/Perennial
        #  - 4,1,1 Crop0 rotation || Double Crop rotation | Crop0/Double Crop | Perennial rotation | Crop0/Perennial 
        #
        #  - 3,3 Crop0/Crop1 || Double Crop rotation | Crop0/Double Crop | Double Crop/Crop1 | Crop0/Perennial | Crop1/Perennial 
        #  - 3,2,1 Crop0/Crop1 || Double Crop rotation | Crop0/Double Crop | Double Crop/Crop1 | Perennial rotation | Crop0/Perennial | Crop1/Perennial
        #  - 3,1,1,1 Crop0 rotation || Double Crop rotation | Perennial rotation
        #
        #  - 2,2,2 Crop0/Crop1/Crop2 || Double Crop rotation | Crop0/Double Crop | Crop1/Double Crop | Crop2/Double Crop 
        #                            || Perennial rotation | Crop0/Perennial | Crop1/Perennial | Crop2/Perennial 
        #  - 2,2,1,1 Crop0/Crop1 || Double Crop rotation | Crop0/Double Crop | Crop1/Double Crop | Perennial rotation | Crop0/Perennial | Crop1/Perennial 
        #  - 2,1,1,1,1 Crop0 rotation || Double Crop rotation | Perennial rotation
        
        # Continuous - single value dominant crop, double crop generalized, perennial class assigned above
        elif Counts[0] == 6:
            roow[1] = "Continuous " + dictValPrime.get(Vals[0])
            roow[2] = "Continuous " + dictValPrime.get(Vals[0])
            if dictValOne.get(Vals[0]) == 'DblCrop':
                roow[1] = 'Continuous Double Crop'
            roow[7] = 1         
            
        # 5 - single dominant crop with lone secondary crop: dominant crop rotation
        elif Counts[0] == 5:
            roow[1] = dictValPrime.get(Vals[0]) +' rotation'
            roow[2] = "Cnt" + dictValPrime.get(Vals[0]) +'/' + dictValPrime.get(Vals[1])
            if dictValOne.get(Vals[0]) == 'DblCrop':
                roow[1] = 'Double Crop rotation'
                
            roow[7] = 1
            
        elif Counts[0] == 4:
            if Counts[1] == 2:
                glu4 = dictValPrime.get(Vals[0]) + '/' + dictValPrime.get(Vals[1])
                lu4 = "Cnt" + dictValPrime.get(Vals[0]) + '/' + dictValPrime.get(Vals[1])
                if dictValOne.get(Vals[0]) == 'DblCrop' and dictValOne.get(Vals[1]) == 'DblCrop':
                    glu4 = 'Double Crop rotation'
                    lu4 = dictValPrime.get(Vals[0]) + '/' + dictValPrime.get(Vals[1])
                elif dictValOne.get(Vals[0]) == 'DblCrop':
                    glu4 = 'Double Crop/' + dictValPrime.get(Vals[1]) 
                    lu4 = dictValPrime.get(Vals[0]) + '/' + dictValPrime.get(Vals[1])
                elif dictValOne.get(Vals[1]) == 'DblCrop':
                    glu4 = dictValPrime.get(Vals[0]) + '/Double Crop'
                    lu4 = dictValPrime.get(Vals[0]) + '/' + dictValPrime.get(Vals[1])
                    
                elif dictValOne.get(Vals[0]) == 'Perennial':
                    glu4 = dictValPrime.get(Vals[1]) + '/Perennial'
                    lu4 = dictValPrime.get(Vals[1]) + '/' + dictValPrime.get(Vals[0])
                elif dictValOne.get(Vals[1]) == 'Perennial':
                    glu4 = dictValPrime.get(Vals[0]) + '/Perennial'
                    lu4 = dictValPrime.get(Vals[0]) + '/' + dictValPrime.get(Vals[1])
                    
            else:
                glu4 = dictValPrime.get(Vals[0]) + ' rotation'
                lu4 = "Cnt" + dictValPrime.get(Vals[0]) + '/Mixed'
                if dictValOne.get(Vals[0]) == 'DblCrop':
                    glu4 = 'Double Crop rotation'
                elif dictValOne.get(Vals[1]) == 'DblCrop' and dictValOne.get(Vals[2]) == 'DblCrop':
                    glu4 = dictValPrime.get(Vals[0]) + '/Double Crop'
                    lu4 = "Cnt" + dictValPrime.get(Vals[0]) + '/Double Crop'

                elif dictValOne.get(Vals[0]) == 'Perennial':
                    glu4 ='Perennial rotation'
                    lu4 = dictValPrime.get(Vals[0]) + '/' + dictValPrime.get(Vals[1]) + '/' + dictValPrime.get(Vals[2])
                elif dictValOne.get(Vals[1]) == 'Perennial' and dictValOne.get(Vals[2]) == 'Perennial':
                    glu4 = dictValPrime.get(Vals[0]) + '/Perennial'
                    lu4 = dictValPrime.get(Vals[0]) + '/' + dictValPrime.get(Vals[1]) + '/' + dictValPrime.get(Vals[2]) #??
                 
            roow[1] = glu4
            roow[2] = lu4
            del (lu4, glu4)
                
            roow[7] = 1
            
        elif Counts[0] == 3:
            if Counts[1] == 3:
                glu3 = dictValPrime.get(Vals[0]) + '/' + dictValPrime.get(Vals[1])
                lu3 = dictValPrime.get(Vals[0]) + '/' + dictValPrime.get(Vals[1])
                if dictValOne.get(Vals[0]) == 'DblCrop' and dictValOne.get(Vals[1]) == 'DblCrop':
                    glu3 = 'Double Crop rotation'
                elif dictValOne.get(Vals[0]) == 'DblCrop':
                    glu3 = 'Double Crop/' + dictValPrime.get(Vals[1])
                elif dictValOne.get(Vals[1]) == 'DblCrop':
                    glu3 = dictValPrime.get(Vals[0]) + '/Double Crop'
                    
                elif dictValOne.get(Vals[0]) == 'Perennial':                           # the flop
                    glu3 = dictValPrime.get(Vals[1]) + '/Perennial'
                    lu3 = dictValPrime.get(Vals[1]) + '/' + dictValPrime.get(Vals[0])
                elif dictValOne.get(Vals[1]) == 'Perennial':
                    glu3 = dictValPrime.get(Vals[0]) + '/Perennial'
                    
            elif Counts[1] == 2:
                glu3 = dictValPrime.get(Vals[0]) + '/' + dictValPrime.get(Vals[1]) 
                lu3 = dictValPrime.get(Vals[0]) + '/' + dictValPrime.get(Vals[1]) + '/' + dictValPrime.get(Vals[2])
                if dictValOne.get(Vals[0]) == 'DblCrop' and dictValOne.get(Vals[1]) == 'DblCrop':
                    glu3 = 'Double Crop rotation'
                    lu3 = dictValPrime.get(Vals[0]) + '/' + dictValPrime.get(Vals[1])
                elif dictValOne.get(Vals[0]) == 'DblCrop':
                    glu3 = 'Double Crop/'  + dictValPrime.get(Vals[1]) 
                    lu3 = dictValPrime.get(Vals[0]) + '/' + dictValPrime.get(Vals[1])
                elif dictValOne.get(Vals[1]) == 'DblCrop':
                    glu3 = dictValPrime.get(Vals[0]) + '/Double Crop'
                    lu3 = dictValPrime.get(Vals[0]) + '/' + dictValPrime.get(Vals[1])
                    
                elif dictValOne.get(Vals[0]) == 'Perennial':
                    glu3 = dictValPrime.get(Vals[1]) + '/Perennial'
                    lu3 = dictValPrime.get(Vals[1]) + '/' + dictValPrime.get(Vals[0]) + '/' + dictValPrime.get(Vals[2])
                elif dictValOne.get(Vals[1]) == 'Perennial':
                    glu3 = dictValPrime.get(Vals[0]) + '/Perennial'
                    lu3 = dictValPrime.get(Vals[0]) + '/' + dictValPrime.get(Vals[1]) + '/' + dictValPrime.get(Vals[2])
                    
            else:
                glu3 = dictValPrime.get(Vals[0]) + ' rotation'
                lu3 = dictValPrime.get(Vals[0]) + '/Mixed'
                if dictValOne.get(Vals[0]) == 'DblCrop':
                    glu3 = 'Double Crop rotation'
                elif dictValOne.get(Vals[0]) == 'Perennial':
                    glu3 ='Perennial rotation'
                    
            roow[1] = glu3
            roow[2] = lu3
            del (lu3, glu3)
            
            roow[7] = 1

        elif Counts[0] == 2:
            if Counts[1] == 2 and Counts[2] == 2:
                glu2 = dictValPrime.get(Vals[0]) + '/' + dictValPrime.get(Vals[1]) + '/' + dictValPrime.get(Vals[2])  
                lu2 = dictValPrime.get(Vals[0]) + '/' + dictValPrime.get(Vals[1]) + '/' + dictValPrime.get(Vals[2])
                if dictValOne.get(Vals[0]) == 'DblCrop' and dictValOne.get(Vals[1]) == 'DblCrop' and dictValOne.get(Vals[2]) == 'DblCrop':
                    glu2 = 'Double Crop rotation'
                elif dictValOne.get(Vals[0]) == 'DblCrop' and dictValOne.get(Vals[1]) == 'DblCrop':
                    glu2 = dictValPrime.get(Vals[2]) + '/Double Crop'
                elif dictValOne.get(Vals[0]) == 'DblCrop' and dictValOne.get(Vals[2]) == 'DblCrop':
                    glu2 = dictValPrime.get(Vals[1]) + '/Double Crop' 
                elif dictValOne.get(Vals[1]) == 'DblCrop' and dictValOne.get(Vals[2]) == 'DblCrop':
                    glu2 = dictValPrime.get(Vals[0]) + '/Double Crop'
                elif dictValOne.get(Vals[2]) == 'DblCrop':
                    glu2 = dictValPrime.get(Vals[0]) + '/' + dictValPrime.get(Vals[1]) + '/Double Crop' 
                elif dictValOne.get(Vals[1]) == 'DblCrop':
                    glu2 = dictValPrime.get(Vals[0])+ '/' + dictValPrime.get(Vals[2]) + '/Double Crop'   
                elif dictValOne.get(Vals[0]) == 'DblCrop':
                    glu2 = dictValPrime.get(Vals[1])+ '/' + dictValPrime.get(Vals[2]) + '/Double Crop' 
                    
                elif dictValOne.get(Vals[0]) == 'Perennial' and dictValOne.get(Vals[1]) == 'Perennial':
                    glu2 = dictValPrime.get(Vals[2]) + '/Perennial'
                elif dictValOne.get(Vals[0]) == 'Perennial' and dictValOne.get(Vals[2]) == 'Perennial':
                    glu2 = dictValPrime.get(Vals[1]) + '/Perennial' 
                elif dictValOne.get(Vals[1]) == 'Perennial' and dictValOne.get(Vals[2]) == 'Perennial':
                    glu2 = dictValPrime.get(Vals[0]) + '/Perennial'
                elif dictValOne.get(Vals[2]) == 'Perennial':
                    glu2 = dictValPrime.get(Vals[0]) + '/' + dictValPrime.get(Vals[1]) + '/Perennial' 
                elif dictValOne.get(Vals[1]) == 'Perennial':
                    glu2 = dictValPrime.get(Vals[0])+ '/' + dictValPrime.get(Vals[2]) + '/Perennial'   
                elif dictValOne.get(Vals[0]) == 'Perennial':
                    glu2 = dictValPrime.get(Vals[1])+ '/' + dictValPrime.get(Vals[2]) + '/Perennial' 
                    
                
            elif Counts[1] == 2:
                glu2 = dictValPrime.get(Vals[0]) + '/' + dictValPrime.get(Vals[1]) 
                lu2 = dictValPrime.get(Vals[0]) + '/' + dictValPrime.get(Vals[1]) + '/' + 'Mixed'
                if dictValOne.get(Vals[0]) == 'DblCrop' and dictValOne.get(Vals[1]) == 'DblCrop':
                    glu2 = 'Double Crop rotation'
                elif dictValOne.get(Vals[0]) == 'DblCrop':
                    glu2 = dictValPrime.get(Vals[1]) + '/Double Crop' 
                elif dictValOne.get(Vals[1]) == 'DblCrop':
                    glu2 = dictValPrime.get(Vals[0]) + '/Double Crop'
                    
                if dictValOne.get(Vals[0]) == 'Perennial' and dictValOne.get(Vals[1]) == 'Perennial':
                    glu2 = 'Perennial rotation'
                elif dictValOne.get(Vals[0]) == 'Perennial':
                    glu2 = dictValPrime.get(Vals[1]) + '/Perennial' 
                elif dictValOne.get(Vals[1]) == 'Perennial':
                    glu2 = dictValPrime.get(Vals[0]) + '/Perennial'

            else:
                glu2 = dictValPrime.get(Vals[0]) + ' rotation' 
                lu2 = dictValPrime.get(Vals[0]) + '/Mixed' 
                if dictValOne.get(Vals[0]) == 'DblCrop':
                    glu2 = 'Double Crop rotation'
                if dictValOne.get(Vals[0]) == 'Perennial':
                    glu2 = 'Perennial rotation'
            
            roow[1] = glu2
            roow[2] = lu2
            del (lu2, glu2)
            
            roow[7] = 1
            
        else:
            roow[1] = 'Mixed Agriculture'
            roow[2] = 'Mixed Agriculture'
            roow[7] = 1
            
        rowz.updateRow(roow)

    del roow
    del rowz
    del [fldList,corncount,beancount,pasturecount,forestcount,urbancount,watercount,Xcount,CBPcount,NonAgcount]
    
    arcpy.Delete_management("TView")

                      
    
def mkOutputs(StatFrame, FileGDB, inHUC, YrList, FBedit):
    arcpy.AddMessage("Exporting...")

    # rename existing features and tables
    # If the original is the only existing one, rename it to '_orig'
    # If '_orig' already exists, rename to old -- over and over again
    #FB_orig = "FB%s_orig" % (inHUC)
    #
    LU_table = "LU6_%s" % inHUC
    CH_table = "CH_%s" % inHUC

    # Create the new
    arcpy.CopyFeatures_management(StatFrame, FBedit)     
    arcpy.TableToTable_conversion(StatFrame, FileGDB, LU_table)
    arcpy.TableToTable_conversion(StatFrame, FileGDB, CH_table)
    
    # Delete appropriate fields
    FB_delfldList = ["GenLU","AgLandUse","CropRotatn","CropSumry","CCCount","MixCount"] 
    LU6_delfldList = ["Shape_Length", "Shape_Area", "Acres", "isAg", "updateYr"]
    CH_delfldList = FB_delfldList + LU6_delfldList 

    arcpy.DeleteField_management(FBedit, FB_delfldList)
    arcpy.DeleteField_management(LU_table, LU6_delfldList)
    arcpy.DeleteField_management(CH_table, CH_delfldList)
    
    # Delete the year fields; FBedit, LU6
    YrfldList = []
    for Yr in YrList:
        YrFld = "maj" + Yr[-2:]
        PctFld = "pct" + Yr[-2:]
        YrfldList.append(YrFld)
        YrfldList.append(PctFld)

    arcpy.DeleteField_management(FBedit, YrfldList)
    arcpy.DeleteField_management(LU_table, YrfldList)
    
    #arcpy.management.AddIndex(FBedit, "FBndID", "FBidx")
    #arcpy.management.AddIndex(LU_table, "FBndID", "FBidx")
    #arcpy.management.AddIndex(CH_table, "FBndID", "FBidx")
    
    arcpy.Delete_management(StatFrame)
    del (LU_table,CH_table,YrfldList, FB_delfldList, CH_delfldList)


##------------------------------------------------------------------------------
##------------------------------------------------------------------------------

def main(inHUC, prjProcFolder):
    base = get_install_base()
    # Input data
    CDL_lkup = base + r"\nationalACPF\ACPF_Basedata.gdb\ACPF_CDLlkup_2023"
    HUC12status = base + r"\nationalACPF\ACPF_Basedata.gdb\US48_HUC12_2023"
    CDLroot = base + r"\nationalACPF\ACPF_LandUse\US_CDL20"
    LTthresh = 5

    FileGDB = prjProcFolder + "\\acpf" + inHUC + ".gdb"

    arcpy.AddMessage("")
    arcpy.AddMessage("Land use 2: " + FileGDB)

    env.workspace = FileGDB
    env.extent = "buf" + inHUC
        
    # Years
    #-----------------------------------------------------------------------------
    arcpy.AddMessage(arcpy.env.workspace)
    YrList = arcpy.ListRasters("wsCDL*")
    
    YrList.sort()
    YrList6 = []
    for year in YrList[-6:]:
        YrList6.append(year[-2:])
    
    if len(YrList) > 6:
        arcpy.AddMessage("---only the last 6 years will be used for land use assignment: %s" %(YrList6))
    
            
    # Process
    #-----------------------------------------------------------------------------
    StatFrame = FileGDB + "\\FieldFrame"
    TempFrame = FileGDB + "\\TempFrame"
    FBedit = FileGDB + "\\FB%s" % inHUC
    
    mkOutputFrame(FBedit, StatFrame, TempFrame, inHUC, LTthresh)
        
    ProcByYear(StatFrame, FileGDB, inHUC, YrList)
        
    popSummaries(StatFrame, YrList6, CDL_lkup, LTthresh)
        
    mkOutputs(StatFrame, FileGDB, inHUC, YrList, FBedit)
            
    del(inHUC,prjProcFolder,FileGDB,YrList,YrList6,StatFrame,TempFrame,FBedit)
    env.workspace = ""
    env.extent = ""    
    
            
if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
