from setuptools import find_packages
from setuptools import setup

setup(
    name='5yncr-Backend',
    version='0.0.1',
    packages=find_packages(),
    license='AGPLv3',
    author="Matthew Bentley, Brett Johnson, David Lance, "
        "Jack LaRue, Alexander Tryjankowski",
    author_email="syncr@mtb.wtf",
    description="5yncr is a peer to peer file sync app",
    url="https://github.com/5yncr/",
    project_urls={
        "Bug Tracker": "https://github.com/5yncr/main/issues",
        "Documentation": "https://syncr.readthedocs.io",
        "Source Code": "https://github.com/5yncr",
    },
    entry_points={
        'console_scripts': [
            'check_drop = syncr_backend.bin.check_drop:main',
            'drop_init = syncr_backend.bin.drop_init:main',
            'sync_drop = syncr_backend.bin.sync_drop:main',
            'make_dht_configs = syncr_backend.bin.make_dht_configs:main',
            'make_tracker_configs = syncr_backend.bin.make_tracker_configs:main',  # noqa
            'node_init = syncr_backend.bin.node_init:main',
            'run_backend = syncr_backend.bin.run_backend:run_backend',
            'run_dht_server = syncr_backend.bin.run_dht_server:main',
            'new_version = syncr_backend.bin.new_version:main',
            'update_drop = syncr_backend.bin.update_drop:main',
            'check_for_updates = syncr_backend.bin.check_for_updates:main',
        ],
    },
    scripts=[
        'syncr_backend/contrib/bq',
    ],
    install_requires=[
        "aiofiles==0.3.2",
        "alabaster==0.7.10",
        "asn1crypto==0.24.0",
        "aspy.yaml==1.1.0",
        "attrs==17.4.0",
        "Babel==2.5.3",
        "bencode.py==2.0.0",
        "cached-property==1.4.2",
        "cachetools==2.0.1",
        "certifi==2018.4.16",
        "cffi==1.11.5",
        "cfgv==1.0.0",
        "chardet==3.0.4",
        "CommonMark==0.5.4",
        "coverage==4.5.1",
        "cryptography==2.2.2",
        "docutils==0.14",
        "flake8==3.5.0",
        "future==0.16.0",
        "identify==1.0.13",
        "idna==2.6",
        "imagesize==1.0.0",
        "Jinja2==2.10",
        "kademlia==1.0",
        "MarkupSafe==1.0",
        "mccabe==0.6.1",
        "more-itertools==4.1.0",
        "mypy==0.590",
        "nodeenv==1.3.0",
        "packaging==17.1",
        "pluggy==0.6.0",
        "pre-commit==1.8.2",
        "psutil==5.4.5",
        "purepng==0.2.0",
        "py==1.5.3",
        "pycodestyle==2.3.1",
        "pycparser==2.18",
        "pyflakes==1.6.0",
        "Pygments==2.2.0",
        "pyparsing==2.2.0",
        "pytest==3.5.1",
        "pytz==2018.4",
        "PyYAML==5.4",
        "recommonmark==0.4.0",
        "requests==2.18.4",
        "rinoh-typeface-dejavuserif==0.1.1",
        "rinoh-typeface-texgyrecursor==0.1.1",
        "rinoh-typeface-texgyreheros==0.1.1",
        "rinoh-typeface-texgyrepagella==0.1.1",
        "rinohtype==0.3.1",
        "rpcudp==3.0.0",
        "six==1.11.0",
        "snowballstemmer==1.2.1",
        "Sphinx==1.7.4",
        "sphinx-rtd-theme==0.2.4",
        "sphinxcontrib-autoprogram==0.1.4",
        "sphinxcontrib-websupport==1.0.1",
        "tox==3.0.0",
        "typed-ast==1.1.0",
        "u-msgpack-python==2.5.0",
        "urllib3==1.22",
        "virtualenv==15.2.0",
    ],
)
