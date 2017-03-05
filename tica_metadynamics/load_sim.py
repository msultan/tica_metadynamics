#!/bin/env python
import os
from simtk.openmm.app import *
from simtk.openmm import *
from simtk.unit import *
from msmbuilder.io import backup
from openmmplumed import PlumedForce
def create_simulation(base_dir, starting_dir,
                      gpu_index,tic_index,
                      plumed_script,
                      sim_save_rate,
                      platform):
    print("Creating simulation for tic %d"%tic_index)
    os.chdir((os.path.join(base_dir,"tic_%d"%tic_index)))


    state = XmlSerializer.deserialize(open("%s/state0.xml"%starting_dir).read())
    system =  XmlSerializer.deserialize(open("%s/system.xml"%starting_dir).read())
    integrator = XmlSerializer.deserialize(open("%s/integrator.xml"%starting_dir).read())
    pdb = app.PDBFile("%s/0.pdb"%starting_dir)
    with open("./plumed_script.dat",'w') as f:
        f.writelines(plumed_script)
    new_f = PlumedForce(str(plumed_script))
    force_group = 30
    new_f.setForceGroup(force_group)
    system.addForce(new_f)
    if platform=='CPU':
        platform = Platform.getPlatformByName("CPU")
        properties =dict()
    else:
        platform = Platform.getPlatformByName("CUDA")
        properties = {'CudaPrecision': 'mixed', 'CudaDeviceIndex': str(gpu_index)}
    simulation = app.Simulation(pdb.topology, system, integrator, platform, properties)
    if os.path.isfile("./checkpt.chk"):
        with open("checkpt.chk",'rb') as f:
            simulation.context.loadCheckpoint(f.read())
    else:
        simulation.context.setState(state)
    print("Done creating simulation for tic %d"%tic_index)

    f = open("./speed_report.txt",'w')
    backup("trajectory.dcd")
    simulation.reporters.append(app.DCDReporter('trajectory.dcd', sim_save_rate))
    simulation.reporters.append(app.StateDataReporter(f, 1000, step=True,\
                                potentialEnergy=True, temperature=True, progress=True, remainingTime=True,\
                                speed=True, totalSteps=200*100, separator='\t'))

    return simulation, force_group

