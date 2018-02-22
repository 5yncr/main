# backend

## coding

1. `pyvenv-3.6 venv`
2. `source venv/bin/activate`
3. `pip install -r requirements.txt`
4. `pre-commit install --install-hooks`
5. code
6. run tests with `tox -e py36,coverage,mypy`
7. run `flake8 tests syncr_backend` and `pycodestyle tests syncr_backend`
