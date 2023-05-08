.PHONY : create_conda_env
.ONESHELL:

SHELL=/bin/bash
PROJ_NAME=simsommodel
ENV_PATH=$$(conda info --base)
CONDA_ACTIVATE=source $$(conda info --base)/etc/profile.d/conda.sh ; conda activate $(PROJ_NAME)
DEPENDENCIES=conda install -y -c anaconda -c conda-forge -c bioconda snakemake-minimal black isort flake8 pytest neovim snakefmt scikit-learn scipy seaborn pandas

create_conda_env:
	echo "Creating conda environent at ${ENV_PATH}/envs/${PROJ_NAME} (Delete any existing conda env with the same name).."
	rm -rf "${ENV_PATH}/envs/${PROJ_NAME}"
	conda create --force -y -n $(PROJ_NAME) python=3.8  
	$(CONDA_ACTIVATE); pip install -e ./libs/; pip install networkx igraph pyarrow igraph; $(DEPENDENCIES)