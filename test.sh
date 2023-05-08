#!/bin/bash
PROJ_NAME = simsommodel
source $$(conda info --base)/etc/profile.d/conda.sh ; conda activate $(PROJ_NAME)
CONDA_ACTIVATE
python3
import simsommodel
status=$?
[ $(status) -eq 0 ] && echo "Successfully built SimSom environment" || echo "Building environment failed"
exit()
