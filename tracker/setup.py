from setuptools import find_packages
from setuptools import setup

setup(
    name='5yncr-Tracker',
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
    scripts=[
        'syncr_tracker/tracker.py',
    ],
    entry_poinst={
        'console_scripts': [
            'tracker = syncr_tracker.tracker:main',
        ],
    },
    install_requires=[
        "5yncr_Backend==0.0.1",
        "asn1crypto==0.24.0",
        "aspy.yaml==1.0.0",
        "attrs==17.4.0",
        "bencode.py==2.0.0",
        "cached-property==1.3.1",
        "cffi==1.11.4",
        "coverage==4.5.1",
        "cryptography==2.1.4",
        "flake8==3.5.0",
        "identify==1.0.7",
        "idna==2.6",
        "mccabe==0.6.1",
        "mypy==0.560",
        "nodeenv==1.2.0",
        "pluggy==0.6.0",
        "pre-commit==1.6.0",
        "psutil==5.4.3",
        "py==1.5.2",
        "pycodestyle==2.3.1",
        "pycparser==2.18",
        "pyflakes==1.6.0",
        "pytest==3.4.1",
        "PyYAML==3.12",
        "six==1.11.0",
        "tox==2.9.1",
        "typed-ast==1.1.0",
        "virtualenv==15.1.0",
    ],
    dependency_links=[
        'git+https://github.com/5yncr/backend.git@master#egg=5yncr_Backend-0.0.1',  # noqa
    ],
)
