.PHONY: install run examples test validate api loadtest clean

install:
	python -m pip install -r requirements.txt

run:
	python scripts/run_all.py

examples:
	python scripts/export_examples.py

test:
	pytest -q

validate: run examples test

api:
	uvicorn hospitality_data_platform.api:app --app-dir src --reload --port 8080

loadtest:
	locust -f loadtest/locustfile.py --host http://localhost:8080

clean:
	python scripts/clean_outputs.py
