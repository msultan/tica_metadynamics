#!/bin/env python
import socket
from mpi4py import MPI
import mdtraj as md

comm = MPI.COMM_WORLD
size = comm.Get_size()
rank = comm.Get_rank()


def get_gpu_list(hst_list):
    gpu_list=[]
    host_name_dict={}
    for i,v in enumerate(hst_list):
        if v in host_name_dict:
            host_name_dict[v] += 1
        else:
            host_name_dict[v] = 0
        gpu_list.append(host_name_dict[v])
    return gpu_list


def get_gpu_index():
    my_host_name = socket.gethostname()
    host_name_list = comm.gather(my_host_name, root=0)
    print(my_host_name)
    data=None
    if rank==0:
        print(host_name_list)
        gpu_list = get_gpu_list(host_name_list)
        data = [i for i in zip(host_name_list,gpu_list)]
    hostname, gpu_index = comm.scatter(data,root=0)
    assert hostname==my_host_name
    return gpu_index


def concatenate_folder(fname, top_loc="./starting_coordinates/0.pdb"):
    flist = sorted(glob.glob("./%s/trajectory.dcd.bak.*"%fname), key=keynat)
    flist.extend(glob.glob("./%s/trajectory.dcd"%fname))
    print(flist)
    top = md.load(top_loc)
    trj_list=[]
    for i in flist:
        try:
            trj_list.append(md.load_dcd(i,top=top))
        except:
            pass


    trj = trj_list[0] + trj_list[1:]
    trj.remove_solvent().save_xtc("%s/%s.xtc"%(fname,fname))
    print("Found %d trajs"%len(trj_list))

    return