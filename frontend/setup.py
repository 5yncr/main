from setuptools import setup

setup(
    name='5yncr Frontend',
    version='0.0.1',
    packages=['syncr_frontend'],
    license='AGPLv3',
    include_package_data=True,
    install_requires=[
        'flask',
    ],
)
