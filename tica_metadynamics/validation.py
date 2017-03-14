
#!/bin/evn python
from subprocess import call
from mdtraj.utils import enter_temp_directory
from msmbuilder.utils import  load
import warnings
def validate_plumed_script(sim_obj_loc = "metad_sim.pkl", featurizer=None, traj=None):
    sim_obj = load(sim_obj_loc)
    if featurizer is None and not hasattr(sim_obj, featurizer):
        raise ValueError("Featuizer cant be none if sim_obj doesnt "
                         "have featurizer object")
    if traj is None:
        warnings.warn("No test trj found")
    # with enter_temp_directory():
    #     for i in range()
    f = open("./plumed.dat", 'w')
    f.writelines(globals()["plumed_%d" % tic_index].format(bias="r%dt%d.bias" % (tic_index, i)))
    f.close()

    cmd = ["plumed", "--no-mpi", "driver", "--mf_xtc", "../tic_%s/tic_%s.xtc" % (i, i)]
    ret_code = call(cmd)
    return