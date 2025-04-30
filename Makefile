.PHONY: install test lint clean docker-build docker-run docker-stop

# Installation
install:
	pip install -r requirements.txt
	python setup.py install

# Testing
test:
	pytest tests/
	pytest --cov=src tests/

# Linting
lint:
	black .
	isort .
	mypy .

# Cleaning
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type d -name "*.egg" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".mypy_cache" -exec rm -r {} +
	find . -type d -name "htmlcov" -exec rm -r {} +

# Docker commands
docker-build:
	docker-compose build

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

# Development
dev:
	flask run --debug

# Production
prod:
	gunicorn app:app

# Data pipeline
data-collect:
	python data/cli.py --symbols AAPL MSFT GOOGL --start-date 2023-01-01

data-process:
	python data/cli.py --symbols AAPL MSFT GOOGL --process

# Model training
train:
	python training/train_models.py

# Model evaluation
evaluate:
	python training/evaluate_models.py 