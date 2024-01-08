This directory contains the results as reported in the paper and the ipython notebook to create figures using the results. 

- `plot_main_results.ipynb`: produces the main figures reported in the paper using `main_results`; saved in `figures`
- `plot_supplementary_figures_quality_appeal`: produces supplementary figures using `supp_data`; saved in `supp_figures` 

## Data
### Experiment results
The `main_results` directory contains outputs from running the snakemake rules in `workflow/rules`. The snakemake files provide a way to run the experiments systematically. Snakemake tracks the specified outputs and makes sure the rules don't have to rerun for existing output. 

Each file here contains the short result of running an experiment. It only contains values for the metrics: "quality", "diversity", "discriminative_pow". i.e., calling `workflow/scripts/driver.py` without passing the "--resharefpath" and  "--verboseoutfile" argument.

### Empirical data
The `supp_data` directory contains the data used to estimate the relationship between quality and engagement, the quality distribution of messages, and to compare the reshare count distribution of messages in the simulation and empirical posts. sss

To estimate the relationship between quality and engagement, we start from a dataset of tweets about COVID-19 used in a [paper by Yang et al.](https://www.researchgate.net/publication/341069201_Prevalence_of_Low-Credibility_Information_on_Twitter_During_the_COVID-19_Outbreak). 
The dataset consists of tweets containing the hashtags \#coronavirus or \#covid19 collected in 2020, selected from a 10\% random sample of public tweets.
From this set of tweets, we analyze only posts that shared links to news sources from March 9--29, 2020.  
Linked sources were extracted from URLs in the tweet metadata. URLs shortened with 70 popular URL shortening services were also expanded to reveal the actual sources. Posts with links to Twitter and other social media platforms were excluded. 
The remaining links were matched against sources with ratings obtained from [NewsGuard](https://www.newsguardtech.com/) in April 2021. 
The final dataset contains 110,224 original Twitter posts that share at least one link with a NewsGuard rating. For each post, we have both the rating of the shared source, used as a proxy for post quality, and the number of retweets. The latter is extracted from the metadata of the latest retweet of each post.

### Other
`stylesheets` contains formatting settings to be shared among all plots.




