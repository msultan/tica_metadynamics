#!/bin/env python

import inspect
import yaml
from .utils import load_yaml_file
from .setup_sim import TicaMetadSim
import os

def setup_file():
    dict_to_dump = {}
    inspect_obj = inspect.getargspec(TicaMetadSim.__init__)
    #first arg is self.
    for i,c in enumerate(inspect_obj.args[1:]):
        dict_to_dump[c] = inspect_obj.defaults[i]
    dict_to_dump["Accept_Config"] = False
    with open('sim_params.yaml', 'w') as outfile:
        yaml.dump(dict_to_dump, outfile, default_flow_style=False)


    print("I just wrote out the sim_params.yaml file. Please change things "
          "and then run the next command")
    return


def main():
    if not os.path.isfile("sim_params.yaml"):
        setup_file()
    else:
        yaml_file = load_yaml_file("sim_params.yaml")
        if yaml_file["Accept_Config"]:
            print("Setting up simulation now")
            yaml_file.pop("Accept_Config")
            TicaMetadSim(**yaml_file)
        else:
            raise ValueError("You have not accepted the config file. Please"
                             "change the Accept_Config row to True")
    return

if __name__ == "__main__":
    main()
