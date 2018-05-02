from setuptools import find_packages
from setuptools import setup

setup(
    name='5yncr Frontend',
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
    include_package_data=True,
    install_requires=[
        'flask',
    ],
)
