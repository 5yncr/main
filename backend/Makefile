all:
	bash -c "source venv/bin/activate;\
	tox -e py36,coverage,mypy;\
	flake8 tests syncr_backend;\
	pycodestyle tests syncr_backend"
