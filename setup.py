#from distutils.core import setup
from setuptools import setup

setup(
    name='comiconverter',
    version='0.1.0',
    author='Tristan Carranante',
    author_email='tristan@carranante.name',
    packages=['comiconverter'],
    scripts=['bin/convertcomics'],
    url='http://',
    license='LICENSE',
    description='',
    long_description=open('README.md').read(),
    install_requires=[
        "Pillow >= 2.0.0",
        "patool >= 1.0.0",
        "docopt >= 0.6"
    ],
)
