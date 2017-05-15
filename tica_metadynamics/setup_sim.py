#!/bin/evn python

import os,shutil
from .utils import load_yaml_file
from msmbuilder.utils import load,dump
from .render_sub_file import slurm_temp
from .plumed_writer import get_interval, get_plumed_dict

class TicaMetadSim(object):
    def __init__(self, base_dir="./", starting_coordinates_folder="./starting_coordinates",
                            n_tics=1,tica_mdl="tica_mdl.pkl", tica_data="tica_data.pkl",
                            data_frame="feature_descriptor.pkl",
                            featurizer=None,
                            kmeans_mdl =None,
                            nrm = None,
                            grid=False,
                            interval=False,wall=False,
                            pace=2500, stride=2500,
                            temp=300, biasfactor=10, height=1.0,
                            sigma=0.2, delete_existing=False, hills_file="HILLS",
                            bias_file="BIAS", label="metad",
                            sim_save_rate=50000,
                            swap_rate=25000, n_iterations=1000,
                            platform='CUDA',
                            grid_mlpt_factor=.3,
                            render_scripts=False,
                            msm_swap_folder=None,
                            msm_swap_scheme='random',
                            n_walkers = 1):
        self.base_dir = os.path.abspath(base_dir)
        self.starting_coordinates_folder = starting_coordinates_folder
        self.n_tics = n_tics

        if type(featurizer)==str:
            self.featurizer = load(featurizer)
        else:
            self.featurizer = featurizer

        if type(tica_mdl)==str:
            self.tica_mdl = load(tica_mdl)
        else:
            self.tica_mdl = tica_mdl

        if type(tica_data)==str:
            self.tica_data = load(tica_data)
        else:
            self.tica_data = tica_data

        if type(data_frame)==str:
            self.data_frame = load(data_frame)
        else:
            self.data_frame = data_frame

        if type(kmeans_mdl)==str:
            self.kmeans_mdl = load(kmeans_mdl)
        else:
            self.kmeans_mdl = kmeans_mdl

        if type(nrm)==str:
            self.nrm = load(nrm)
        else:
            self.nrm = nrm

        self.grid = grid
        self.grid_mlpt_factor = grid_mlpt_factor
        self.interval=interval
        self.wall = wall
        self.delete_existing = delete_existing
        self.n_iterations = n_iterations
        self.platform = platform
        self.grid_list  = self.interval_list = self.wall_list = None
        self.render_scripts = render_scripts
        self.walker_n = n_walkers

        if self.grid:
            if len(self.grid) < 2:
                raise ValueError("grid must length at least 2 (like [0, 100]")
            if len(self.grid)==2 and type(self.grid[0]) in [float,int]:
                # assume user meant us to specify
                self.grid_list = get_interval(self.tica_data, self.grid[0], self.grid[1])
                print(self.grid_list)
                #add extra mulplicative factor because these these tend to fail
                self.grid_list = [(k[0]-self.grid_mlpt_factor*abs(k[0]),\
                                   k[1]+self.grid_mlpt_factor*abs(k[1])) for k in self.grid_list]
                print(self.grid_list)
            else:
                self.grid_list = self.grid

        if self.interval:
            if len(self.interval) < 2:
                raise ValueError("interval must length 2(like [0, 100] for "
                                 "calculating percentiles")
            if len(self.interval)==2 and type(self.interval[0]) in [float,int]:
               self.interval_list = get_interval(self.tica_data, self.interval[0], self.interval[1])
            else:
                self.interval_list = self.interval

        if self.wall:
            if len(self.wall) < 2:
                raise ValueError("interval must length 2(like [0, 100] for "
                                 "calculating percentiles")
            if len(self.wall)==2 and type(self.wall[0]) in [float,int]:
               self.wall_list = get_interval(self.tica_data,self.wall[0],self.wall[1])
            else:
                self.wall_list = self.wall

        self.pace = pace
        self.stride = stride
        self.temp = temp
        self.biasfactor = biasfactor
        self.height = height
        self.sigma = sigma
        self.hills_file = hills_file
        self.bias_file = bias_file
        self.label = label
        self.sim_save_rate = sim_save_rate
        self.swap_rate = swap_rate
        self.plumed_scripts_dict = None
        self.msm_swap_folder = msm_swap_folder
        self.msm_swap_scheme = msm_swap_scheme


        if self.walker_n > 1:
            print("Multiple walkers found. Modifying current model")
            os.chdir(self.base_dir)
            # base_dir, has n_walker folders called walker_0 ... walkers
            c_base_dir = self.base_dir
            self._setup_walkers_folder()
            for w in range(self.walker_n):
                os.chdir(c_base_dir)
                self.base_dir  =os.path.join(c_base_dir,"walker_%d"%w)
                self.walker_id = w
                os.chdir(base_dir)
                self._setup()
                self._write_scripts_and_dump()
                # make

        else:
            self._setup()
            self._write_scripts_and_dump()




    def _write_scripts_and_dump(self):
        with open(os.path.join(self.base_dir,"sub.sh"),'w') as f:
            f.writelines(slurm_temp.render(job_name="tica_metad",
                              base_dir=self.base_dir,
                              partition="pande",
                              n_tics=self.n_tics))

        if self.render_scripts:
            self.plumed_scripts_dict = get_plumed_dict(self)
            for i in range(self.n_tics):
                with open("%s/tic_%d/plumed.dat"%(self.base_dir,i),'w') as f:
                    f.writelines(self.plumed_scripts_dict[i])

        dump(self,"%s/metad_sim.pkl"%self.base_dir)
        return

    def _setup(self):
        c_dir = os.path.abspath(os.path.curdir)

        os.chdir(self.base_dir)
        for i in range(self.n_tics):
            try_except_delete("tic_%d"%i,self.delete_existing)
        os.chdir(c_dir)
        return

    def _setup_walkers_folder(self):
        # rotuine to setup folder structure
        # in the main folder
        os.chdir(self.base_dir)
        for j in range(self.walker_n):
            try_except_delete("walker_%d"%j, self.delete_existing)
        for i in range(self.n_tics):
            try_except_delete("data_tic%d"%i, self.delete_existing)

        return


def try_except_delete(folder_name, delete_existing=False):
    try:
        os.mkdir(folder_name)
    except FileExistsError:
        if delete_existing:
            print("Deleting existing %s"%folder_name)
            shutil.rmtree(folder_name)
            os.mkdir(folder_name)
        else:
            raise ValueError("Folder already exists and cant delete")
    return

def parse_commandline():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f','--yaml_file', dest='f',
                            default='./sim_params.pkl',
              help='sim_params location file')
    return args

def main():
    args = parse_commandline()
    yaml_file = load_yaml_file(args.f)
    TicaMetadSim(**load_yaml_file(yaml_file))
    return

if __name__ == "__main__":
    main()


