#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sat Jun 13 08:20:42 2020

@author: felix
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
import scipy.stats as stats
import ants

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
    opts, args = getopt.getopt(sys.argv[1:], "hd:T:Cpca:f", ["help","dir=","transfer_anat=","Crop","preproc","CT","atlas=","f"])
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
        print('Help of the cortical thickness estimation prepocessing:')
        print('* means that no parameter is needed \n')
        print('     -h , --help: print the help')
        print('     -d , --dir : Source directory (MUST be set)')
        print('     -T , --transfer_anat : Transfer T1 from sourcedata (need series description json)')
        print('     -C , --Crop: Crop the data')
        print('     -p , --preproc : Perform the segmentation of the different parts of the brain with fmriprep')
        print('     -c , --CT *: Cortical Thickness estimation') 
        print('     -a , --atlas: Define the atlas to perform the connectome analysis')
        print('     -f , --fusion*: Fusion the labels of the atlas and estimate the CT per ROI')
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
        
        if len(glob.glob(file_name)) == 0:
            print("Error")
            print("No files are found are found in " + cur_dir+"/sub-*/ses-*/")
            print("Please check the directory tree.")
            sys.exit(-1)
    
            
    elif o in ("-T","--transfer_anat"):

        series_description_file = a
        if os.path.isfile(series_description_file)==False:
            print("Error")
            print( series_description_file + " is not a file.")
            sys.exit(-1)

        try:
            series_description = json.load(open(series_description_file))
        except NameError:
            print("Error with the json file")
            print("Please specify the -d or --dir parameters.")
            sys.exit(-1)

        try:
            series_description['anat']
        except:
            print("Error in the series_description.json file")
            print("No anat descritption has been given")
            

        for i in range(len(dir_name_source)):
            tmp =  glob.glob(dir_name_source[i] +'/anat/'+ series_description['anat'])
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


    elif o in ("-C","--Crop"):
        print(" Crop the data")
        try:
            name_source
        except NameError:
            print("Error with directory")
            print("Directory is no set or empty.")
            print("Please specify the -d or --dir parameters.")
            sys.exit(-1)

        for i in range(len(dir_name)):
          try:
            anat_file = dir_name[i] +'anat/'+sub_name[i]+'_'+ses_name[i]+'_T1w.nii.gz'
            anat_orig_file = dir_name[i] +'anat/'+sub_name[i]+'_'+ses_name[i]+'_T1w_orig.nii.gz'
            anat_dir = dir_name[i] +'anat/'
            #os.mkdir(dir_name[i] +'anat/' + sub_name[i]) 
            cmd = "recon-all -s "+sub_name[i]+" -i "+anat_file+" -autorecon1 -sd "+dir_name[i] +'anat/'
            print(cmd)
            call(cmd.split(" "))
            cmd = "recon-all -s "+sub_name[i]+" -gcareg -sd "+dir_name[i] +'anat/'
            print(cmd)
       	    call(cmd.split(" "))
            cmd = "recon-all -s "+sub_name[i]+" -canorm -sd "+dir_name[i] +'anat/'
            print(cmd)
       	    call(cmd.split(" "))
            cmd = "recon-all -s "+sub_name[i]+" -rmneck -sd "+dir_name[i] +'anat/'
            print(cmd)
       	    call(cmd.split(" "))
       	    shutil.move(anat_file,anat_orig_file)
            anat_crop = dir_name[i] +'anat/'+sub_name[i]+"/mri/nu_noneck.mgz"
            cmd = "mri_convert --in_type mgz --out_type nii "+anat_crop+" "+anat_file
            print(cmd)
            call(cmd.split(" "))
            print(dir_name[i] +'anat/'+sub_name[i])
            shutil.rmtree(dir_name[i] +'anat/'+sub_name[i])
          except:
            print("problem for the crop with subject "+ sub_name[i])
            shutil.move(anat_orig_file,anat_file)

    elif o in ("-p","--preproc"):
        print("Preprocessing with fmriprep \n")

        try:
            name_source
        except NameError:
            print("Error with directory")
            print("Directory is no set or empty.")
            print("Please specify the -d or --dir parameters.")
            sys.exit(-1)
        if which('fmriprep') is not None:
            cmd= "fmriprep "+cur_dir+" "+cur_dir+"/derivatives/ participant --anat-only --fs-no-reconall --clean-workdir --output-spaces anat"
            call(cmd.split(" "))
        elif which('fmriprep-docker') is not None:
            cmd= "fmriprep-docker "+cur_dir+" "+cur_dir+"/derivatives/ participant --anat-only --fs-no-reconall --clean-workdir --output-spaces anat"
            call(cmd.split(" "))
        else:
            print("Error fmriprep or fmriprep-docker is not installed")
            print("Please install fmriprep before starting the preprocessing step")
            sys.exit(-1)


    
    elif o in ("-c","--CT"):
        #Estimate Cortical Thickness via ANTS
        print( "Estimate the cortical thickness \n")
        try:
            name_source
        except NameError:
            print("Error with directory")
            print("Directory is no set or empty.")
            print("Please specify the -d or --dir parameters.")
            sys.exit(-1)   
        for i in range(len(dir_name)):
                #Create first segmentation for the cortical substructure
                T1_name_file = cur_dir + "/derivatives/fmriprep/" +sub_name[i]+ "/anat/"+ sub_name[i]+ "_desc-preproc_T1w.nii.gz"
                seg_output = cur_dir + "/derivatives/"+sub_name[i]+"/"+ses_name[i]+"/anat/"+sub_name[i]+'_'+ses_name[i]
                cmd = "run_first_all -i "+T1_name_file+" -o "+seg_output
                call(cmd.split(" "))
                cortstruct_file = cur_dir + "/derivatives/"+sub_name[i]+"/"+ses_name[i]+"/anat/"+sub_name[i]+'_'+ses_name[i] +"_all_fast_firstseg.nii.gz"
                cortstruct = ants.image_read(cortstruct_file)
                ind_cortstruct = np.where(cortstruct.numpy() == 16)
                cortstruct[ind_cortstruct] = 0
                ind_cortstruct = np.where(cortstruct.numpy())
                cortstruct[ind_cortstruct] = 1
                #Read the images
                seg_anat_file = cur_dir + "/derivatives/fmriprep/"+sub_name[i]+"/anat/"+sub_name[i]+"_dseg.nii.gz"
                seg_anat_file2 = cur_dir + "/derivatives/fmriprep/"+sub_name[i]+"/anat/"+sub_name[i]+"_dseg2.nii.gz"
                GM_prob_file = cur_dir + "/derivatives/fmriprep/"+sub_name[i]+"/anat/"+sub_name[i]+"_label-GM_probseg.nii.gz"
                WM_prob_file = cur_dir + "/derivatives/fmriprep/"+sub_name[i]+"/anat/"+sub_name[i]+"_label-WM_probseg.nii.gz"
                segs = ants.image_read(seg_anat_file)
                GM_prob = ants.image_read(GM_prob_file)
                WM_prob = ants.image_read(WM_prob_file)
                CT_file = cur_dir + "/derivatives/"+sub_name[i]+"/"+ses_name[i]+"/anat/"+sub_name[i]+'_'+ses_name[i]+"_thickness.nii.gz"
                #convert FSL segmentation labels to ANTS label
                ind1 = np.where(segs.numpy()==1)
                ind2 = np.where(segs.numpy()==2)
                ind3 = np.where(segs.numpy()==3)
                segs[ind1] = 2  #GM label
                segs[ind2] = 3  #WM label
                segs[ind3] = 1  #CSF label
                segs[ind_cortstruct] = 2 #cortical structure label
                ants.image_write(segs,seg_anat_file2)
                GM_prob[ind_cortstruct] = 0.9
                WM_prob[ind_cortstruct] = 0.1
                #estimate the cortical thickness
                thickimg = ants.kelly_kapowski(s=segs, g=GM_prob, w=WM_prob, its=45, r=0.5, m=1)
                ants.image_write(thickimg,CT_file)
                
      
    elif o in ("-a","--atlas"):
        #Get the atlas name, the atlas file name and the corresponding lables name from json file
        print("Set the atlas name\n") 
        atlas_file = a
        if os.path.isfile(atlas_file)==False:
            print("Error")
            print( atlas_file + " is not a file. Please verify your file.")
            sys.exit(-1)
            
        print( atlas_file)
        try:
            data_json = json.load(open(atlas_file))
        except:
            print( atlas_file + " is not a correct JSON. Please verify your file.")
            sys.exit(-1)
        
        #Test the atlas files
        try:
            atlas = data_json["Atlas"]
        except:
            print( "No Atlas key in the json file. It is mandatory.")
            print( "Please check your json file.")
            sys.exit(-1)
        
        for tmp_atlas in atlas:
            if os.path.isfile(tmp_atlas)==False:
                print("Error")
                print( tmp_atlas + " is not a file. Please verify your file.")
                sys.exit(-1)
        
        
        #Test the labels files
        try:
            labels = data_json["Labels"]
        except:
            print( "No Labels key in the json file. It is mandatory.")
            print( "Please check your json file.")
            sys.exit(-1)
        
        for tmp_labels in labels:
            if os.path.isfile(tmp_labels)==False:
                print("Error")
                print( tmp_labels + " is not a file. Please verify your file.")
                sys.exit(-1)
        
        #Test the name of the atlas
        try:
            name_atlas = data_json["Name"]
        except:
            print( "No Name key in the json file. It is mandatory.")
            print( "Please check your json file.")
            sys.exit(-1)
            
        #check the number of each parameter 
        if not( len(atlas) == len(labels) == len(name_atlas) ):
            print( "Not the same number of atlas, labels and atlas_name in the json file.")
            print("It is mandatory.")
            print( "Please check your json file.")
            sys.exit(-1)
            
           
    elif o in ("-f","--fusion"):
        #Register to the template
        try:
            name_source
        except NameError:
            print("Error with directory")
            print("Directory is no set or empty.")
            print("Please specify the -d or --dir parameters.")
            sys.exit(-1)

        #Get the atlas and labels image
        try:
            atlas
        except:
            print( "The parameter -a,--atlas must be set for this step")
            
        #Load the atlas and the labels
        atlas_img = []
        labels_img = []
        for tmp_atlas in atlas:
            atlas_img.append( ants.image_read(tmp_atlas) )
        for tmp_labels in labels:
            labels_img.append( ants.image_read(tmp_labels) )
        
        for ind_sub in range(len(dir_name)):
            #Read the T1w for each subject
            T1_name_file = cur_dir + "/derivatives/fmriprep/" +sub_name[ind_sub]+ "/anat/"+ sub_name[ind_sub]+ "_desc-preproc_T1w.nii.gz"
            CT_name_file = cur_dir + "/derivatives/"+sub_name[ind_sub]+"/"+ses_name[ind_sub]+"/anat/"+sub_name[ind_sub]+'_'+ses_name[ind_sub]+"_thickness.nii.gz"
            #CT_name_file = cur_dir + "/derivatives/fmriprep/" +sub_name[ind_sub]+ "/anat/"+ sub_name[ind_sub]+ "_label-GM_probseg.nii.gz"
            mask_name_file = cur_dir + "/derivatives/fmriprep/" +sub_name[ind_sub]+ "/anat/"+ sub_name[ind_sub]+ "_dseg.nii.gz"
            T1_img = ants.image_read(T1_name_file)
            CT_img = ants.image_read(CT_name_file)
            img_mask = ants.image_read(mask_name_file)
            Vol_total = len(np.where(img_mask.numpy())[0])
            for ind_atlas in range(len(atlas)):
                print("Atlas for CT: "+ atlas[ind_atlas])
                #Mask the skull
                ind = np.where(img_mask.numpy() == 0)
                T1_img[ind] = 0
                #Estimate the transformation between template and subject
                atlas2T1_tx = ants.registration(fixed = T1_img, moving = atlas_img[ind_atlas], type_of_transform = 'SyN' ) 
                #Apply the transformation on the labels
                labels2T1_imgs = ants.apply_transforms(fixed = T1_img, moving= labels_img[ind_atlas], transformlist=atlas2T1_tx['fwdtransforms'],interpolator='nearestNeighbor')
                labels2T1_name = cur_dir+"/derivatives/" +sub_name[ind_sub]+"/"+ses_name[ind_sub]+ "/anat/"+ sub_name[ind_sub]+"_"+ses_name[ind_sub] +"labels_"+ name_atlas[ind_atlas]+"2T1.nii.gz"
                ants.image_write(labels2T1_imgs, labels2T1_name)
                Xspace,Yspace,Zspace = labels2T1_imgs.spacing
                labels = labels2T1_imgs.numpy()
                CT_ima = CT_img.numpy()
                #Number of ROIs - Be careful to remove the 0-background ROI
                # AAL atlas
                NB_ROI = np.unique(labels).shape[0]-1
                ROI = np.unique(labels)[1:]
                #Folder name to save the results
                dir_name_tmp = cur_dir + "/derivatives/"+sub_name[ind_sub]+"/"+ses_name[ind_sub]+"/anat/"+sub_name[ind_sub]+"_"+ses_name[ind_sub]
                #Average the CT
                mask = np.where(CT_ima == 0)
                labels[mask] = 0
                CT_mean = np.zeros(NB_ROI)
                CT_std = np.zeros(NB_ROI)
                Vol = np.zeros(NB_ROI)
                for j in range(NB_ROI):
                    CT_mean[j] = np.mean(CT_ima[labels == ROI[j]]) * Xspace * Yspace * Zspace
                    CT_std[j] = np.std(CT_ima[labels == ROI[j]]) * Xspace * Yspace * Zspace
                    Vol[j] = len(np.where(labels == ROI[j])[0]) * Xspace * Yspace * Zspace
                np.savetxt(dir_name_tmp + "_CT_mean_"+name_atlas[ind_atlas]+".txt",CT_mean,fmt='%.10f')    
                np.savetxt(dir_name_tmp + "_CT_std_"+name_atlas[ind_atlas]+".txt",CT_std,fmt='%.10f')    
                np.savetxt(dir_name_tmp + "_Vol_"+name_atlas[ind_atlas]+".txt",Vol,fmt='%.10f')    
                np.savetxt(dir_name_tmp + "_Vol_norm_"+name_atlas[ind_atlas]+".txt",Vol / Vol_total, fmt='%.10f')    
