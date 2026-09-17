.PHONY: help install load ratios test report dashboard api batch clean

help:
	@echo "Available commands:"
	@echo "  make install   - Install project dependencies"
	@echo "  make load      - Execute full ETL database loader pipeline"
	@echo "  make report    - Run DQ validator and generate validation report"
	@echo "  make ratios    - Process financial ratios, peer rankings, and screener"
	@echo "  make batch     - Generate all tearsheets, sector reports, and radar charts"
	@echo "  make test      - Run complete pytest suite and generate HTML report"
	@echo "  make dashboard - Launch the Streamlit dashboard"
	@echo "  make api       - Launch the FastAPI server"
	@echo "  make clean     - Clean temporary cache files"

install:
	pip install -r requirements.txt

load:
	python -m src.etl.loader

report:
	python -m src.etl.validator

ratios:
	python -m src.analytics.pipeline

batch:
	python -m src.reports.batch_generator

test:
	pytest --html=reports/pytest_report.html --self-contained-html

dashboard:
	streamlit run src/dashboard/app.py

api:
	uvicorn src.api.main:app --host 0.0.0.0 --port 8000

clean:
	python -c "import pathlib, shutil; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__')]; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('.pytest_cache')]"
