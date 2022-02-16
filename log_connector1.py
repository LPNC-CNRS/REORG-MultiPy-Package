# -*- coding: utf-8 -*-
"""
Created on Fri Mar  8 09:55:38 2018

@author: Felix Renard
"""

import sys
import getopt
import os, fnmatch
import csv
from subprocess import call
import glob
import shutil
import nibabel as nib
import numpy as np
import json


#########

def find_files(directory, pattern):
    for root, dirs, files in os.walk(directory):
        for basename in files:
            if fnmatch.fnmatch(basename, pattern):
                filename = os.path.join(root, basename)
                yield filename


#############test function

def which(program):
    import os
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)
    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None

#############

try:
    opts, args = getopt.getopt(sys.argv[1:], "hd:et:T:f:", ["help","dir=","extract","transfer_dwi=","transfer_anat=","transfer_field_map="])
except getopt.GetoptError as err:
    # Affiche l'aide et quitte le programme
    print(err) # Va afficher l'erreur en anglais
    print('Please see the help.') # Fonction à écrire rappelant la syntaxe de la commande
    sys.exit(2)
 
output = None
verbose = False
for o, a in opts:
    if o == "-v":
        # On place l'option 'verbose' à True
        verbose = True


    elif o in ("-h", "--help"):
        # On affiche l'aide
        print('Help of the DTI prepocessing:')
        print('* means that no parameter is needed \n')
        print('     -h , --help: print the help')
        print('     -d , --dir : Source directory (MUST be set)')
        print('     -e , --extract *: Convert DICOM to nifti files with dcm2niix')  
        print('     -t,  --transfer : Need series_description.json. Transfer dwi files from source_data to the BIDS directory' ) 
        print('     -T,  --transfer : Need series_description.json. Transfer anat files from source_data to the BIDS directory' )
        print('     -f,  --transfer : Need series_description.json. Transfer field map files from source_data to the BIDS directory' )
        sys.exit()


    elif o in ("-d", "--dir"):
        #Lecture des fichiers
        cur_dir = a
        print( a)
        if os.path.isdir(cur_dir)==False:
            print("Error")
            print( cur_dir + " is not a directory.")
            sys.exit(-1)


        print( "\n Directory of the raw data:"+ cur_dir +" \n")
        file_name_source = cur_dir+"/sourcedata/sub-*/ses-*/"
        name_source = glob.glob(file_name_source)
        name_source.sort()
        dir_name_source = name_source
        file_name =  cur_dir+"/sub-*/ses-*/"
        name = glob.glob(file_name)
        name.sort()
        dir_name = name
        sub_name = [ x.split('/')[-3] for x in name]
        ses_name =[ x.split('/')[-2] for x in name]
        if len(ses_name)==0:
            print("Error")
            print("No directory are found in " + cur_dir+"/sourcedata/sub-*/ses-*/")
            print("Please check the directory tree.")
            sys.exit(-1)
        
        file_name_source = cur_dir+"/sourcedata/sub-*/ses-*/*"
        if len(glob.glob(file_name_source)) == 0:
            print("Error")
            print("No files are found are found in " + cur_dir+"/sourcedata/sub-*/ses-*/")
            print("Please check the directory tree.")
            sys.exit(-1)


    elif o in ("-e","--extract"):
        #Read dicom with dicom2niix_afni
        print( "Convert dicom to nifti \n")

        try:
            name_source
        except NameError:
            print("Error with directory")
            print("Directory is no set or empty.")
            print("Please specify the -d or --dir parameters.")
            sys.exit(-1)


        for i in range(len(name_source)):
            cmd = "dcm2niix -z y -o "+ name_source[i]+"DICOM/ "+ name_source[i]+"DICOM/"
            print(cmd)
            call(cmd.split())
    
    elif o in ("-t","--transfer_dwi"):

        series_description_file = a
        if os.path.isfile(series_description_file)==False:
            print("Error")
            print( series_description_file + " is not a file.")
            sys.exit(-1)

        try:
            series_description = json.load(open(series_description_file))
        except NameError:
            print("Error with directory")
            print("Directory is no set or empty.")
            print("Please specify the -d or --dir parameters.")
            sys.exit(-1)

        try:
            series_description['dwi']
        except:
            print("Error in the series_description.json file")
            print("No dwi descritption has been given")
            
        for i in range(len(dir_name_source)):
            tmp =  glob.glob(dir_name_source[i] +'/DICOM/'+ series_description['dwi'])
            for j in range(len(tmp)): 
                if ".nii" in tmp[j]:
                    try:
                        shutil.move(tmp[j],dir_name[i] +'dwi/'+sub_name[i]+'_'+ses_name[i]+'_dwi.nii.gz')
                    except:
                        print("Warning No nifti file for folder "+dir_name_source[i])
                if ".bval" in tmp[j]:
                    try:
                        shutil.move(tmp[j],dir_name[i] +'dwi/'+sub_name[i]+'_'+ses_name[i]+'_dwi.bval')
                    except:
                        print("Warning No bval file for folder "+dir_name_source[i])                
                if ".bvec" in tmp[j]:
                    try:
                        shutil.move(tmp[j],dir_name[i] +'dwi/'+sub_name[i]+'_'+ses_name[i]+'_dwi.bvec')
                    except:
                        print("Warning No bvec file for folder "+dir_name_source[i])                
                if ".json" in tmp[j]:
                    try:
                        shutil.move(tmp[j],dir_name[i] +'dwi/'+sub_name[i]+'_'+ses_name[i]+'_dwi.json')
                    except:
                        print("Warning No json file for folder "+dir_name_source[i])                

                

    elif o in ("-T","--transfer_anat"):

        series_description_file = a
        if os.path.isfile(series_description_file)==False:
            print("Error")
            print( series_description_file + " is not a file.")
            sys.exit(-1)

        try:
            series_description = json.load(open(series_description_file))
        except NameError:
            print("Error with directory")
            print("Directory is no set or empty.")
            print("Please specify the -d or --dir parameters.")
            sys.exit(-1)

        try:
            series_description['anat']
        except:
            print("Error in the series_description.json file")
            print("No anat descritption has been given")
            

        for i in range(len(dir_name_source)):
            tmp =  glob.glob(dir_name_source[i] +'/DICOM/'+ series_description['anat'])
            for j in range(len(tmp)): 
                if ".nii" in tmp[j]:
                    try:
                        shutil.move(tmp[j],dir_name[i] +'anat/'+sub_name[i]+'_'+ses_name[i]+'_T1w.nii.gz')
                    except:
                        print("Warning No nifti file for folder "+dir_name_source[i])
                if ".json" in tmp[j]:
                    try:
                        shutil.move(tmp[j],dir_name[i] +'anat/'+sub_name[i]+'_'+ses_name[i]+'_T1w.json')
                    except:
                        print("Warning No json file for folder "+dir_name_source[i])                


    elif o in ("-f","--transfer_field_map"):

        series_description_file = a
        if os.path.isfile(series_description_file)==False:
            print("Error")
            print( series_description_file + " is not a file.")
            sys.exit(-1)

        try:
            series_description = json.load(open(series_description_file))
        except NameError:
            print("Error with directory")
            print("Directory is no set or empty.")
            print("Please specify the -d or --dir parameters.")
            sys.exit(-1)

        try:
            series_description['fmap']
        except:
            print("Error in the series_description.json file")
            print("No field map descritption has been given")
            

        for i in range(len(dir_name_source)):
            for fmap in series_description['fmap']:
                tmp =  glob.glob(dir_name_source[i] +'/DICOM/'+ fmap['epi'])
                tmp.sort()
                for j in range(len(tmp)): 
                    if ".nii" in tmp[j]:
                        try:
                            shutil.move(tmp[j],dir_name[i] +'fmap/'+sub_name[i]+'_'+ses_name[i]+'_dir-'+fmap['dir_name'] +'_epi.nii.gz')
                        except:
                            print("Warning No nifti file for folder "+dir_name_source[i])
                    if ".bval" in tmp[j]:
                        try:
                            shutil.move(tmp[j],dir_name[i] +'fmap/'+sub_name[i]+'_'+ses_name[i]+'_dir-'+fmap['dir_name'] +'_epi.bval')
                        except:
                            print("Warning No bval file for folder "+dir_name_source[i])                
                    if ".bvec" in tmp[j]:
                        try:
                            shutil.move(tmp[j],dir_name[i] +'fmap/'+sub_name[i]+'_'+ses_name[i]+'_dir-'+fmap['dir_name'] +'_epi.bvec')
                        except:
                            print("Warning No bvec file for folder "+dir_name_source[i])                
                    if ".json" in tmp[j]:
                        #add encoding phase to the json field map
                        with open(tmp[j]) as feedsjson:
                            feeds = json.load(feedsjson)
                        feeds[u'PhaseEncodingDirection']= fmap['PhaseEncodingDirection']
                        with open(tmp[j], mode='w') as f:
                            f.write(json.dumps(feeds, indent=2))
                            
                        try:
                            shutil.move(tmp[j],dir_name[i] +'fmap/'+sub_name[i]+'_'+ses_name[i]+'_dir-'+fmap['dir_name'] +'_epi.json')
                        except:
                            print("Warning No json file for folder "+dir_name_source[i])                


    else:
        print("Unknown {} option".format(o))
        sys.exit(2)
