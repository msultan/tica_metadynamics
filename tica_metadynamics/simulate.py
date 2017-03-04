#!/bin/env python
from mpi4py import MPI
import argparse
from msmbuilder.utils import load
from .load_sim import create_simulation
from .utils import get_gpu_index
import socket
import numpy as np
from simtk.unit import *

import os
boltzmann_constant = 0.0083144621

comm = MPI.COMM_WORLD
size = comm.Get_size()
rank = comm.Get_rank()


def run_meta_sim(file_loc="metad_sim.pkl"):
    metad_sim = load(file_loc)
    #beta is 1/kt
    beta = 1/(boltzmann_constant * metad_sim.temp)

    #get
    my_host_name = socket.gethostname()
    my_gpu_index = get_gpu_index()
    print("Hello from rank %d running tic %d on "
          "host %s with gpu %d"%(rank, rank, my_host_name, my_gpu_index))

    plumed_force_dict = get_plumed_dict(metad_sim) 
    sim_obj, force_group = create_simulation(metad_sim.base_dir, metad_sim.starting_coordinates,
                                my_gpu_index, rank, plumed_force_dict[rank],
                                metad_sim.sim_save_rate)

    n_rounds = metad_sim.sim_time*1000*1000/2*swap_rate
    for step in range(int(n_rounds)):
        #2fs *5000 =10ps
        sim_obj.step(metad_sim.swap_rate)
        #get old energy for just the plumed force
        old_energy = sim_obj.context.getState(getEnergy=True,groups={force_group}).\
            getPotentialEnergy().value_in_unit(kilojoule_per_mole)
        #write the chckpt
        with open("checkpt.chk",'wb') as f:
            f.write(sim_obj.context.createCheckpoint())
        old_state = os.path.abspath("checkpt.chk")
        #send state and energy
        data = comm.gather((old_state,old_energy), root=0)

        if rank==0:
            #rnd pick 2 states
            i,j =  np.random.choice(np.arange(size), 2, replace=False)
            s_i_i,e_i_i = data[i]
            s_j_j,e_j_j = data[j]
            #swap out states
            data[j], data[i] = data[i],data[j]
        else:
            data = None

        #get possible new state
        new_state = None
        new_state,energy = comm.scatter(data,root=0)
        #set state
        with open(new_state, 'rb') as f:
            sim_obj.context.loadCheckpoint(f.read())

        #sim_obj.context.setState(new_state)

        # return new state and new energies
        new_energy = sim_obj.context.getState(getEnergy=True,groups={1}).\
            getPotentialEnergy().value_in_unit(kilojoule_per_mole)
        data = comm.gather((new_state,new_energy), root=0)

        if rank==0:
            s_i_j, e_i_j = data[i]
            s_j_i, e_j_i = data[j]
            print(e_i_i,e_j_j,e_i_j,e_j_i,np.min((1,np.exp(beta*(e_i_i+e_j_j - e_i_j - e_j_i)))))
            if np.random.rand() < np.min((1,np.exp(beta*(e_i_i+e_j_j - e_i_j - e_j_i)))):
                #do nothing and go forward
                print("Swapping out %d with %d"%(i,j),flush=True)
            else:
                print("Failed Swap of %d with %d"%(i,j),flush=True)
                #go back to original state list
                data[i], data[j] = data[j] , data[i]
        else:
            data = None

        #get final state for iteration
        new_state,energy = comm.scatter(data,root=0)
        #print(rank,new_state)
        with open(new_state, 'rb') as f:
            sim_obj.context.loadCheckpoint(f.read())

        comm.barrier()
        #sim_obj.context.setState(new_state)
    #    comm.barrier()

    return




def parse_commandline():

    parser = argparse.ArgumentParser()
    parser.add_argument('-f','--file', dest='f',
                        default='./metad_sim.pkl',
          help='TICA METAD location file')

    return args

def main():
    args = parse_commandline()
    file_loc = args.f
    run_meta_sim(file_loc)
    return

if __name__ == "__main__":
    main()
