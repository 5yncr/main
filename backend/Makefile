all:
	bash -c "source venv/bin/activate;\
	tox -e coverage,mypy;\
	flake8 tests syncr_backend;\
	pycodestyle tests syncr_backend"

docs:
	$(MAKE) -C docs html

.PHONY: all docs
