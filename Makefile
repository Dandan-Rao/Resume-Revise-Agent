# Define the tools 
FORMATTER = nbqa black
LINTER = nbqa pylint
STYLE_CHECKER = nbqa flake8

# Find all Jupyter Notebooks and Python scripts
NOTEBOOKS := $(shell find . -name "*.ipynb" 2>/dev/null)
PYTHON_SCRIPTS := $(shell find . -name "*.py" -not -path ".venv/*" -not -path "*/__pycache__/*")


install:
	pip install --upgrade pip &&\
		pip install -r requirements.txt

# Format all notebooks and python scripts
format:
	@if [ -n "$(NOTEBOOKS)" ]; then \
		echo "Formatting all notebooks..."; \
		$(FORMATTER) $(NOTEBOOKS); \
	else \
		echo "No notebooks found, skipping notebook formatting."; \
	fi
	@echo "Formatting all python scripts..."
	@black $(PYTHON_SCRIPTS)

# Lint all notebooks
lint:
	@echo "Linting all notebooks..."
	@$(LINTER) $(NOTEBOOKS)

# Check style for all notebooks
check-style:
	@echo "Checking style for all notebooks..."
	@$(STYLE_CHECKER) $(NOTEBOOKS)

# Run all tasks
all: install format lint check-style