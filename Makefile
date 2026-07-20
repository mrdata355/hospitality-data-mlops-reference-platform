.PHONY: run test clean api

run:
	python scripts/run_all.py

test:
	pytest -q

api:
	uvicorn hospitality_data_platform.api:app --app-dir src --reload --port 8080

clean:
	python scripts/clean_outputs.py
