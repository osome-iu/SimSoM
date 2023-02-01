Snakemake rules to run simulations whose results are reported in the paper.
The associated section and figure is listed with each rule. 

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