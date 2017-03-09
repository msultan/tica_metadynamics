#!/bin/env python
from mpi4py import MPI
import argparse
from msmbuilder.utils import load
from .utils import get_gpu_index
import socket
import numpy as np
import glob
from simtk.unit import *
from .plumed_writer import get_plumed_dict
import os
from simtk.openmm.app import *
from simtk.openmm import *

boltzmann_constant = 0.0083144621

comm = MPI.COMM_WORLD
size = comm.Get_size()
rank = comm.Get_rank()


def run_meta_sim(file_loc="metad_sim.pkl"):
    from tica_metadynamics.load_sim import create_simulation

    metad_sim = load(file_loc)
    #beta is 1/kt
    beta = 1/(boltzmann_constant * metad_sim.temp)

    #get
    my_host_name = socket.gethostname()
    my_gpu_index = get_gpu_index()
    print("Hello from rank %d running tic %d on "
          "host %s with gpu %d"%(rank, rank, my_host_name, my_gpu_index))

    plumed_force_dict = get_plumed_dict(metad_sim) 
    sim_obj, force_group = create_simulation(metad_sim.base_dir, metad_sim.starting_coordinates_folder,
                                my_gpu_index, rank, plumed_force_dict[rank],
                                metad_sim.sim_save_rate, metad_sim.platform)
    if rank ==0 and size>1:
        log_file = open("../swap_log.txt","a")
        header = ["Iteration","S_i","S_j","Eii","Ejj","Eij","Eji","DeltaE","Temp","Beta","Probability","Accepted"]
        log_file.writelines("#{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(*header))
    for step in range(metad_sim.n_iterations):
        #2fs *3000 = 6ps
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
        if size >1:
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

            # return new state and new energies
            new_energy = sim_obj.context.getState(getEnergy=True,groups={force_group}).\
                getPotentialEnergy().value_in_unit(kilojoule_per_mole)
            data = comm.gather((new_state,new_energy), root=0)

            if rank==0:
                s_i_j, e_i_j = data[i]
                s_j_i, e_j_i = data[j]
                delta_e = e_i_i+e_j_j - e_i_j - e_j_i
                probability = np.min((1,np.exp(beta*delta_e)))
                print(e_i_i,e_j_j,e_i_j,e_j_i,probability)
                if np.random.random() < probability :
                    accepted= 1
                    print("Swapping out %d with %d"%(i,j),flush=True)
                else:
                    accepted= 0
                    print("Failed Swap of %d with %d"%(i,j),flush=True)
                    #go back to original state list
                    data[i], data[j] = data[j] , data[i]
                header = [step, i, j, e_i_i,e_j_j,e_i_j,e_j_i,delta_e,metad_sim.temp,beta,probability,accepted]
                log_file.writelines("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(*header))
                log_file.flush()
            else:
                data = None

            #get final state for iteration
            new_state,energy = comm.scatter(data,root=0)
            #print(rank,new_state)
            with open(new_state, 'rb') as f:
                sim_obj.context.loadCheckpoint(f.read())
            #barrier here to prevent 
            comm.barrier()

    if rank==0 and size >1: 
        log_file.close()

    return

def swap_with_msm_state(sim_obj, swap_folder):
    flist = glob.glob(os.path.join(swap_folder,"state*.xml"))
    print("Found %d states"%len(flist),flush=True)
    random_chck = np.random.choice(flist)
    print("Swapping with %s"%random_chck,flush=True)
    state = XmlSerializer.deserialize(open(random_chck).read())
    sim_obj.context.setState(state)
    return sim_obj

def run_msm_meta_sim(file_loc="metad_sim.pkl"):
    from tica_metadynamics.load_sim import create_simulation

    metad_sim = load(file_loc)
    if metad_sim.msm_swap_folder is not None:
        print("Found MSM state folder. Will swap all replicas with the MSM "
              "occasionally",flush=True)
    #beta is 1/kt
    beta = 1/(boltzmann_constant * metad_sim.temp)

    #get
    my_host_name = socket.gethostname()
    my_gpu_index = get_gpu_index()
    print("Hello from rank %d running tic %d on "
          "host %s with gpu %d"%(rank, rank, my_host_name, my_gpu_index))

    plumed_force_dict = get_plumed_dict(metad_sim)
    sim_obj, force_group = create_simulation(metad_sim.base_dir, metad_sim.starting_coordinates_folder,
                                my_gpu_index, rank, plumed_force_dict[rank],
                                metad_sim.sim_save_rate, metad_sim.platform)
    if rank ==0 and size>1:
        log_file = open("../swap_log.txt","a")
        header = ["Iteration","S_i","S_j","Eii","Ejj","Eij","Eji","DeltaE","Temp","Beta","Probability","Accepted"]
        log_file.writelines("#{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(*header))

    for step in range(metad_sim.n_iterations):
        #2fs *3000 = 6ps
        sim_obj.step(metad_sim.swap_rate)

        if metad_sim.msm_swap_folder is not None and np.random.random() < 0.5:
            sim_obj = swap_with_msm_state(sim_obj, metad_sim.msm_swap_folder)
            continue
        #get old energy for just the plumed force
        old_energy = sim_obj.context.getState(getEnergy=True,groups={force_group}).\
            getPotentialEnergy().value_in_unit(kilojoule_per_mole)
        #write the chckpt
        with open("checkpt.chk",'wb') as f:
            f.write(sim_obj.context.createCheckpoint())
        old_state = os.path.abspath("checkpt.chk")
        #send state and energy
        data = comm.gather((old_state,old_energy), root=0)
        if size >1:
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

            # return new state and new energies
            new_energy = sim_obj.context.getState(getEnergy=True,groups={force_group}).\
                getPotentialEnergy().value_in_unit(kilojoule_per_mole)
            data = comm.gather((new_state,new_energy), root=0)

            if rank==0:
                s_i_j, e_i_j = data[i]
                s_j_i, e_j_i = data[j]
                delta_e = e_i_i+e_j_j - e_i_j - e_j_i
                probability = np.min((1,np.exp(beta*delta_e)))
                print(e_i_i,e_j_j,e_i_j,e_j_i,probability)
                if np.random.random() < probability :
                    accepted= 1
                    print("Swapping out %d with %d"%(i,j),flush=True)
                else:
                    accepted= 0
                    print("Failed Swap of %d with %d"%(i,j),flush=True)
                    #go back to original state list
                    data[i], data[j] = data[j] , data[i]
                header = [step, i, j, e_i_i,e_j_j,e_i_j,e_j_i,delta_e,metad_sim.temp,beta,probability,accepted]
                log_file.writelines("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(*header))
                log_file.flush()
            else:
                data = None

            #get final state for iteration
            new_state,energy = comm.scatter(data,root=0)
            #print(rank,new_state)
            with open(new_state, 'rb') as f:
                sim_obj.context.loadCheckpoint(f.read())
            #barrier here to prevent
            comm.barrier()

    if rank==0 and size >1:
        log_file.close()

    return



def parse_commandline():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f','--file', dest='f',
                            default='./metad_sim.pkl',
              help='TICA METAD location file')
    args = parser.parse_args()
    return args

def main():
    args = parse_commandline()
    file_loc = args.f
    run_meta_sim(file_loc)
    return

if __name__ == "__main__":
    main()
