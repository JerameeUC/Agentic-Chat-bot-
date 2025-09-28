.PHONY: dev ml dev-deps example example-dev test run seed check lint fmt typecheck clean serve all ci coverage docker-build docker-run

# --- setup ---
dev:
	pip install -r requirements.txt

ml:
	pip install -r requirements-ml.txt

dev-deps:
	pip install -r requirements-dev.txt

# --- one-stop local env + tests ---
example-dev: dev dev-deps
	pytest
	@echo "✅ Dev environment ready. Try 'make example' to run the CLI demo."

# --- tests & coverage ---
test:
	pytest

coverage:
	pytest --cov=storefront_chatbot --cov-report=term-missing

# --- run app ---
run:
	export PYTHONPATH=. && python -c "from storefront_chatbot.app.app import build; build().launch(server_name='0.0.0.0', server_port=7860)"

# --- example demo ---
example:
	export PYTHONPATH=. && python example/example.py "hello world"

# --- data & checks ---
seed:
	python storefront_chatbot/scripts/seed_data.py

check:
	python storefront_chatbot/scripts/check_compliance.py

# --- quality gates ---
lint:
	flake8 storefront_chatbot

fmt:
	black .
	isort .

typecheck:
	mypy .

# --- hygiene ---
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage

serve:
	export PYTHONPATH=. && uvicorn storefront_chatbot.app.app:build --reload --host 0.0.0.0 --port 7860

# --- docker (optional) ---
docker-build:
	docker build -t storefront-chatbot .

docker-run:
	docker run -p 7860:7860 storefront-chatbot

# --- bundles ---
all: clean check test
ci: lint typecheck coverage
