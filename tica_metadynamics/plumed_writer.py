#!/bin/env python
from jinja2 import Template
from kinase_msm.data_loader  import load_yaml_file
import numpy as np

plumed_dist_template = Template("DISTANCE ATOMS={{atoms}} LABEL={{label}} ")
plumed_torsion_template = Template("TORSION ATOMS={{atoms}} LABEL={{label}} ")
plumed_rmsd_template = Template("RMSD REFERENCE={{loc}} TYPE=OPTIMAL LABEL={{label}} ")

plumed_matheval_template = Template("MATHEVAL ARG={{arg}} FUNC={{func}} LABEL={{label}} PERIODIC={{periodic}} ")

plumed_combine_template = Template("COMBINE LABEL={{label}} ARG={{arg}} COEFFICIENTS={{coefficients}} "+\
                                    "PERIODIC={{periodic}} ")

plumed_plain_metad_template = Template("METAD ARG={{arg}} SIGMA={{sigma}} HEIGHT={{height}} "+\
                                       "FILE={{hills}} TEMP={{temp}} PACE={{pace}} LABEL={{label}}")

plumed_metad_template = Template("METAD ARG={{arg}} SIGMA={{sigma}} HEIGHT={{height}} FILE={{hills}} "+\
                                 "BIASFACTOR={{biasfactor}} TEMP={{temp}} "+\
                                "INTERVAL={{interval}} GRID_MIN={{grid_min}} "+ \
                                "GRID_MAX={{grid_max}} PACE={{pace}} LABEL={{label}} ")

plumed_print_template = Template("PRINT ARG={{arg}} STRIDE={{stride}} FILE={{file}} ")




def create_torsion_label(inds, label):
    #t: TORSION ATOMS=inds
    return plumed_torsion_template.render(atoms=','.join(map(str, inds)), label=label) +" \\n\\"

def create_distance_label(inds, label):
    return plumed_dist_template.render(atoms=','.join(map(str, inds)), label=label) + " \\n\\"


def create_rmsd_label(loc, label):
    return plumed_rmsd_template.render(loc=loc , label=label)+" \\n\\"


def create_mean_free_label(feature_label, offset, func=None,**kwargs):
    arg = feature_label
    if func is None:
        f = "x-%s"%offset
    elif func=="exp":
        f = "%s(-(x)^2/(2*%s^2)) - %s"%(func,kwargs.pop("sigma"),offset)
    elif func in ["sin","cos"]:
        f = "%s(x)-%s"%(func, offset)
    else:
        raise ValueError("Can't find function")
    label= "meanfree_"+ "%s_"%func + feature_label

    return plumed_matheval_template.render(arg=arg, func=f,\
                                           label=label,periodic="NO")


class PlumedWriter(object):
    """
    protein class to write all tica metadynamics files
    """
    def __init__(self, yaml_file, grid=True, interval=True, interval_lim=(0.01,0.99),\
                 pace=1000, biasfactor=20, temp=300):
        self.yaml_file = load_yaml_file(yaml_file)
        self.prj = load(yaml_file["prj_file"])
        self.tica_mdl = prj.tica_mdl
        self.df = prj.df
        self.grid = grid
        if self.grid:
            self.grid_min,self.grid_max = get_interval(self.prj,0,100)
        self.interval = interval
        self.interval_lim = interval_lim
        if self.interval:
            self.interval_min,self.interval_max = get_interval(self.prj,interval_lim[0],interval_lim[1])

        self.pace = pace
        self.biasfactor = biasfactor
        self.temp = temp


    def render_plumed(self):
        return write_plumed_file(self.tica_mdl, self.df)

def get_interval(prj,lower,upper):
    if type(prj.tica_data)==dict:
        return np.percentile(np.concatenate([prj.tica_data[i] for \
                                             i in prj.tica_data.keys()]),(lower, upper), axis=0)
    else:
        return np.percentile(np.concatenate([i for i in prj.tica_data]),(lower, upper), axis=0)


def render_raw_features(df,inds):
    output = []
    if df.featurizer[0] not in ["Contact","LandMarkFeaturizer","Dihedral"]:
        raise ValueError("Sorry only contact, landmark, and dihedral featuizers\
                         are supported for now")
    if df.featurizer[0] in ["Contact"] and df.featuregroup[0] not in ["ca"]:
        raise ValueError("Sorry only ca contact are supported for now")

    possibles = globals().copy()
    possibles.update(locals())

    if df.featurizer[0] == "Contact":
        func = possibles.get("create_distance_label")
    elif df.featurizer[0] == "LandMarkFeaturizer":
        func = possibles.get("create_rmsd_label")
    else:
        func = possibles.get("create_torsion_label")

    already_done_list = []

    for j in df.iloc[inds].iterrows():
        feature_index = j[0]
        atominds = j[1]["atominds"]
        resids = j[1]["resids"]
        feat = j[1]["featuregroup"]
        feat_label = feat+"_%s"%'_'.join(map(str,resids))
        if feat_label not in already_done_list:
            #mdtraj is 0 indexed and plumed is 1 indexed
            output.append(func(atominds + 1 , feat_label))
            output.append("\n")
            already_done_list.append(feat_label)

    return ''.join(output)


