This directory contains an example of data used to produce Fig.6 and Fig.7. 
All files containing all message and news feeds info (popularity, mapping of feed-messages, etc.) used are not included due to Github storage limit. They can be reproduce by calling `workflow/rules/cascade_scaling.smk`, which calls `workflow/scripts/driver.py` with the respective arguments:
  - "--resharefpath" to track & save reshares and exposures to .csv files (for network viz) 
  - "--verboseoutfile" to save save all message information.