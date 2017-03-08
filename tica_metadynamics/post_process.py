#!/bin/env python
from msmbuilder.utils import load,dump
import os,glob
from subprocess import call
from multiprocessing import Pool
from .utils import concatenate_folder
from .plumed_writer import get_plumed_dict
from jinja2 import Template

def process_folder(job_tuple):
    r1, r2, script = job_tuple
    fname = os.path.join("tic_%d" %r1)
    print(fname)
    base_dir = os.getcwd()
    os.chdir(os.path.join(base_dir,fname))
    try:
        os.remove("r%s_t%s.bias"%(r1,r2))
    except:
        pass
    traj_file_loc = os.path.abspath("../tic_%s/tic_%s.xtc"%(r2,r2))
    plumed_file = "./plumed_reweight_%d_%d.dat"%(r1,r2)
    print(traj_file_loc,plumed_file)
    f = open(plumed_file,'w')
    f.writelines(script)
    f.close()
    cmd = ["plumed","--no-mpi", "driver", "--mf_xtc", traj_file_loc, "--plumed" ,plumed_file]
    ret_code = call(cmd)
    print(ret_code)
    os.chdir(base_dir)
    return

def process_all_replicas(file_loc,redo=True):
    sim_mdl = load(file_loc)
    os.chdir(sim_mdl.base_dir)
    top_loc = glob.glob(os.path.join(sim_mdl.starting_coordinates_folder,"0.pdb"))[0]
    for i in range(sim_mdl.n_tics):
        if redo:
            concatenate_folder("tic_%d"%i, top_loc)

    sim_mdl.pace = 1000000000
    sim_mdl.height = 0
    sim_mdl.stride = 1
    sim_mdl.bias_file ="{{fname}}"
    plumed_scripts_dict = get_plumed_dict(sim_mdl)
    full_dict={}
    for r1 in range(sim_mdl.n_tics):
        for r2 in range(sim_mdl.n_tics):
            full_dict["%d_%d"%(r1,r2)] = Template(plumed_scripts_dict[r1]).render(fname="r%d_t%d.bias"%(r1,r2))

    p = Pool(n_tics)
    jobs =[(r1, r2, full_dict["%d_%d"%(r1,r2)]) for r1 in range(sim_mdl.n_tics)
           for r2 in range(sim_mdl.n_tics)]
    p.map(process_folder,jobs)
    p.close()
    return

def parse_commandline():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f','--file', dest='f',
                            default='./metad_sim.pkl',
              help='TICA METAD location file')
    parser.add_argument('-r','--redo', dest='r',
                            default=True,
              help='Redo trajectory concatenation')
    return args


def main():
    args = parse_commandline()
    file_loc = args.f
    redo = args.r
    process_all_replicas(file_loc,redo)
    return


if __name__ == "__main__":
    main()
