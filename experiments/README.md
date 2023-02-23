This directory contains the results as reported in the paper and the ipython notebook to create figures using the results. 

# Experiment results
The `results` directory contains outputs from running the snakemake rules in `workflow/rules`. The snakemake files provide a way to run the experiments systematically. Snakemake tracks the specified outputs and makes sure the rules don't have to rerun for existing output. 

Each file here contains the short result of running an experiment. It only contains values for the metrics: "quality", "diversity", "discriminative_pow". i.e., calling `workflow/scripts/driver.py` without passing the "--resharefpath" and  "--verboseoutfile" argument.

# Create figures

- `plot_findings.ipynb`: produces the figures reported in the paper using the files in `results`.

- `plot_cascade_scaling.py`: produces Fig.7 using the sample data provided in results/cascade_scaling. Read `cascade_scaling/README.md` for how to reproduce full results (across 10 simulations). 
  - Invoke by calling (from `experiments` directory) `python plot_cascade_scaling.py results/cascade_scaling None2 figures` where:
   - `results/cascade_scaling`: directory containing the results
   - `None2`: experiment name, used as pattern to combine data across runs. e.g., if there are 3 runs, the directory contains 3 files prefixed with `None2`: `None2_*.json.gz`)
   - `figures`: directory to save plot in

## Styling

`stylesheet.mplstyle` contains formatting settings to be shared among all plots, unless specified otherwise.