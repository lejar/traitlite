from setuptools import setup, find_packages
import distutils.cmd
import subprocess


class CosmicRay(distutils.cmd.Command):
    description = 'Run cosmic-ray to find bad unit tests.'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        print('Running cosmic-ray. This could take a while.')
        commands = [
            'cosmic-ray init cosmic_ray_cfg.yml session',
            'cosmic-ray exec session',
            'cosmic-ray dump session | cr-report',
        ]
        for command in commands:
            print(command)
            try:
                subprocess.check_call(command, shell=True)
            except subprocess.CalledProcessError:
                print('Command failed. Aborting cosmic-ray.')
                return


class Coverage(distutils.cmd.Command):
    description = 'Determine unittest coverage.'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        commands = [
            'coverage run -m unittest discover',
            'coverage report',
        ]
        for command in commands:
            print(command)
            try:
                subprocess.check_call(command, shell=True)
            except subprocess.CalledProcessError:
                print('Command failed. Aborting.')
                return


with open('README.md', 'r') as fh:
    long_description = fh.read()


setup(
    name='traitlite',
    version='0.0.1',
    author='Christopher Pezley',
    author_email='pypi@pezley.net',
    description='A light-weight module that aims to provide control '
                'for class attributes.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/lejar/traitlite',
    packages=find_packages(exclude=['tests']),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    cmdclass={
        'crtest': CosmicRay,
        'coverage': Coverage,
    },
)
