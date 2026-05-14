PYTHON := python
PYTEST := $(PYTHON) -m pytest

.PHONY: test test-v install

install:
	$(PYTHON) -m pip install -q Pillow PyYAML pytest

test:
	$(PYTEST) apps/mame-harness/tests/

test-v:
	$(PYTEST) apps/mame-harness/tests/ -v
