.PHONY: install run examples test backtest validate quality security api container-up container-smoke benchmark container-down loadtest clean

install:
	python -m pip install -r requirements.txt

run:
	python scripts/run_all.py

examples:
	python scripts/export_examples.py

test:
	pytest -q

backtest: run
	python scripts/run_backtests.py

validate: run examples test

quality:
	python -m ruff check scripts/benchmark_serving.py scripts/run_backtests.py src/hospitality_data_platform/backtesting.py tests/test_backtesting.py
	python -m coverage erase
	python -m coverage run scripts/run_all.py
	python -m coverage run --append -m pytest -q
	python -m coverage report
	python scripts/run_backtests.py

security:
	python -m pip_audit -r requirements.txt

api:
	uvicorn hospitality_data_platform.api:app --app-dir src --reload --port 8080

container-up: run
	docker compose up --build -d

container-smoke:
	python scripts/smoke_test_serving.py --base-url http://localhost:8080 --evidence artifacts/serving/local-smoke.json

benchmark:
	python scripts/benchmark_serving.py --base-url http://localhost:8080 --requests 200 --concurrency 16 --warmup 20 --output artifacts/serving/local-benchmark.json

container-down:
	docker compose down

loadtest:
	locust -f loadtest/locustfile.py --host http://localhost:8080

clean:
	python scripts/clean_outputs.py
