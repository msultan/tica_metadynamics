MINICONDA=Miniconda3-latest-Linux-x86_64.sh
MINICONDA_MD5=$(curl -s https://repo.continuum.io/miniconda/ | grep -A3 $MINICONDA | sed -n '4p' | sed -n 's/ *<td>\(.*\)<\/td> */\1/p')
wget https://repo.continuum.io/miniconda/$MINICONDA
if [[ $MINICONDA_MD5 != $(md5sum $MINICONDA | cut -d ' ' -f 1) ]]; then  echo "Miniconda MD5 mismatch"; exit 1; fi
bash $MINICONDA -b
export PATH=$HOME/miniconda3/bin:$PATH
conda config --add channels omnia
conda config --add channels acellera
#conda update conda
conda info -a
conda create --yes -n _test python=$TRAVIS_PYTHON_VERSION `cat requirements.txt | xargs`
source activate _test
conda install -yq plumed2=2.3.0
conda install -yq openmm
pip install git+https://github.com/msmbuilder/msmbuilder.git
python setup.py install
