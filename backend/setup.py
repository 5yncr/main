from distutils.core import setup

setup(
    name='5yncr Backend',
    version='0.0.1',
    packages=[
        'syncr_backend',
        'syncr_backend.util',
        'syncr_backend.metadata',
        'syncr_backend.init',
        'syncr_backend.tracker_interface',
    ],
    license='AGPLv3',
)
