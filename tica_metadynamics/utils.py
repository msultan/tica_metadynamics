#!/bin/env python
import socket
from mpi4py import MPI

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
