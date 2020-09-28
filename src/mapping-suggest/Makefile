PYTHON_FILE_NAMES := id-generator-templates create-data-validation merge-mapping-suggestions mapping-suggest-qc mapping-suggest-nlp mapping-suggest-zooma ihcc-zooma-dataset lib
PYTHON_FILES := $(patsubst %, %.py, $(PYTHON_FILE_NAMES))

.PHONY: lint
lint:
	flake8 --max-line-length 100 --ignore E203,W503 $(PYTHON_FILES)
	black --line-length 100 --check $(PYTHON_FILES)

.PHONY: format
format:
	black --line-length 100 $(PYTHON_FILES)