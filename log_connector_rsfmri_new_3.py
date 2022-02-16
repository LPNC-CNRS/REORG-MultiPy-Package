#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 25 2020

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
import nilearn as ni
from nilearn.input_data import NiftiLabelsMasker
from nilearn.connectome import ConnectivityMeasure
import numpy as np
import pandas as pd
import json
import ants
import scipy.stats as stats
from rpy2.robjects.packages import importr
import threading 
################


class prepfmriThread (threading.Thread):
    def __init__(self, name, Anat): 
        threading.Thread.__init__(self)  # = donnée supplémentaire
        self.name = name
        self.Anat = Anat
    def run(self):
        print("thread itération "+self.name)
        if self.Anat == 0:
            cmd= "fmriprep "+cur_dir+" "+cur_dir+"/derivatives/ participant --participant-label "+self.name+" -t rest --fs-no-reconall --clean-workdir --output-spaces anat func"
            call(cmd.split(" "))
        if self.Anat == 1:
            cmd= "fmriprep "+cur_dir+" "+cur_dir+"/derivatives/ participant --participant-label "+self.name+" -t rest --fs-no-reconall --clean-workdir --output-spaces anat func --anat-derivatives "+cur_dir+"/derivatives/fmriprep/"
            call(cmd.split(" "))
        


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
    opts, args = getopt.getopt(sys.argv[1:], "hd:Apc:a:sw", ["help","dir=","Anat","preproc","confounds=","atlas=","signal","wavelet"])
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
        print('     -A , --Anat : Consider previous anatomical preprocessing from fmriprep')
        print('     -p , --preproc : Preprocessing with fmriprep')
        print('     -c , --confounds: json file with the names of the confound')
        print('     -a , --atlas: json file with the names of the atlas')
        print('     -s , --signal : Estimate the cleaning signal and the correlation matrix')  
        print('     -w , --wavelet : Estimate the connectome with Brainwaver')  
        sys.exit()


    elif o in ("-d", "--dir"):
        #Lecture des fichiers
        cur_dir = a
        print( a ) 
        if os.path.isdir(cur_dir)==False:
            print("Error")
            print(cur_dir + " is not a directory.")
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
            print("No directory are found in " + cur_dir+"/sub-*/ses-*/")
            print("Please check the directory tree.")
            sys.exit(-1)
        
        file_name = cur_dir+"/sub-*/ses-*/func/*"
        if len(glob.glob(file_name)) == 0:
            print("Error")
            print("No files are found are found in " + cur_dir+"/sub-*/ses-*/func/")
            print("Please check the directory tree.")
            sys.exit(-1)

    elif o in ("-A","--Anat"):
        print("Consider previous Anatomical preprocessing from fmriprep \n")
        Anat = 1


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
            tmp_nb = int(len(dir_name)/10)+1
            for i in range(tmp_nb):
              threads = []
              for j in range(10):
                try:
                 rs_file = sub_name[i*10+j]
                 t = prepfmriThread(rs_file,Anat)
                 threads.append(t)
                except:
                 print(" ")              
              # Start all threads
              for x in threads:
                x.start()
              # Wait for all of them to finish
              for x in threads:
                x.join()  
              os.removedirs("work")

        elif which('fmriprep-docker') is not None:
            cmd= "fmriprep-docker "+cur_dir+" "+cur_dir+"/derivatives/ participant -t rest --fs-no-reconall --clean-workdir --output-spaces anat func"
            call(cmd.split(" "))
        else:
            print("Error fmriprep or fmriprep-docker is not installed")
            print("Please install fmriprep before starting the preprocessing step")
            sys.exit(-1)
            
    elif o in ("-c","--confounds"):
        #Get the confounds name from a json file for the
        print("Set the confounds for the signal estimation\n") 
        
        confound_file = a
        if os.path.isfile(confound_file)==False:
            print("Error")
            print( confound_file + " is not a file. Please verify your file.")
            sys.exit(-1)
            
        print( confound_file)
        try:
            data_json = json.load(open(confound_file))
        except:
            print( confound_file + " is not a correct JSON. Please verify your file.")
            sys.exit(-1)
        
        #Test the atlas files
        try:
            confound_name = data_json["Confound"]
        except:
            print( "No Confound key in the json file. It is mandatory.")
            print( "Please check your json file.")
            sys.exit(-1)
        
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
            
    elif o in ("-s","--signal"):
        print("Estimate the signal without confounds")  
        #Get the atlas and labels image
        try:
            atlas
        except:
            print( "The parameter -a,--atlas must be set for this step")
        try:
            confound_name
        except:
            print( "The parameter -c,--confound must be set for this step")
            
        #Load the atlas and the labels
        atlas_img = []
        labels_img = []
        for tmp_atlas in atlas:
            atlas_img.append( ants.image_read(tmp_atlas) )
        for tmp_labels in labels:
            labels_img.append( ants.image_read(tmp_labels) )


        #Load the atlas and the labels
        for i in range(len(dir_name)):
            GM_mask_file = cur_dir + "/derivatives/fmriprep/"+sub_name[i]+"/anat/"+sub_name[i]+"_GM_mask.nii.gz"
            if not os.path.exists(GM_mask_file):
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
                
                segs = ants.image_read(seg_anat_file)
                #convert FSL segmentation labels to ANTS label
                ind1 = np.where(segs.numpy()==1)
                ind2 = np.where(segs.numpy()==2)
                ind3 = np.where(segs.numpy()==3)
                segs[ind1] = 2  #GM label
                segs[ind2] = 3  #WM label
                segs[ind3] = 1  #CSF label
                segs[ind_cortstruct] = 2 #cortical structure label
                ants.image_write(segs,seg_anat_file2)
                segs[ind1] = 1
                segs[ind2] = 0
                segs[ind3] = 0
                segs[ind_cortstruct] = 1
                ants.image_write(segs,GM_mask_file)
                
        
        for ind_sub in range(len(dir_name)):
         try: 
            #Read the T1w for each subject
            T1_name = cur_dir + "/derivatives/fmriprep/" +sub_name[ind_sub]+ "/anat/"+ sub_name[ind_sub]+ "_desc-preproc_T1w.nii.gz"
            GM_name =cur_dir + "/derivatives/fmriprep/" +sub_name[ind_sub]+ "/anat/"+sub_name[ind_sub]+"_GM_mask.nii.gz"
            mask_name_file = cur_dir + "/derivatives/fmriprep/" +sub_name[ind_sub]+ "/anat/"+ sub_name[ind_sub]+ "_dseg.nii.gz"
            T1_img = ants.image_read(T1_name)
            img_mask = ants.image_read(mask_name_file)
            GM_mask = ants.image_read(GM_name)
            for ind_atlas in range(len(atlas)):
                #Mask the skull
                ind = np.where(img_mask.numpy() == 0)
                T1_img[ind] = 0
                ind_GM = np.where(GM_mask.numpy() == 0)
                #Estimate the transformation between template and subject
                atlas2T1_tx = ants.registration(fixed = T1_img, moving = atlas_img[ind_atlas], type_of_transform = 'SyN' ) 
                #Apply the transformation on the labels
                labels2T1_imgs = ants.apply_transforms(fixed = T1_img, moving= labels_img[ind_atlas], transformlist=atlas2T1_tx['fwdtransforms'],interpolator='nearestNeighbor')
                labels2T1_imgs_tmp = labels2T1_imgs.copy()
                labels2T1_imgs_tmp[ind_GM] = 0
                label = np.setdiff1d(np.unique(labels2T1_imgs.numpy()),np.unique(labels2T1_imgs_tmp.numpy()))
                for label_tmp in label:
                    labels2T1_imgs_tmp[np.where(labels2T1_imgs.numpy() == label_tmp)] = label_tmp
                labels2T1_name = cur_dir+"/derivatives/" +sub_name[ind_sub]+ "/" +ses_name[ind_sub]+ "/anat/"+ sub_name[ind_sub] + "_" +ses_name[ind_sub]+"_"+"labels_"+name_atlas[ind_atlas]+"2T1.nii.gz"
                ants.image_write(labels2T1_imgs_tmp, labels2T1_name)
                #Estimate the time series over the ROI of the atlas
                #masker = NiftiLabelsMasker(labels_img=labels2T1_name) 
                masker = NiftiLabelsMasker(labels_img=labels2T1_name)
                cofound = pd.read_csv(cur_dir+ "derivatives/fmriprep/" +sub_name[ind_sub]+"/" +ses_name[ind_sub]+"/func/"+sub_name[ind_sub]+"_" +ses_name[ind_sub]+ "_task-rest_desc-confounds_regressors.tsv",delimiter="\t") 
                confound_filter = cofound[confound_name]
                time_series = masker.fit_transform(cur_dir + "derivatives/fmriprep/" +sub_name[ind_sub]+"/" +ses_name[ind_sub]+"/func/" +sub_name[ind_sub]+"_" +ses_name[ind_sub]+"_task-rest_space-T1w_desc-preproc_bold.nii.gz", confounds=confound_filter.values) 
                #Save the time series
                df_time_series = pd.DataFrame(time_series)
                df_time_series.to_csv(cur_dir + "derivatives/"+sub_name[ind_sub]+"/" +ses_name[ind_sub] +"/func/"+sub_name[ind_sub]+"_" +ses_name[ind_sub]+"_"+name_atlas[ind_atlas]+"_atlas_task-rest_time_series.csv",index=False)
                #Estimate the functionnal connectome based on correlation
                correlation_measure = ConnectivityMeasure(kind='correlation')
                correlation_matrix = correlation_measure.fit_transform([time_series])[0]
                df_corr = pd.DataFrame(correlation_matrix)
                df_corr.to_csv(cur_dir + "derivatives/"+sub_name[ind_sub] + "/" +ses_name[ind_sub]+"/func/"+sub_name[ind_sub]+"_"+ses_name[ind_sub]+"_"+ name_atlas[ind_atlas]+"_atlas_task-rest_connectome.csv",index=False)
         except:
            print("Error with "+sub_name[ind_sub]+ "/" +ses_name[ind_sub] )       

    elif o in ("-w","--wavelet"):
        print("Estimate the correlation matrix with wavelet")
       	#Get the atlas and labels image

        try:
            atlas
        except:
            print( "The parameter -a,--atlas must be set for this step")

        #import the brainwaver package
        brainwaver = importr('brainwaver')

        #Activate conversion between R and numpy array

        import rpy2.robjects.numpy2ri
        rpy2.robjects.numpy2ri.activate()

        for ind_sub in range(len(dir_name)):
          try:
            for ind_atlas in range(len(atlas)):
               	#Read the time series
                tmp_name = cur_dir + "derivatives/"+sub_name[ind_sub]+"/" +ses_name[ind_sub] +"/func/"+sub_name[ind_sub]+"_" +ses_name[ind_sub]+"_"+name_atlas[ind_atlas]+"_atlas_task-rest_"
                df_time_series = pd.read_csv(tmp_name + "time_series.csv")
                #Estimate the functionnal connectome based on correlation
                corr_matrix = brainwaver.const_cor_list(df_time_series.values)
                #Save the wavelet at the level 3 and 4
                wave3 = pd.DataFrame( np.array(corr_matrix[2]) )
                wave4 = pd.DataFrame( np.array(corr_matrix[3]) )
                wave3.to_csv( tmp_name + "connectome_wave3.csv",index=False)
                wave4.to_csv( tmp_name + "connectome_wave4.csv",index=False)
          except:
            print("Error with "+ sub_name[ind_sub]+"/" +ses_name[ind_sub])
