import h5py
from mpi4py import MPI
import os
from natsort import natsorted
import numpy as np
import time

tic=time.time()

comm = MPI.COMM_WORLD
rank = comm.Get_rank()  # Grab the process ID (integer 0-3 for 4-process run)
size = comm.Get_size()

#get data to be read by individal procs
root_dir = os.path.abspath('F:\pd\monitoring_data\Ren001')
in_data=[f.path for f in os.scandir(root_dir) if f.is_file()==True and f.name[0:4]=='AMPM']
in_data=natsorted(in_data)

#open shared file for writing 
#f = h5py.File('MPI_test.h5', 'w', driver='mpio', comm=MPI.COMM_WORLD)
#dset = f.create_dataset('test', (2,10,10), dtype='i')

start_points=np.array((20,0))

for i in range(5):
        with h5py.File(in_data[start_points[rank]+i], 'r') as f:
            #data=f.get('data')
            #data=np.array(np.uint16(data)[:,[1,3,12,13,15,16]])
            sendBuf=np.ones((2,2,5,5), dtype='uint8')*rank

        print("file {0} read by proc {1}".format((in_data[start_points[rank]+i]), rank))
            
recvBuf=None
if rank==0:
    recvBuf = np.empty([size, 2,2,5,5], dtype='uint8')
comm.Gather(sendBuf, recvBuf, root=0)
if rank==0:
    print(recvBuf)


# if rank == 0:
#     for i in range(size):
#         assert np.allclose(recvbuf[i,:], i)
#f.close()
toc=time.time()
print('{0} files processed in {1} secs by {2} procs'.format(rank*5, toc-tic, size))