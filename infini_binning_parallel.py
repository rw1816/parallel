import os
from os import path
import numpy as np
import h5py
import pandas as pd
import math
from natsort import natsorted
from myutils import parallel_chunker
from ML.lagrangian_processing import rotate_xy_pos, translate_part, declare_voxel_space, drop_borders
from ML.infiniSubroutines import bininfini
import matplotlib.pyplot as plt
import time
from mpi4py import MPI

comm = MPI.COMM_WORLD
rank = comm.Get_rank()  # Grab the process ID (integer 0-3 for 4-process run)
size = comm.Get_size()

s=time.time()
# pull out the layer files from the root folder
root_dir = path.abspath('F:\pd\monitoring_data\Ren001')
layer_files = [f.path for f in os.scandir(root_dir) if f.is_file()==True and f.name[0:4]=='AMPM']
layer_files=natsorted(layer_files)
layer_num=np.arange(0, len(layer_files))
layer_height=0.06

build_height= len(layer_num)*layer_height #in mm 
z = np.arange(layer_height, build_height+(layer_height/2), layer_height)

#select voxel size, should be divisible by layer height
bin_size=0.6
layers_per_voxel=int(bin_size//layer_height)

#find the dimensions of the voxel space
ren01_coords=([[-15146.332706093192, 16850.913924731176], [-3314.3213560334552, 6781.117031063317]])
array_x, array_y, array_z, x, y, ref_x, ref_y = declare_voxel_space(layer_files, bin_size, 
                                        build_height, coords=ren01_coords)

#declare blank df
df=pd.DataFrame(columns=('corr_x_req',
             'corr_y_req', 'power_req','power_act','PD1', 'PD2'), dtype='int16')
#be sure to specify dtypes in Pandas, it will default to double and int64!
voxel_layer=0

sendBuf=np.zeros((math.ceil(array_z/size), 12, array_x, array_y), dtype='float64')
"""
!key 1 = PD1, 2 = PD2, 3 = STD1, 4 = STD4, 5 = Range 1, 6 = Range 2, 7 = Max 1, 8=Max2, 9=Min1, 10=Min2 
"""
for start,end in parallel_chunker(len(layer_files), layers_per_voxel, size, rank):
    for filename in (layer_files)[start:end]:
        with h5py.File(filename, 'r') as f:
            print(filename + ' loaded by cpu {0}'.format(rank+1), flush=True)
            data=f.get('data')
            data=np.array(np.uint16(data)[:,[1,3,12,13,15,16]])
            data=data[:,:np.max(np.where(data[:,3]<10))]
            df=df.append(pd.DataFrame(data.astype('int16'), columns=('corr_x_req',
                  'corr_y_req', 'power_req','power_act','PD1', 'PD2')))
            df=df[:np.max(np.where(df.power_act<10))]   #drop border
            
            
    df=df[(x[0]<df.corr_x_req) & (df.corr_x_req<x[1]) & (y[0]<df.corr_y_req) & (df.corr_y_req<y[1])]
    df['corr_x_req'], df['corr_y_req'] = rotate_xy_pos(df.corr_x_req.to_numpy(), df.corr_y_req.to_numpy(), 201)
    df=df[df.index>(max(df.index)*0.01)] 
    df=df[df.PD1>700]
    df['corr_x_req'], df['corr_y_req'] = translate_part(df['corr_x_req'], df['corr_y_req'], 10)
    df['corr_x_req'], df['corr_y_req'] = df['corr_x_req']/200, df['corr_y_req']/200
    df=drop_borders(df)
    
    sendBuf[voxel_layer]=bininfini(array_x, array_y, 
        df.corr_x_req.to_numpy(), df.corr_y_req.to_numpy(), df.PD1.to_numpy(), df.PD2.to_numpy(), bin_size)
    
    voxel_layer=voxel_layer+1

# if sendBuf[-1].all()==0:
#     sendBuf=sendBuf[:-1]
comm.Barrier()
recvBuf=None
if rank==0:
    recvBuf = np.empty([size, math.ceil(array_z/size), 12, array_x, array_y], dtype='float64')

comm.Gather(sendBuf, recvBuf, root=0)
if rank==0:
    print("finished binning!", flush=True)
    
    unpacked=np.zeros((int(recvBuf.shape[0]*recvBuf.shape[1]), 12, array_x, array_y))
    count=0
    for j in range(recvBuf.shape[1]):
        for i in range(recvBuf.shape[0]):
            unpacked[count]=recvBuf[i,j,:,:]    
            count+=1
            
    with h5py.File("F:\\pd\\monitoring_data\\Ren001\\binned_PDpara_600.h5", 'w') as f:
        f.create_dataset("unpacked", shape=unpacked.shape, dtype='float64', data=unpacked)
        f.create_dataset("stacked", shape=recvBuf.shape, dtype='float64', data=recvBuf)
    e=time.time()
    print('Time taken = {0} secs'.format(e-s))
#imageio.volwrite(os.path.normpath("F:\\pd/monitoring_data\\Ren001\\Ren001_PD1voxels_0.6_2.tiff"), binned_PD1.astype('int16'), format='tiff')
#imageio.volwrite(os.path.normpath("F:\\pd/monitoring_data\\Ren001\\Ren001_PD2voxels_0.6_2.tiff"), binned_PD2.astype('int16'), format='tiff')