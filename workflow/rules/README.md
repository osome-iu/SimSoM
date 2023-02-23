This directory contains Snakemake rules to run simulations whose results are reported in the paper.
- Snakemake is a powerful workflow that helps keeping track of experiments systematically. Each Snakemake file is consists of rules that define how to create output files from input files. Dependencies between the rules are determined automatically, creating a DAG (directed acyclic graph) of jobs that can be automatically parallelized. Read more about Snakemake in its [documentation](https://snakemake.readthedocs.io/en/v5.1.4/executable.html)
- The associated section and figure is listed with each rule. 

Run each snakefile below by: 
- Changing into the root directory of this project 
- calling `snakemake --snakefile workflow/rules/<rule-name>.smk --cores all`
**Note**: If you decide to run __multiple rules at the same time__, call the above command with the `--nolock` flag. This is to disable Snakemake's default mechanism of locking a directory to prevent a file being modified multiple times. We do this since some of our rules make use of the same network files.
Although using `--nolock` is generally __not recommended__, this should be fine because our results are disjoint sets of output files.

# Cognitive and Network Vulnerabilities
## Cognitive 
- vary_mu.smk (Fig.3a)
- vary_alpha.smk (Fig.3b)

## Network
- shuffle_network.smk (Fig.4)

# Effects of Bot Tactics
- thetagamma.smk (Fig.5d)
- phigamma.smk (Fig.5e)
- thetaphi.smk (Fig.5f)
Panel a,b,c of Figure 5 use a subset of results from these simulations: 
- infiltration: results from thetagamma.smk where $\theta=1$ (Fig.5a)
- flooding: results from thetagamma.smk where $\gamma=0.01$ (Fig.5b)
- deception: results from phigamma.smk where $\gamma=0.01$ (Fig.5c)
Simulations to test the effects of extreme bot parameters ($\gamma=0.1$, $\theta=32$, $\phi=1$) is run by `extreme.smk`

# Targeting Strategies 
- strategies_gamma.smk (Fig.8)
Significant effects are only observed in a system with high bot infiltration rate. Reported in the paper are results of simulations where $\gamma=0.1$.

# Others
## Network initialization 
All network configurations explored are initialized using the `initnet.smk` rule. 

## Baseline 
Baseline results are from a scenario where there is no bot in the system. Used to calculate _relative_quality_
- baseline.smk 