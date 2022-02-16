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
    opts, args = getopt.getopt(sys.argv[1:], "hd:cgebmTRFn", ["help","dir=","convert","degibbs","eddy","biasfield","mask","tensor","response_function","FOD","normalize"])
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
        print('     -d , --dir : Directory of the data (MUST be set)')
        print('     -c , --convert *: Transform the DWI in valid MRtrix files ')
        print('     -g,  --degibbs : Remove Gibbs ringing artifacts' )  
        print("     -e,  --eddy : Perform diffusion image pre-processing using FSL's eddy tool")  
        print('     -b,  --biasfield : Perform Bias field correction')
        print('     -m,  --mask : Estimate the brain mask' )   
        print('     -T,  --tensor : Estimate the DTI and the FA maps.' )
        print('     -R,  --response_function : Estimate the Response Function.' )
        print('     -F,  --FOD : Estimate the FOD.' )
        print('     -n,  --normalize : Normalize the dwi intensity' )
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
        
        file_name_der =  cur_dir+"derivatives/sub-*/ses-*/"
        name_der = glob.glob(file_name_der)
        name_der.sort()
        dir_name_der = name_der
        sub_name_der = [ x.split('/')[-3] for x in name_der]
        ses_name_der =[ x.split('/')[-2] for x in name_der]
        if len(ses_name_der)==0:
            print("Error")
            print("No directory are found in " + cur_dir+"derivatives/sub-*/ses-*/")
            print("Please check the directory tree.")
            sys.exit(-1)


    elif o in ("-c","--convert"):
        #Read dicom with dicom2niix_afni
        print( "Convert DWI to DWI compatible with MRtrix \n")

        try:
            name
        except NameError:
            print("Error with directory")
            print("Directory is no set or empty.")
            print("Please specify the -d or --dir parameters.")
            sys.exit(-1)

        
        for i in range(len(name)):
            nii_file = dir_name[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_dwi.nii.gz'
            bvec_file =dir_name[i] +'dwi/'+sub_name[i]+'_'+ses_name[i]+'_dwi.bvec'
            bval_file = dir_name[i] +'dwi/'+sub_name[i]+'_'+ses_name[i]+'_dwi.bval'
            output_file = dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_dwi.mif'
            cmd = "mrconvert "+nii_file+' -fslgrad '+ bvec_file+' '+ bval_file+' '+ output_file
            print( sub_name[i])
            call(cmd.split())
    
    elif o in ("-g","--degibbs"):

        print( "Remove Gibbs ringing artifacts")
        
        try:
            name_der
        except NameError:
            print("Error with directory")
            print("Directory is no set or empty.")
            print("Please specify the -d or --dir parameters.")
            sys.exit(-1)
        
        tmp = glob.glob(cur_dir+'derivatives/*/*/dwi/*mif')
        if len(tmp) == 0:
            print( "Warning!!! No files previously converted to MRtrix format!")
            sys.exit(-1)
            
        for i in range(len(name_der)):
            input_file = dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_dwi.mif'
            input_file_denoise = dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_denoise_dwi.mif'
            output_file_gibbs = dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_degibbs_dwi.mif'
            print( sub_name[i] ) 
            cmd = "dwidenoise "+input_file+' '+input_file_denoise
            call(cmd.split(" "))
            cmd = "mrdegibbs "+input_file_denoise+' '+ output_file_gibbs
            call(cmd.split())
                

    elif o in ("-e","--eddy"):

        print( "TOPUP or Eddy currecnt correction")
        
        try:
            name_der
        except NameError:
            print("Error with directory")
            print("Directory is no set or empty.")
            print("Please specify the -d or --dir parameters.")
            sys.exit(-1)
        
        tmp = glob.glob(cur_dir+'*/*/fmap/*nii.gz')
        if len(tmp) == 0:
            print( "Warning!!! No files previously converted to MRtrix format!")
            sys.exit(-1)
        
        for i in range(len(name_der)):
            print( sub_name[i] )
            if os.path.isfile(dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_degibbs_dwi.mif'):
                input_file = dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_degibbs_dwi.mif'
            else:
                input_file = dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_dwi.mif'
            
            output_file = dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_eddy_dwi.mif'
            tmp = glob.glob(dir_name[i]+'fmap/'+sub_name[i]+'_'+ses_name[i]+'_*nii.gz')
            try:
             if os.path.isfile(tmp[0]):
                fmap1 = tmp[0].split("/")[-1].split(".")[0] #APA
                fmap2 = tmp[1].split("/")[-1].split(".")[0] #APP
                fmap1_in = dir_name[i] +'fmap/'+fmap1+'.nii.gz'
                fmap1_out = dir_name_der[i]+'fmap/'+fmap1+'.mif'
                fmap1_bvec = dir_name[i]+'fmap/'+fmap1+".bvec"
                fmap1_bval = dir_name[i]+'fmap/'+fmap1+".bval"
                fmap2_in = dir_name[i] +'fmap/'+fmap2+'.nii.gz'
                fmap2_out = dir_name_der[i]+'fmap/'+fmap2+'.mif'
                fmap2_bvec = dir_name[i]+'fmap/'+fmap2+".bvec"
                fmap2_bval = dir_name[i]+'fmap/'+fmap2+".bval"
                cmd = "mrconvert -fslgrad "+fmap1_bvec+" "+fmap2_bval+" "+fmap1_in+" "+fmap1_out
                call(cmd.split(" "))
                cmd = "mrconvert -fslgrad "+fmap2_bvec+" "+fmap2_bval+" "+fmap2_in+" "+fmap2_out
                call(cmd.split(" "))
                
                output_fmap = dir_name_der[i]+'fmap/'+sub_name[i]+'_'+ses_name[i]+'_concat_fmap.mif'
                cmd = "mrcat "+fmap2_out + " "+fmap1_out+" "+output_fmap+" -axis 3"
                call(cmd.split())   
                cmd = "dwipreproc -nthreads 30 -rpe_pair "+input_file+" "+output_file+" -pe_dir PA -se_epi "+output_fmap
             else:
                cmd = "dwipreproc -nthreads 30 -rpe_none "+input_file+" "+output_file+" -pe_dir PA"
             call(cmd.split())
            except:
             print(dir_name[i] + " is not available")
            
    elif o in ("-b","--biasfield"):
        
        print(" Bias field estimation")
        
        
        try:
            name_der
        except NameError:
            print("Error with directory")
            print("Directory is no set or empty.")
            print("Please specify the -d or --dir parameters.")
            sys.exit(-1)
        
        tmp = glob.glob(cur_dir+'derivatives/*/*/dwi/*mif')
        if len(tmp) == 0:
            print( "Warning!!! No files previously converted to MRtrix format!")
            sys.exit(-1)
            
        for i in range(len(name_der)):
            if os.path.isfile(dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_dwi.mif'):
                input_file = dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_dwi.mif'
            if os.path.isfile(dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_degibbs_dwi.mif'):
                input_file = dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_degibbs_dwi.mif'
            if os.path.isfile(dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_eddy_dwi.mif'):
                input_file = dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_eddy_dwi.mif'

            output_file = dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_biasfield_dwi.mif'
            try:
                cmd = 'dwibiascorrect ants -nthreads 20 '+input_file+' '+ output_file
                print( sub_name[i])
                print(cmd)
                call(cmd.split())    
            except:
                print( sub_name[i])
                print("Impossible to estimate the bias field correction! Check your preprocessing and files" )
    
    elif o in ("-m","--mask"):

        print( "Estimate brain mask")
        
        try:
            name_der
        except NameError:
            print("Error with directory")
            print("Directory is no set or empty.")
            print("Please specify the -d or --dir parameters.")
            sys.exit(-1)
        
        tmp = glob.glob(cur_dir+'derivatives/*/*/dwi/*mif')
        if len(tmp) == 0:
            print( "Warning!!! No files previously converted to MRtrix format!")
            sys.exit(-1)
            
        for i in range(len(name_der)):
            if os.path.isfile(dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_dwi.mif'):
                input_file = dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_dwi.mif'
            if os.path.isfile(dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_degibbs_dwi.mif'):
                input_file = dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_degibbs_dwi.mif'
            if os.path.isfile(dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_eddy_dwi.mif'):
                input_file = dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_eddy_dwi.mif'
            if os.path.isfile(dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_biasfield_dwi.mif'):
                input_file = dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_biasfield_dwi.mif'
            
            output_file = dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_brain_mask.mif'
            try:
                cmd = "dwi2mask -nthreads 20 "+input_file+' '+ output_file
                print( sub_name[i])
                call(cmd.split())    
            except:
                print( sub_name[i])
                print("Impossible to create the mask! Check your preprocessing and files" )
    

   
    elif o in ("-T","--tensor"):

        print( "Estimate the dti tensor and the FA/ADC maps")
        
        try:
            name_der
        except NameError:
            print("Error with directory")
            print("Directory is no set or empty.")
            print("Please specify the -d or --dir parameters.")
            sys.exit(-1)
        
        tmp = glob.glob(cur_dir+'derivatives/*/*/dwi/*mif')
        if len(tmp) == 0:
            print( "Warning!!! No files previously converted to MRtrix format!")
            sys.exit(-1)
            
        for i in range(len(name_der)):
            if os.path.isfile(dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_dwi.mif'):
                input_file = dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_dwi.mif'
            if os.path.isfile(dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_degibbs_dwi.mif'):
                input_file = dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_degibbs_dwi.mif'
            if os.path.isfile(dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_eddy_dwi.mif'):
                input_file = dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_eddy_dwi.mif'
            if os.path.isfile(dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_biasfield_dwi.mif'):
                input_file = dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_biasfield_dwi.mif'

            output_file =  dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_dti.mif'
            output_fa =dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_FA.mif'
            output_adc = dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_ADC.mif'

            try:
                cmd = "dwi2tensor -nthreads 20 "+input_file+' '+output_file
                print( sub_name[i])
                call(cmd.split())  
                cmd = "tensor2metric -nthreads 20 "+output_file+' -fa '+output_fa +' -adc '+output_adc
            except:
                print( sub_name[i])
                print("Impossible to normalize! Check your preprocessing and your files (dwi and mask files)" )

    elif o in ("-R","--response_function"):

        print( "Estimate the response function")
        
        try:
            name_der
        except NameError:
            print("Error with directory")
            print("Directory is no set or empty.")
            print("Please specify the -d or --dir parameters.")
            sys.exit(-1)
        
        tmp = glob.glob(cur_dir+'derivatives/*/*/dwi/*mif')
        if len(tmp) == 0:
            print( "Warning!!! No files previously converted to MRtrix format!")
            sys.exit(-1)
            
        for i in range(len(name_der)):
            if os.path.isfile(dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_dwi.mif'):
                input_file = dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_dwi.mif'
            if os.path.isfile(dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_degibbs_dwi.mif'):
                input_file = dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_degibbs_dwi.mif'
            if os.path.isfile(dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_eddy_dwi.mif'):
                input_file = dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_eddy_dwi.mif'
            if os.path.isfile(dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_biasfield_dwi.mif'):
                input_file = dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_biasfield_dwi.mif'

            mask_file = dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_brain_mask.mif'
            output_file_WM =  dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_response_function_wm.txt'
            output_file_GM =  dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_response_function_gm.txt'
            output_file_CSF =  dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_response_function_csf.txt'

            
            cmd = "dwi2response dhollander -nthreads 20 -mask "+mask_file+' '+input_file+' '+output_file_WM+' '+output_file_GM+' '+output_file_CSF
            print(cmd)
            try:
                print( sub_name[i])
                call(cmd.split())
            except:
                print( sub_name[i])
                print("Impossible to estimate the response function! Check your preprocessing and your files (dwi and mask files)" )
        cmd_RF_wm_name = glob.glob(cur_dir+'derivatives/*/*/dwi/*_response_function_wm.txt')
        print("Average White Matter Response Function")
        cmd_RF_wm_name.insert(0,"responsemean")
        cmd_RF_wm_name.append(cur_dir+'derivatives/average_response_function_wm.txt')
        call(cmd_RF_wm_name)
       	print("Average Gray Matter Response Function")
        cmd_RF_gm_name = glob.glob(cur_dir+'derivatives/*/*/dwi/*_response_function_gm.txt')
        cmd_RF_gm_name.insert(0,"responsemean")
        cmd_RF_gm_name.append(cur_dir+'derivatives/average_response_function_gm.txt')
        call(cmd_RF_gm_name)
       	print("Average CSF Response Function")
        cmd_RF_csf_name = glob.glob(cur_dir+'derivatives/*/*/dwi/*_response_function_csf.txt')
        cmd_RF_csf_name.insert(0,"responsemean")
        cmd_RF_csf_name.append(cur_dir+'derivatives/average_response_function_csf.txt')
        call(cmd_RF_csf_name)

    elif o in ("-F","--FOD"):

        print( "Estimate the Fiber Orientation Direction (csd estimation)")
        
        try:
            name_der
        except NameError:
            print("Error with directory")
            print("Directory is no set or empty.")
            print("Please specify the -d or --dir parameters.")
            sys.exit(-1)
        
        tmp = glob.glob(cur_dir+'derivatives/*/*/dwi/*mif')
        if len(tmp) == 0:
            print( "Warning!!! No files previously converted to MRtrix format!")
            sys.exit(-1)
            
        for i in range(len(name_der)):
            if os.path.isfile(dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_dwi.mif'):
                input_file = dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_dwi.mif'
            if os.path.isfile(dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_degibbs_dwi.mif'):
                input_file = dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_degibbs_dwi.mif'
            if os.path.isfile(dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_eddy_dwi.mif'):
                input_file = dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_eddy_dwi.mif'
            if os.path.isfile(dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_biasfield_dwi.mif'):
                input_file = dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_biasfield_dwi.mif'

            mask_file = dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_brain_mask.mif'
            #rf_file =  dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_response_function.txt'
            rf_file_wm = cur_dir+'derivatives/average_response_function_wm.txt'
            rf_file_gm = cur_dir+'derivatives/average_response_function_gm.txt'
            rf_file_csf = cur_dir+'derivatives/average_response_function_csf.txt'
            output_file_wm =  dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_CSD_wm.mif'
            output_file_gm =  dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_gm.mif'
            output_file_csf =  dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_csf.mif'

            #multi shell
            #cmd = "dwi2fod msmt_csd "+input_file+" "+rf_file_wm+" "+output_file_wm+" "+rf_file_gm+" "+output_file_gm+" "+rf_file_csf+" "+output_file_csf+" -mask "+mask_file+" -nthreads 20"
            cmd = "ss3t_csd_beta1 -force "+input_file+" "+rf_file_wm+" "+output_file_wm+" "+rf_file_gm+" "+output_file_gm+" "+rf_file_csf+" "+output_file_csf+" -mask "+mask_file+" -nthreads 20"
            #cmd = "dwi2fod -force csd "+input_file+" "+rf_file+" "+output_file+" -mask "+mask_file+" -nthreads 20"
            print(cmd)    
            try:
                print( sub_name[i])
                call(cmd.split())
            except:
                print( sub_name[i])
                print("Impossible to estimate the response function! Check your preprocessing and your files (dwi and mask files)" )

    elif o in ("-n","--normalize"):

        print( "Normalize the intensity of the FODs")
        
        try:
            name_der
        except NameError:
            print("Error with directory")
            print("Directory is no set or empty.")
            print("Please specify the -d or --dir parameters.")
            sys.exit(-1)
        
        tmp = glob.glob(cur_dir+'derivatives/*/*/dwi/*mif')
        if len(tmp) == 0:
            print( "Warning!!! No files previously converted to MRtrix format!")
            sys.exit(-1)
        
        tmp = glob.glob(cur_dir+'derivatives/*/*/dwi/*_brain_mask.mif')
        if len(tmp) == 0:
            print( "Warning!!! No brain mask files! Please estimate the mask first!")
            sys.exit(-1)
            
        for i in range(len(name_der)):
            input_file_wm = dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_CSD_wm.mif'
            input_file_gm = dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_gm.mif'
            input_file_csf = dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_csf.mif'
            
            mask_file = dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_brain_mask.mif'
            
            output_file_wm =  dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_wmfod_norm.mif'
            output_file_gm =  dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_gm_norm.mif'
            output_file_csf =  dir_name_der[i]+'dwi/'+sub_name[i]+'_'+ses_name[i]+'_csf_norm.mif'

            cmd = "mtnormalise -force -nthreads 20 "+input_file_wm+" "+output_file_wm+" "+input_file_gm+" "+output_file_gm+" "+input_file_csf+" "+output_file_csf+" -mask "+mask_file
            print(cmd)
            try:
                print( sub_name[i])
                call(cmd.split())    
            except:
                print( sub_name[i])
                print("Impossible to normalize! Check your preprocessing and your files (dwi and mask files)" )

    
    else:
        print("Unknown {} option".format(o))
        sys.exit(2)
