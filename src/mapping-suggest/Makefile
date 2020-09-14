PYTHON_FILES := mapping_suggest.py mapping_suggest_qc.py ihcc_zooma_dataset.py lib.py

.PHONY: lint
lint:
	flake8 --max-line-length 100 --ignore E203,W503 $(PYTHON_FILES)
	black --line-length 100 --check $(PYTHON_FILES)

.PHONY: format
format:
	black --line-length 100 $(PYTHON_FILES)