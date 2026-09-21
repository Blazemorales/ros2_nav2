from setuptools import find_packages
from setuptools import setup

setup(
    name='rover_msgs',
    version='2.0.0',
    packages=find_packages(
        include=('rover_msgs', 'rover_msgs.*')),
)
