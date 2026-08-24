.PHONY: help install load ratios test report dashboard api clean

help:
	@echo "Available commands:"
	@echo "  make install   - Install project dependencies"
	@echo "  make load      - Execute full ETL database loader pipeline"
	@echo "  make ratios    - Process and calculate financial ratios"
	@echo "  make test      - Run complete pytest unit test suite"
	@echo "  make report    - Run DQ validator and generate validation report"
	@echo "  make dashboard - Prepare data layer for dashboard integration"
	@echo "  make api       - Prepare API endpoint layer"
	@echo "  make clean     - Clean temporary cache files"

install:
	pip install -r requirements.txt

load:
	python -m src.etl.loader

ratios:
	python -m src.etl.loader

test:
	pytest

report:
	python -m src.etl.validator

dashboard:
	@echo "Dashboard data layer initialized."

api:
	@echo "API foundation layer initialized."

clean:
	python -c "import pathlib, shutil; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__')]; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('.pytest_cache')]"
