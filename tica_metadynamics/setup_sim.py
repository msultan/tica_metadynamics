#!/bin/evn python

import os,shutil,sys
from msmbuilder.utils import load,dump
from .render_sub_file import slurm_temp
from .plumed_writer import get_interval, get_plumed_dict
class TicaMetadSim(object):
    def __init__(self, base_dir="./", starting_coordinates_folder="./starting_coordinates",
                            n_tics=1,tica_mdl=None, tica_data=None,data_frame=None, grid=False,
                            interval=False,wall=False,
                            pace=1000, stride=1000,
                            temp=300, biasfactor=50, height=1.0,
                            sigma=0.2, delete_existing=False, hills_file="HILLS",
                            bias_file="BIAS", label="metad",
                            sim_save_rate=50000,
                            swap_rate=3000, n_iterations=1000,
                            platform='CUDA',
                            grid_mlpt_factor=.3,
                            render_scripts=False):
        self.base_dir = base_dir
        self.starting_coordinates_folder = starting_coordinates_folder
        self.n_tics = n_tics
        self.tica_mdl = tica_mdl
        self.tica_data = tica_data
        self.data_frame = data_frame
        self.grid = grid
        self.grid_mlpt_factor = grid_mlpt_factor
        self.interval=interval
        self.wall = wall
        self.delete_existing = delete_existing
        self.n_iterations = n_iterations
        self.platform = platform
        self.grid_list  = self.interval_list = self.wall_list = None
        self.render_scripts = render_scripts

        if self.grid:
            if len(self.grid) < 2:
                raise ValueError("grid must length at least 2 (like (0,100)")
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
                raise ValueError("interval must length 2(like (0,100) for "
                                 "calculating percentiles")
            if len(self.interval)==2 and type(self.interval[0]) in [float,int]:
               self.interval_list = get_interval(self.tica_data,self.interval[0],self.interval[1])
            else:
                self.interval_list = self.interval

        if self.wall:
            if len(self.wall) < 2:
                raise ValueError("interval must length 2(like (0,100) for "
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

        self._setup()
        print("Dumping model into %s and writing "
              "submission scripts"%base_dir)

        with open(os.path.join(base_dir,"sub.sh"),'w') as f:
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

    def _setup(self):
        c_dir = os.path.abspath(os.path.curdir)

        os.chdir(self.base_dir)
        for i in range(self.n_tics):
            try:
                os.mkdir("tic_%d"%i)
            except FileExistsError:
                if self.delete_existing:
                    print("Deleting existing tic %d"%i)
                    shutil.rmtree("tic_%d"%i)
                    os.mkdir("tic_%d"%i)
                else:
                    print("Folder already exists and cant delete")
                    return #sys.exit()
        os.chdir(c_dir)
        return
