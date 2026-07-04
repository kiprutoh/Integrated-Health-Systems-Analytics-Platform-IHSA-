.PHONY: install seed run api test lint docker
install:      ; pip install -r requirements-dev.txt
seed:         ; python scripts/seed_master_data.py && python scripts/generate_hiv_panel.py
run:          ; streamlit run app.py
api:          ; uvicorn api.main:app --reload --port 8000
test:         ; pytest -q
lint:         ; ruff check .
docker:       ; docker build -f docker/Dockerfile -t ihsa-streamlit .
