#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Mar  8 09:55:38 2018

@author: Felix Renard
"""

import sys
import getopt
import os
import csv
from subprocess import call
import glob
import shutil
import nibabel as nib
import numpy as np
import json
import errno

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

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise
#############

try:
    opts, args = getopt.getopt(sys.argv[1:], "hd:f:F:", ["help","dir=","file=","File="])
except getopt.GetoptError as err:
    # Affiche l'aide et quitte le programme
    print(err) # Va afficher l'erreur en anglais
    print('Please see the help.') # Fonction à écrire rappelant la syntaxe de la commande
    sys.exit(2)
 
output = None
verbose = False

if len(opts) == 0:
    print( "No parameter has been given.")
    print( "Try -h")

if len([item for item in opts if item[0] == '-h']) == 1:
	print('Help of the BIDS database creation:')
	print('* means that no parameter is needed \n')
	print('     -h , --help: print the help')
	print('     -d , --dir : Source directory (MUST be set)')
	print('     -F , --File : the json for data_description')
	print('     -f , --file : the json for setup group study ')
	sys.exit()

if len([item for item in opts if item[0] == '-d']) == 0:
    print( 'Source Directory must be set. Check -h or the help.')
    sys.exit(1)


if len([item for item in opts if item[0] == '-f']) == 0:
    print( 'The json config file must be set. Check -h or the help.')
    sys.exit(1)
    

if len([item for item in opts if item[0] == '-F']) == 0:
    print( 'The json data_description must be set. Check -h or the help.')
    sys.exit(1)

print( opts)
for o, a in opts:
    if o == "-v":
        # On place l'option 'verbose' à True
        verbose = True


    elif o in ("-h", "--help"):
        # On affiche l'aide
        print('Help of the BIDS database creation:')
        print('* means that no parameter is needed \n')
        print('     -h , --help: print the help')
        print('     -d , --dir : Source directory (MUST be set)')
        print('     -F , --File : the json for data_description')
        print('     -f , --file : the json for setup group study ')
        sys.exit()


    elif o in ("-d", "--dir"):
        #Lecture des fichiers
        cur_dir = a
        
        print( "\nThe directory for the BIDS database is "+a +"\n")
        if os.path.isdir(cur_dir)==False:
            print("Error")
            print( cur_dir + " is not a directory.")
            sys.exit(-1)
    

    elif o in ("-F","--File"):
        #Transformation des PAR REC avec dicom2nii
        print( "Read data_description.json \n")
        cur_file = a
        if os.path.isfile(cur_file)==False:
            print("Error")
            print( cur_dir + " is not a file. Check you file.")
            sys.exit(-1)
            
        try:
            data_description = json.load(open(cur_file))
        except:
            print( cur_file + " is not a correct JSON. Please verify your file.")
            sys.exit(-1)
        
        try:
            NameDB = data_description["Name"]
        except:
            print( 'No name is given for the study')
            print( 'Please check your '+cur_file+' file!')
            sys.exit(-1)
        
        if os.path.isdir(cur_dir +"/"+ NameDB) == False:
            os.mkdir(cur_dir +"/"+ NameDB)
            cur_DB = cur_dir +"/"+ NameDB +"/"
            os.mkdir(cur_DB + "code/")
            os.mkdir(cur_DB + "derivatives/")
            os.mkdir(cur_DB + "stimuli/")
            os.mkdir(cur_DB + "sourcedata/")
            shutil.copy(cur_file,cur_DB)
        else:
            print( "The repertory "+cur_dir +"/"+ NameDB+ " already exists!")
            print( "Remove it or change the name!")
            data_description = json.load(open(cur_file))
        
        
    elif o in ("-f","--file"):
        #print "Create arborescence \n"
        print( NameDB)
        print( cur_dir)
        print( cur_DB)
        cur_file = a
        if os.path.isfile(cur_file)==False:
            print("Error")
            print( cur_dir + " is not a file. Please verify your file.")
            sys.exit(-1)
            
        print( cur_file)
        try:
            data_json = json.load(open(cur_file))
        except:
            print( cur_file + " is not a correct JSON. Please verify your file.")
            sys.exit(-1)
            
        try:
            Subject = data_json["Subject"]
        except:
            print( "No Subject in the json file. It is mandatory.")
            print( "Please check your json file.")
            sys.exit(-1)
            
        try:
            Session = data_json["Session"]
        except:
            print( "Warning!!! ")
            print( "No Session in the json file. It is recommanded.")
            print( "Please check your json file if needed.")
            Session = [0]
            
        print( '\nList of Subject =' )
        print( Subject )
        print( '\n')
        print( '\nNumber of Sessions =')
        print( Session)
        for name in Subject:
            os.mkdir(cur_DB +"sub-"+ name)
            for ses in range(len(Session)):
                os.mkdir(cur_DB +"sub-"+ name+"/ses-"+np.str(Session[ses])+"/")
                os.mkdir(cur_DB +"sub-"+ name+"/ses-"+np.str(Session[ses])+"/anat")
                os.mkdir(cur_DB +"sub-"+ name+"/ses-"+np.str(Session[ses])+"/func")
                os.mkdir(cur_DB +"sub-"+ name+"/ses-"+np.str(Session[ses])+"/dwi")
                os.mkdir(cur_DB +"sub-"+ name+"/ses-"+np.str(Session[ses])+"/fmap")
            os.mkdir(cur_DB +"/sourcedata/sub-"+ name)
            for ses in range(len(Session)):
                os.mkdir(cur_DB +"/sourcedata/sub-"+ name+"/ses-"+np.str(Session[ses])+"/")
                os.mkdir(cur_DB +"/sourcedata/sub-"+ name+"/ses-"+np.str(Session[ses])+"/anat")
                os.mkdir(cur_DB +"/sourcedata/sub-"+ name+"/ses-"+np.str(Session[ses])+"/func")
                os.mkdir(cur_DB +"/sourcedata/sub-"+ name+"/ses-"+np.str(Session[ses])+"/dwi")
                os.mkdir(cur_DB +"/sourcedata/sub-"+ name+"/ses-"+np.str(Session[ses])+"/fmap")
            os.mkdir(cur_DB +"/derivatives/sub-"+ name)
            for ses in range(len(Session)):
                os.mkdir(cur_DB +"/derivatives/sub-"+ name+"/ses-"+np.str(Session[ses])+"/")
                os.mkdir(cur_DB +"/derivatives/sub-"+ name+"/ses-"+np.str(Session[ses])+"/anat")
                os.mkdir(cur_DB +"/derivatives/sub-"+ name+"/ses-"+np.str(Session[ses])+"/func")
                os.mkdir(cur_DB +"/derivatives/sub-"+ name+"/ses-"+np.str(Session[ses])+"/dwi")
                os.mkdir(cur_DB +"/derivatives/sub-"+ name+"/ses-"+np.str(Session[ses])+"/fmap")


            #sub-<participant_label>[/ses-<session_label>]/<data_type>/
            

    else:
        print("Unknown {} option".format(o))
        sys.exit(2)
