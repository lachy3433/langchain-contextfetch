.PHONY: all format lint test tests integration_test integration_tests help

# Default target executed when no arguments are given to make.
all: help

# Define a variable for the test file path.
TEST_FILE ?= tests/unit_tests/
integration_test integration_tests: TEST_FILE = tests/integration_tests/

# unit tests are run with the --disable-socket flag to prevent network calls
test tests:
	uv run --group test pytest --disable-socket --allow-unix-socket $(TEST_FILE)

# integration tests call the live API; they are skipped unless CONTEXTFETCH_API_KEY is set
integration_test integration_tests:
	uv run --group test --group test_integration pytest -v $(TEST_FILE)

######################
# LINTING AND FORMATTING
######################

PYTHON_FILES=.
MYPY_CACHE=.mypy_cache

lint:
	uv run --all-groups ruff check $(PYTHON_FILES)
	uv run --all-groups ruff format $(PYTHON_FILES) --diff
	mkdir -p $(MYPY_CACHE) && uv run --all-groups mypy $(PYTHON_FILES) --cache-dir $(MYPY_CACHE)

format:
	uv run --all-groups ruff format $(PYTHON_FILES)
	uv run --all-groups ruff check --fix $(PYTHON_FILES)

help:
	@echo '----'
	@echo 'format                       - run code formatters'
	@echo 'lint                         - run linters'
	@echo 'test                         - run unit tests'
	@echo 'integration_test             - run integration tests (needs CONTEXTFETCH_API_KEY)'
	@echo 'test TEST_FILE=<test_file>   - run all tests in file'
