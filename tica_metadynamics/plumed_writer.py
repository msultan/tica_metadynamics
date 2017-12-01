#!/bin/env python
from jinja2 import Template
from msmbuilder.utils import load
import numpy as np
from .pyplumed import *
import warnings

def get_interval(tica_data,lower,upper):
    if type(tica_data)==dict:
        res = np.percentile(np.concatenate([tica_data[i] for \
                                             i in tica_data.keys()]),(lower, upper), axis=0)
    else:
        res = np.percentile(np.concatenate([i for i in tica_data]),(lower, upper), axis=0)
    return [i for i in zip(res[0],res[1])]


def plumed_network(vde_mdl, df=None, nrm=None, tica_mdl=None):
    assert df is not None
    output = []
    output.append("RESTART\n")
    print("Running VDE dynamics")
    import torch
    vde_mdl = torch.load(vde_mdl, map_location=lambda storage, loc: storage)
    if vde_mdl.input_size < len(df):
        warnings.warn("VDE's input size is less than the dataframe. Assuming tica"
                      "tICs are being fed into the model")
        assert tica_mdl is not None
        n_tics = vde_mdl.input_size
        inds = np.unique(np.nonzero(tica_mdl.components_[:n_tics, :])[1])
        features = render_df(df, inds=inds, nrm=nrm, tica_mdl=tica_mdl)
        output.append(features)
        for i in range(n_tics):
            output.append(render_tic(tica_mdl, i, output_label_prefix="l0"))
    else:
        features = render_df(df, nrm=nrm)
        output.append(features)
    output.append(render_network(vde_mdl))
    return output

def render_tica_plumed_file(tica_mdl, df, n_tics, grid_list=None,interval_list=None,
                            wall_list=None,nrm=None,
                             pace=1000,  height=1.0, biasfactor=50,
                            temp=300, sigma=0.2, stride=1000, hills_file="HILLS",
                            bias_file="BIAS", label="metad",
                            walker_n=None,walker_id = None,**kwargs):
    """
    Renders a tica plumed dictionary file that can be directly fed in openmm
    :param tica_mdl: project's ticamd
    :param df: data frame
    :param grid_list: list of min and max vals for grid
    :param interval_list: list of min and max vals for interval
    :param pace: gaussian drop rate
    :param biasfactor: gaussian attenuation rate
    :param temp: simulation temp
    :param sigma: sigma
    :param stride: bias file stride
    :param hills_file: hills file
    :param bias_file: bias file
    :param label: metad label
    :param walker_n : number of walkers per tic
    :param walker: current walkers id
    :return:
    dictionary keyed on tica indices
    """

    return_dict = {}

    # inds = np.arange(tica_mdl.n_features)
    # raw_feats = render_raw_features(df,inds)
    # mean_feats = render_mean_free_features(df,inds,tica_mdl,nrm)

    if grid_list is None:
        grid_list = np.repeat(None,n_tics)
    if interval_list is None:
        interval_list = np.repeat(None, n_tics)

    vde_mdl = kwargs.pop("vde_mdl")
    if vde_mdl is not None:
        output = plumed_network(vde_mdl,df, nrm, tica_mdl)
        arg=output[-1].split("LABEL=")[-1].split("PERIODIC")[0][:-1]
        output.append(render_metad_code(arg=arg,
                                        sigma=sigma,
                                        height=height,
                                        hills=hills_file,
                                        biasfactor=biasfactor,
                                        pace=pace,
                                        temp=temp,
                                        interval=interval_list[0],
                                        grid = grid_list[0],
                                        label=label,
                                        walker_n=walker_n,
                                        walker_id=walker_id))

        output.append(render_metad_bias_print(arg=arg,
                                             stride=stride,
                                             file=bias_file))
        return_dict[0] = str(''.join(output))
        return return_dict

    multiple_tics = kwargs.pop('multiple_tics')

    if type(multiple_tics) == int:
        output = []
        output.append("RESTART\n")
        print("Running Multiple tics per simulation. Going up to tic index %d"%n_tics)
        inds = np.unique(np.nonzero(tica_mdl.components_[:multiple_tics,:])[1])

        features = render_df(df, inds=inds, nrm=nrm, tica_mdl=tica_mdl)
        output.append(features)
        for i in range(multiple_tics):
            output.append(render_tic(tica_mdl,i))

        tic_arg_list = ','.join(["tic_%d"%i for i in range(multiple_tics)])
        grid_min = ','.join([str(grid_list[i][0]) for i in range(multiple_tics)])
        grid_max = ','.join([str(grid_list[i][1]) for i in range(multiple_tics)])
        current_grid_list = [grid_min, grid_max]
        print(current_grid_list)
        current_interval_list = None
        print(current_interval_list)
        output.append(render_metad_code(arg=tic_arg_list,
                                        sigma=sigma,
                                        height=height,
                                        hills=hills_file,
                                        biasfactor=biasfactor,
                                        pace=pace,
                                        temp=temp,
                                        interval=current_interval_list,
                                        grid = current_grid_list,
                                        label=label,
                                        walker_n=walker_n,
                                        walker_id=walker_id))
        output.append(render_metad_bias_print(arg=tic_arg_list,
                                             stride=stride,
                                             file=bias_file))

        return_dict[0] = str(''.join(output))

        return return_dict

    for i in range(n_tics):
        output=[]
        output.append("RESTART\n")
        inds = np.nonzero(tica_mdl.components_[i,:])[0]
        features = render_df(df, inds=inds, nrm=nrm, tica_mdl=tica_mdl)
        output.append(features)

        output.append(render_tic(tica_mdl, i))
        if wall_list is not None:
            output.append(render_tic_wall(arg="tic_%d"%i,
                                          wall_limts=wall_list[i],
                                          **kwargs))
        if type(height) == list:
            current_height = height[i]
        else:
            current_height = height
        if type(sigma) == list:
            current_sigma = sigma[i]
        else:
            current_sigma = sigma
        output.append(render_metad_code(arg="tic_%d"%i,
                                        sigma=current_sigma,
                                        height=current_height,
                                        hills=hills_file,
                                        biasfactor=biasfactor,
                                        pace=pace,
                                        temp=temp,
                                        interval=interval_list[i],
                                        grid = grid_list[i],
                                        label=label,
                                        walker_n=walker_n,
                                        walker_id=walker_id))
        output.append(render_metad_bias_print(arg="tic_%d"%i,
                                             stride=stride,
                                             file=bias_file))
        return_dict[i] = str(''.join(output))
    return return_dict


