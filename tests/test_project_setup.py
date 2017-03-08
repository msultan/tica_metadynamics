#!/bin/env python
import os
from msmbuilder.utils import load
from tica_metadynamics.setup_sim import TicaMetadSim
from mdtraj.utils import enter_temp_directory
from mdtraj.testing import eq
if os.path.isdir("tests"):
    base_dir = os.path.abspath(os.path.join("./tests/test_data"))
else:
    base_dir = os.path.abspath(os.path.join("./test_data"))

def test_setup():
    tica_mdl = load(os.path.join(base_dir,"landmark_mdl/tica_mdl.pkl"))
    tica_data = load(os.path.join(base_dir,"landmark_mdl/tica_features.pkl"))
    df = load(os.path.join(base_dir,"./landmark_mdl/feature_descriptor.pkl"))
    with enter_temp_directory():
        cur_dir = os.path.abspath(os.path.curdir)
        TicaMetadSim(base_dir=cur_dir,tica_data=tica_data, tica_mdl=tica_mdl,
                     data_frame=df, grid=False, interval=False,wall=False,
                     render_scripts=True)

        metad_sim = load("./metad_sim.pkl")

        assert eq(tica_mdl.components_, metad_sim.tica_mdl.components_)
        for i in range(metad_sim.n_tics):
            assert os.path.isdir("tic_%d"%i)
            assert os.path.isfile(("tic_%d/plumed.dat"%i))
        assert os.path.isfile("sub.sh")

def test_delete():
    tica_mdl = load(os.path.join(base_dir,"landmark_mdl/tica_mdl.pkl"))
    tica_data = load(os.path.join(base_dir,"landmark_mdl/tica_features.pkl"))
    df = load(os.path.join(base_dir,"./landmark_mdl/feature_descriptor.pkl"))
    with enter_temp_directory():
        cur_dir = os.path.abspath(os.path.curdir)
        TicaMetadSim(base_dir=cur_dir, tica_data=tica_data,tica_mdl=tica_mdl,
                     data_frame=df, grid=False, interval=False,render_scripts=True)


        f = open("tic_0/rand.txt",'w')
        f.writelines("t")
        f.close()

        TicaMetadSim(base_dir=cur_dir, tica_mdl=tica_mdl,tica_data=tica_data,
                     data_frame=df, grid=False, interval=False,
                     delete_existing=False)

        assert os.path.isfile("tic_0/rand.txt")


        TicaMetadSim(base_dir=cur_dir, tica_mdl=tica_mdl,tica_data=tica_data,
                     data_frame=df, grid=False, interval=False,
                     delete_existing=True)

        assert not os.path.isfile("tic_0/rand.txt")
