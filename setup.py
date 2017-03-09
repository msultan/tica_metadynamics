from setuptools import setup
import numpy
import os


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='tica_metadynamics',
    version="0.1",
    include_dirs=[numpy.get_include()],
    zip_safe=False,
    packages=['tica_metadynamics', 'tests'],
    author="Mohammad M. Sultan",
    author_email="msultan at stanford dot edu",
    description=("Useful scripts for running and analysing tica_metad"),
    long_description=read('README.md'),
    entry_points = {
       'console_scripts': ['setup_tica_meta_sim=tica_metadynamics.setup_file:main',
                           'run_tica_meta_sim=tica_metadynamics.simulate:main',
                           'process_tica_meta_sim=tica_metadynamics.post_process:main'],

    }
)
