#!/bin/env python
from jinja2 import Template

slurm_temp = Template("#!/bin/bash \n"
                      "#SBATCH --job-nam={{job_name}} \n"
                      "#SBATCH -o {{base_dir}}/log.out \n"
                      "#SBATCH -p {{partition}} \n"
                      "#SBATCH -n {{n_tics}} \n"
                      "#SBATCH --gres=gpu:{{n_tics}} \n"
                      "#SBATCH -t 23:59:00 \n"
                      "#SBATCH --no-requeue\n"
                      "module purge \n"
                      "source ~/.bash_profile \n"
                      "echo $CUDA_VISIBLE_DEVICES \n"
                      "cd {{base_dir}} \n"
                      "sbatch --dependency=afterany:$SLURM_JOB_ID sub.sh \n"
                      "srun run_tica_meta_sim")





