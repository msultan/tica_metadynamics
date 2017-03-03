#!/bin/evn python

import os,shutil,sys
from msmbuilder.utils import load,dump
import yaml

yaml_template = """
base_dir : {base_dir}
n_tics: {n_tics}
starting_coordinates_folder: {starting_coordinates_folder}
grid: {grid}
interval: {interval}
pace: {pace}
stride: {stride}
temp: {temp}
sigma: {sigma}
biasfactor: {biasfactor}
height: {height}
hills_file: {hills_file}
bias_file: {bias_file}
label: {label}
"""

def setup_tica_meta_sim(sim_loc="./", starting_coordinates_folder="./starting_coordinates",
                        n_tics=1,tica_mdl=None, data_frame=None, grid=None,
                        interval=None, pace=1000, stride=1000,
                        temp=300, biasfactor=50, height=1.0,
                        sigma=0.2, delete_existing=False,hills_file="HILLS",
                        bias_file="BIAS", label="metad"):

    c_dir = os.path.abspath(os.path.curdir)
    base_dir = sim_loc
    starting_coordinates_folder = starting_coordinates_folder

    print("Setting up tica simulation folder")
    try:
        os.mkdir(sim_loc)
    except FileExistsError :
        if delete_existing:
            print("Deleting existing")
            shutil.rmtree(sim_loc)
            os.mkdir(sim_loc)
        else:
            print("Folder already exists and cant delete")
            return #sys.exit()

    os.chdir(sim_loc)
    dump(tica_mdl, "tica_mdl.pkl")
    dump(data_frame, "df.pkl")
    for i in range(n_tics):
        try:
            os.mkdir("tic_%d"%i)
        except FileExistsError:
            if delete_existing:
                print("Deleting existing tic %d"%i)
                shutil.rmtree(sim_loc)
                os.mkdir(sim_loc)
            else:
                print("Folder already exists and cant delete")
                return #sys.exit()

    with open("project.yaml",'w') as yaml_out:
        yaml_file = yaml.load(yaml_template.format(base_dir=base_dir,
                                                   n_tics=n_tics,
                                                   starting_coordinates_folder=starting_coordinates_folder,
                                                   grid=grid,
                                                   interval=interval,
                                                   temp=temp,
                                                   pace=pace,
                                                   height=height,
                                                   biasfactor=biasfactor,
                                                   sigma=sigma,
                                                   stride=stride,
                                                   hills_file=hills_file,
                                                   label=label,
                                                   bias_file=bias_file))

        yaml_out.write(yaml.dump(yaml_file))
    os.chdir(c_dir)

    return