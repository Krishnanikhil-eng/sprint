.PHONY: help install run test clean

help:
	@echo "Available commands:"
	@echo "  make install  - Install project dependencies"
	@echo "  make run      - Execute ETL pipeline"
	@echo "  make test     - Run unit tests"
	@echo "  make clean    - Remove cached files"

install:
	pip install -r requirements.txt

run:
	python -m src.etl.loader

test:
	pytest tests/

clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
