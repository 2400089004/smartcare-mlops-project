.PHONY: install test run build
install:
	pip install -r requirements.txt
test:
	python -m pytest -q
run:
	python app.py
build:
	docker build -t smartcare-mlops:local .
