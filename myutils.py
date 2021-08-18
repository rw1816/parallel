# -*- coding: utf-8 -*-
"""
Created on Tue Feb 16 16:36:23 2021

@author: rw1816
"""
import os, sys
import numpy as np
import cv2
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import math
 
def matrix_chunker(blocksize, matrix, axis=0, offset=0):
    """
    Generator function to chunk through a matrix along specified axis. Will
    yield blocks of length 'blocksize' along axis = 1,2,3
    
    Inputs: blocksize - the size of the blocks to be yielded
            matrix - input large matrix to be 'chunked'
            optional:
                axis - axis along which to block (in python 0,1,2 notation)
                offset - apply an offset to the start of blocking (int)
                
    Returns: start, end - sequential indicies of block edges
    
    * As a 'generator' function this will yield start, end on the fly when
    called and iterated through. It will return only a generator object if
    called in the standard function manner.
    
    """
    length=matrix.shape[axis]
    index=np.arange(0+offset, length+offset, blocksize)
    index=np.append(index, index[-1]+(length+offset-index[-1]))
    
    for start, end in zip(index[:-1],index[1:]):
        yield start, end
        
def parallel_chunker(limit, chunksize, num_procs, proc_ID):
    

    index=np.arange(0, limit, chunksize)
    remainder=len(index) % num_procs
    if remainder:
        index=np.pad(index, ((0,num_procs-remainder)), 'constant', 
                 constant_values=(-1)).reshape(math.ceil(len(index)/num_procs), num_procs)
    else:
        index=index.reshape((len(index)//num_procs), num_procs)
    
    for i, val in enumerate(index[:,proc_ID]):
        if val==-1:
            break
        
        if chunksize==1:
            yield val
        elif proc_ID==num_procs-1:
            yield val, min(val+chunksize, limit)
        elif index[i,proc_ID+1]==-1:
            yield val, limit
        else:
            yield val, index[i,proc_ID+1] 
        
def limit_step(limit, step):
    
    if step>0:
        index=np.arange(0, limit, step)
        index=np.append(index, index[-1]+(limit-index[-1]))
        for start, end in zip(index[:-1], index[1:]):
            yield start, end
    
    elif step<0:
        index=np.arange(limit, 0, step)
        index=np.append(index, 0)
        for start, end in zip(index[:-1], index[1:]):
            yield start, end
            
def check_file(filename, folder):
    
    if filename in [f.name for f in os.scandir(folder)]:
        try:
            ovr=input('File {0} already exists. Do you want to overwrite? Y/N '.format(filename))
        
            if ovr.lower()=='y':
                os.remove(os.path.join(folder, filename))
            
            elif ovr.lower()=='n':
                sys.exit('Aborting...no overwrite')
        except ValueError:
            print('Not a valid response')
            
def get_crop_coords(x, y):
    if 1:
        fig, ax = plt.subplots(figsize=(12,12))
        ax.set_aspect('equal')
        ax.set_title('Select NW and SE corners of crop region')
        ax.plot(x,y)
        global coords
        coords = []
        
        def onclick(event):
            coords.append([event.xdata, event.ydata])
            print(coords)
        
        cid=fig.canvas.mpl_connect('button_press_event', onclick)
        plt.pause(15)
        if len(coords)==2:
            return coords
    return coords

def grab_files(folder_path, ext='.h5', first4=None):
    """
    Function to get a list of all relevant files, or a file series, 
    in a folder, as os.path objects.
    
    Args in:
        folder_path = full path to the desired folder, as a string
    Optional:
        ext = file extension for the file series desired, string
        first4 = First four letters of the filename, to help with identification,
                    again passed as a string
                    
    Returns:
        A list of path objects for the matching file series in the folder
    
    """
    folder_path=os.path.normpath(folder_path)
    if first4 in locals():
        # incorporate the excerpt of the filename
        dir_List=[f for f in os.scandir(folder_path) if f.is_file()==True and 
                  f.name[-len(ext):]==ext and f.name[:4]==first4]         
    else:
        #do it without the excerpt
        dir_List=[f for f in os.scandir(folder_path) if f.is_file()==True and 
                  f.name[-len(ext):]==ext]
    
    return dir_List