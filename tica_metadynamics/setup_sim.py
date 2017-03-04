#!/bin/evn python

import os,shutil,sys
from msmbuilder.utils import load,dump
from .render_sub_file import slurm_temp

class TicaMetadSim(object):
    def __init__(self, base_dir="./", starting_coordinates_folder="./starting_coordinates",
                            n_tics=1,tica_mdl=None, data_frame=None, grid=True,
                            grid_list=None, interval=True,
                            interval_list=None, pace=1000, stride=1000,
                            temp=300, biasfactor=50, height=1.0,
                            sigma=0.2, delete_existing=False, hills_file="HILLS",
                            bias_file="BIAS", label="metad",
                            sim_save_rate=50000,
                            swap_rate=3000, n_iterations=1000):
        self.base_dir = base_dir
        self.starting_coordinates_folder = starting_coordinates_folder
        self.n_tics = n_tics
        self.tica_mdl = tica_mdl
        self.data_frame = data_frame
        self.grid = grid
        self.interval=interval
        self.delete_existing = delete_existing
        self.n_iterations = n_iterations

        if self.grid and grid_list is None:
            raise ValueError("Grid list is required with grid")
        self.grid_list = grid_list

        if self.interval and interval_list is None:
            raise ValueError("interval_list is required with interval")
        self.interval_list = interval_list

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


        self._setup()
        print("Dumping model into %s and writing "
              "submission scripts"%base_dir)

        with open(os.path.join(base_dir,"sub.sh"),'w') as f:
            f.writelines(slurm_temp.render(job_name="tica_metad",
                          base_dir=self.base_dir,
                          partition="pande",
                          n_tics=self.n_tics))

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
        dump(self,"metad_sim.pkl")
        os.chdir(c_dir)
        return
