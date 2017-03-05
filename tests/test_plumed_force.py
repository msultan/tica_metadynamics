#!/bin/env python
import os
from msmbuilder.utils import load
from tica_metadynamics.setup_sim import TicaMetadSim
from mdtraj.utils import enter_temp_directory
from tica_metadynamics.simulate import run_meta_sim
if os.path.isdir("tests"):
    base_dir = os.path.abspath(os.path.join("./tests/test_data"))
else:
    base_dir = os.path.abspath(os.path.join("./test_data"))

def test_plumed_run():
    tica_mdl = load(os.path.join(base_dir,"dihedral_mdl/tica_mdl.pkl"))
    df = load(os.path.join(base_dir,"./dihedral_mdl/feature_descriptor.pkl"))
    starting_coordinates_folder = os.path.join(base_dir,"starting_coordinates")
    with enter_temp_directory():
        cur_dir = os.path.abspath(os.path.curdir)
        TicaMetadSim(base_dir=cur_dir,starting_coordinates_folder=starting_coordinates_folder,
                     tica_mdl=tica_mdl,
                     data_frame=df, grid=False, interval=False,
                     platform='CPU',n_iterations=1,
                     swap_rate=5,sim_save_rate=10,pace=1,
                     stride=1)
        meta_sim = load("./metad_sim.pkl")
        run_meta_sim("./metad_sim.pkl")
        for i in range(1):
            for j in [meta_sim.bias_file, meta_sim.hills_file,\
                      "speed_report.txt","trajectory.dcd","plumed_script.dat",\
                      "checkpt.chk"]:
                print(i,j)
                assert os.path.isfile(os.path.join(cur_dir,"tic_%d"%i,j))
        assert not os.path.isfile("swap_log.txt")
    
