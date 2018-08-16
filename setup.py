from setuptools import setup

setup(
    name='comiconverter',
    version='0.1.1',
    author='Tristan Carranante',
    author_email='tristan@carranante.name',
    packages=['comiconverter'],
    scripts=['bin/comiconverter'],
    url='https://gogs.ponos.space/tristan-c/Comiconverter',
    license='LICENSE',
    description='Old tool to convert comics, make backup before, could crash',
    long_description=open('README.md').read(),
    install_requires=[
        "Pillow >= 2.0.0",
        "docopt >= 0.6"
    ],
)
