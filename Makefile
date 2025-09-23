.PHONY: install install-dev test lint clean

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test:
	pytest tests/

lint:
	flake8 lep/ tests/
	black --check lep/ tests/
	isort --check-only lep/ tests/

format:
	black lep/ tests/
	isort lep/ tests/

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf build/ dist/ *.egg-info/

run-scenario:
	python -m lep.orchestrator run-scenario $(ARGS)