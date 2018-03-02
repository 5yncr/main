# 5yncr Tracker

## Key/Value store
Provides a means for the service to find list of associated IPs, ports, and
node IDs from a given drop ID. Users are able to add their own tuples so that
others know which drops they have available
### Requests
- GET `['GET', Drop ID(64 bytes)]`
- POST `['POST', Drop ID(64 bytes), [Node ID, IP, Port]]`
## Public key server
Provides a means for the service to access public keys from node ids when
verifying the metadata file of a drop. Users are able to add their own public
key so that others can verify their drops.
### Requests
- GET `['GET', Node ID(32 bytes)]`
- POST `['POST', Node ID(32 bytes)(Hash of PubKey), RSA Public Key]`
## Running
1. clone and open this repo
2. `virtualenv -p python3 venv`
3. `source venv/bin/activate`
4. `pip install -r requirements.txt`
5. `python syncr_tracker/tracker ${IP} ${port}`
## Development
1. clone and open this repo
2. `virtualenv -p python3 venv`
3. `source venv/bin/activate`
4. `pip install -r requirements.txt`
5. `pre-commit install --install-hooks`
6. Write code
7. `tox -e py36,coverage`
8. `flake8 tests syncr_tracker` and `pycodestyle tests syncr_tracker`
