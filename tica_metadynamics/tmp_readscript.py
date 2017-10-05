import numpy as np
import pickle

with open('tmp_script','r') as f:
	string=f.read()

print(string)

dct={0: string}

with open('plumed_dict','wb') as f:
	pickle.dump(dct,f)