def get_plumed_dict(metad_sim):
    if  type(metad_sim)==str:
        metad_sim = load(metad_sim)
    if not hasattr(metad_sim,"nrm"):
        metad_sim.nrm = None
    if not hasattr(metad_sim,"walker_id"):
        metad_sim.walker_id = None
        metad_sim.walker_n = None
    if not hasattr(metad_sim, "multiple_tics"):
        metad_sim.multiple_tics = None
    if not hasattr(metad_sim, "vde_mdl"):
        metad_sim.vde_mdl = None
    if type(metad_sim.tica_mdl)==str:
            tica_mdl = load(metad_sim.tica_mdl)
    return render_tica_plumed_file(tica_mdl=tica_mdl,
                                   df = metad_sim.data_frame,
                                   n_tics=metad_sim.n_tics,
                                   grid=metad_sim.grid,
                                   interval=metad_sim.interval,
                                    wall_list=metad_sim.wall_list,
                                   grid_list=metad_sim.grid_list,
                                   interval_list=metad_sim.interval_list,
                                    pace=metad_sim.pace,
                                   height=metad_sim.height, biasfactor=metad_sim.biasfactor,
                                    temp=metad_sim.temp, sigma=metad_sim.sigma,
                                   stride=metad_sim.stride, hills_file=metad_sim.hills_file,
                                   bias_file=metad_sim.bias_file, label=metad_sim.label,
                                   nrm = metad_sim.nrm, walker_id = metad_sim.walker_id,
                                   walker_n=metad_sim.walker_n,
                                   multiple_tics=metad_sim.multiple_tics,
                                   vde_mdl = metad_sim.vde_mdl)
