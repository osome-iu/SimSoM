This directory contains toy data and minimal example to run the model.

## An introduction with .ipynb

`run_simulation.ipynb`: provide the basic steps needed to run a simulation and demo some of the results. There are two other alternatives to run a simulation.

## Run simulation from the command line

From the root directory, call the `workflow/scripts/driver.py` script using
 ```py
 python3 workflow/scripts/driver.py -i example/data/infosys_network.gml --config example/data/config.json -o example/results/results.json -v example/results/verbose_results.json.gz --times 2
 ```
In which the options are:
  - `-i`: input network file path
  - `-o`: file path to output the results
  - `-v`: file path to output the results, plus other detailed tracking information
  - `--config`: file path specifying the parameters to run the simulation
  - `--times`: number of time to run the simulation

## Run simulation using a Snakemake rule: 

`Snakefile` specifies the rules to create a network and run simulation by calling `workflow/scripts/init_net.py` and `workflow/scripts/driver.py`
- from the `example` directory, run the command `snakemake -c1`
- This will use 1 CPU core. Use `--cores N` or `-cN` to use N cores or `--cores all` for all available cores.
- Call `snakemake -n` for a dryrun. You can preview the output and see the DAG of jobs

