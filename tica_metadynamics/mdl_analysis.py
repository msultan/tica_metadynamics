#!/bin/evn python

import os
import mdtraj as mdt
import numpy as np
from pyemma.thermo import mbar


class MetaProtein(object):
    """
    protein class to load all metadynamics related data for a single protein within a project
    """
    def __init__(self, loc, prj,start=0,stop=-1,skip=1, kt=2.5):
        self.loc = os.path.abspath(loc)
        self.prj = prj
        self.start = start
        self.stop = stop
        self.skip = skip
        self.kt = kt
        self.bd,self.ad,self.cd =  self.load_metad_data()
        self._biases= None
        self._mbar_obj = None
        self._avail_states = None
        self._ttrajs = None
        self._dtrajs = None

    @property
    def max_len(self):
        return min([len(self.ad[i]) for i in self.ad.keys()])


    @property
    def avail_states_(self):
        if self._avail_states is not None:
            return self._avail_states
        self._avail_states =  np.unique([self.ad[i][self.start:self.stop][::self.skip] \
                                         for i in self.ad.keys()])
        return self._avail_states


    @property
    def biases_(self):
        if self._biases is not None:
            return self._biases

        self._biases=[]
        for replica in range(self.prj.n_tics_):
            self._biases.append([tuple(self.bd["%d_%d"%(j,replica)][i] for j in range(self.prj.n_tics_))\
                                 for i in range(self.max_len)[self.start:self.stop][::self.skip]])

        self._biases = np.array(self._biases)
        return self._biases

    @property
    def ttrajs_(self):
        if self._ttrajs is not None:
            return self._ttrajs
        self._ttrajs = [np.repeat(tic_index,len(self.ad["%d"%(tic_index)][self.start:self.stop][::self.skip])) \
          for tic_index in range(self.prj.n_tics_)]
        return self._ttrajs

    @property
    def dtrajs_(self):
        if self._dtrajs is not None:
            return self._dtrajs
        self._dtrajs =  [self.ad["%d"%(tic_index)][self.start:self.stop][::self.skip] \
                for tic_index in range(self.prj.n_tics_)]
        return self._dtrajs

    @property
    def mbar_obj_(self):
        if self._mbar_obj is not None:
            return self._mbar_obj
        self._mbar_obj = mbar(self.ttrajs_, self.dtrajs_, self.biases_)
        return self._mbar_obj

    def load_metad_data(self):
        bias_dict = {}
        ass_dict = {}
        colvar_dict = {}
        for replica in range(self.prj.n_tics_):
            traj = mdt.load("%s/tic_%d/tic_%d.xtc"%(self.loc,replica,replica),top=self.prj.top)
            colvar_dict[replica] = self.prj.tica_mdl.transform(self.prj.feat.transform([traj]))
            tica_feat = colvar_dict[replica]
            ass_dict["%d"%(replica)] = self.prj.kmeans_mdl.transform(tica_feat)[0]

            for i in range(self.prj.n_tics_):
                bias = np.loadtxt("%s/tic_%d/r%dt%d.BIAS"%(self.loc,replica,replica,i))
                #0 th column is time
                # 1st column is tic val
                # 2nd column is bias
                bias_dict["%d_%d"%(replica,i)]=bias[:,2]/self.kt
        return bias_dict,ass_dict,colvar_dict
