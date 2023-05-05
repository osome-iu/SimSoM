SHELL=/bin/bash
PROJ_NAME=simsommodel

.PHONY: create_env install_lib create_ipykernel


create_conda_env:
	mamba create -y -n $(PROJ_NAME) python=3.8
	
	mamba init

	mamba activate $(PROJ_NAME)

	pip install networkx igraph pyarrow igraph

	mamba install -y -c anaconda -c conda-forge -c bioconda pandas snakemake-minimal black isort flake8 pytest neovim snakefmt scikit-learn scipy seaborn


install_lib:
	pip install -e ./libs/

create_ipykernel:
	python3 -m ipykernel install --user --name=$(PROJ_NAME)

	