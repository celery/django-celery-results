# Contributing to django-celery-results

Welcome to the django-celery-results project!
This document will help you get things set up locally.
Please read the Celery project [contributing guidelines](https://docs.celeryproject.org/en/latest/contributing.html)
for more information.

## Setting Up a Local Development Environment

### Prerequisites

You need a supported python version installed, an IDE of your choice,
and preferably [make](https://www.gnu.org/software/make/).

### Installation

1. Fork and clone the repository
2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate
3. Install the package in editable mode with dependencies:

   ```bash
   pip install -e . # This will install pkgs in requirements/default.txt,
   pip install -r requirements/test.txt
   ```
4. If you need to install dependencies for a specific Django version,
   see the available text files in `requirements/`.

### Common Make Targets

Run `make help` to see all available targets. The most useful ones:

| Target       | Description                                  |
|--------------|----------------------------------------------|
| `test`       | Run tests using the current Python            |
| `lint`       | Run all lint checks (flake8, apicheck, etc.)  |
| `docs`       | Build documentation                           |
| `clean`      | Remove build artifacts and `.pyc` files       |
| `distcheck`  | Run lint, tests, and clean                    |

## Submitting Changes

Please submit your changes as a pull request to this repository.
For more information about the contribution and review process, please see the
Celery project [contributing guidelines](https://docs.celeryproject.org/en/latest/contributing.html).