def render_mean_free_features(df,inds,tica_mdl):
    output = []
    if df.featurizer[0] not in ["Contact","LandMarkFeaturizer","Dihedral"]:
        raise ValueError("Sorry only contact, landmark, and dihedral featuizers\
                         are supported for now")
    if df.featurizer[0] in ["Contact"] and df.featuregroup[0] not in ["ca"]:
        raise ValueError("Sorry only ca contact are supported for now")

    possibles = globals().copy()
    possibles.update(locals())

    sigma = None

    if df.featurizer[0] == "Contact":
        func = np.repeat(None, len(inds))
    elif df.featurizer[0] == "LandMarkFeaturizer":
        func = np.repeat("exp", len(inds))
        sigma =  df.otherinfo[0]
    else:
        func = list(df.otherinfo[inds])

    for j in df.iloc[inds].iterrows():
        feature_index = j[0]
        atominds = j[1]["atominds"]
        feat = j[1]["featuregroup"]
        resids = j[1]["resids"]
        feat = j[1]["featuregroup"]

        feat_label = feat+"_%s"%'_'.join(map(str,resids))

        output.append(create_mean_free_label(feature_label=feat_label,\
                                             offset=prj.tica_mdl.means_[feature_index],\
                                             func =func[feature_index], sigma=sigma)+" \\n\\")
        output.append("\n")

    return ''.join(output)

def render_tic(df,tica_mdl, tic_index=0):
    output = []
    inds = np.nonzero(tica_mdl.components_[tic_index,:])[0]
    template = Template("meanfree_{{func}}_{{feature_group}}_{{feature_index}}")

    if df.featurizer[0] == "Contact":
        func = np.repeat(None, len(inds))
    elif df.featurizer[0] == "LandMarkFeaturizer":
        func = np.repeat("exp", len(inds))
    else:
        func = df.otherinfo[inds]

    feat_labels=['_'.join(map(str,i)) for i in df.resids[inds]]
    feature_labels = [template.render(func=i,feature_group=j,feature_index=k) \
                      for i,j,k in zip(func[inds],df.featuregroup[inds],feat_labels)]

    tic_coefficient = tica_mdl.components_[tic_index,]
    if tica_mdl.kinetic_mapping:
        tic_coefficient *= prj.tica_mdl.eigenvalues_[tic_index]

    arg=','.join(feature_labels)
    tic_coefficient = ','.join(map(str,tic_coefficient))

    output.append(plumed_combine_template.render(arg=arg,
                                   coefficients=tic_coefficient,
                                   label="tic%d"%tic_index,
                                   periodic="NO") +" \\n\\")
    return ''.join(output)


def render_metad_code(arg="tic0", sigma=0.2, height=1.0, hills="HILLS",biasfactor=40,
                      temp=300,interval=None, grid=None,
                      label="metad",pace=1000):

    output=[]
    if interval is None or grid is None:
        plumed_script = plumed_plain_metad_template
        output.append(plumed_script.render(arg=arg,
                         sigma=sigma,
                         height=height,
                         hills=hills,
                         temp=temp,
                         pace=pace)+" \\n\\")
    else:
        plumed_script = plumed_metad_template

        grid_min=grid[0]
        grid_max=grid[1]

        output.append(plumed_script.render(arg=arg,
                         sigma=sigma,
                         height=height,
                         hills=hills,
                         biasfactor=biasfactor,
                         interval=','.join(map(str,interval)),
                         grid_min=grid_min,
                         grid_max=grid_max,
                         label=label,
                         pace=pace)+" \\n\\")
    return ''.join(output)


def render_metad_bias_print(arg="tic0",stride=1000,label="metad",file="BIAS"):
    output=[]
    arg=','.join([arg,label + ".bias"])
    output.append(plumed_print_template.render(arg=arg,
                                               stride=stride,
                                               file=file))

    return ''.join(output)


def render_tica_plumed_file(tica_mdl, df, grid_list=[None,None],interval_list=[None,None],
                             pace=1000, biasfactor=50,
                            temp=300, sigma=0.2, stride=1000, hills_file="HILLS",
                            bias_file="BIAS", label="metad"):
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
    :return:
    dictionary keyed on tica indices
    """

    return_dict = {}

    inds = np.arange(tica_mdl.n_features)
    raw_feats = render_raw_features(df,inds)
    mean_feats = render_mean_free_features(df,inds,tica_mdl)

    for i in range(tica_mdl.n_components):
        output=[]
        output.append(raw_feats)
        output.append(mean_feats)
        output.append(render_tic(df,tica_mdl,i))
        output.append("\n")
        output.append(render_metad_code(arg="tic%d"%i,
                                        sigma=sigma,
                                        height=height,
                                        hills=hills_file,
                                        biasfactor=biasfactor,
                                        pace=pace,
                                        temp=temp,
                                        interval=interval_list[i],
                                        grid = grid_list[i],
                                        label=label))
        output.append("\n")
        output.append(render_metad_bias_print(arg="tic%d"%i,
                                             stride=stride,
                                             label=label,
                                             file=bias_file))
        return_dict[i] = output
    return return_dict
