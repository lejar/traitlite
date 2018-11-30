from setuptools import setup, find_packages
import distutils.cmd
import os
import shutil
import subprocess
import sys


class RunCommands(distutils.cmd.Command):
    description = ''
    user_options = []
    commands = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        print('Running commands. This could take a while.')
        for command in self.commands:
            print(command)
            try:
                subprocess.check_call(command, shell=True)
            except subprocess.CalledProcessError as error:
                print('Command failed. Aborting.')
                print(error.output)
                sys.exit(error.returncode)
                return


class CosmicRay(RunCommands):
    description = 'Run cosmic-ray to find bad unit tests.'
    commands = [
        r'''python -c "exec('try:\n    import typed_ast\n    x=1\nexcept:\n    x=0'); import sys; sys.stderr.write('typed_ast cannot be installed with cosmic_ray\n' if x == 1 else ''); sys.exit(x)"''',
        'cosmic-ray init cosmic_ray_cfg.yml session',
        'cosmic-ray exec session',
        'cosmic-ray dump session | cr-report',
    ]


class Coverage(RunCommands):
    description = 'Determine unittest coverage.'
    commands = [
        'coverage run --branch --source=traitlite -m unittest discover',
        'coverage report',
    ]


class MyPy(RunCommands):
    description = 'Run mypy on the package.'
    commands = [
        'mypy traitlite/',
    ]


class Clean(distutils.cmd.Command):
    description = 'Clean up the whole package.'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        to_remove = [
            # Files.
            'session.json',
            '.coverage',
            '.DS_Store',

            # Directories.
            '.hypothesis',
            '.mypy_cache',
            'build',
            'dist',
            'docs/_build',
            'tests/__pycache__',
            'traitlite/__pycache__',
            'traitlite.egg-info',
        ]
        for remove in to_remove:
            remove = os.path.join(*remove.split('/'))
            if os.path.isdir(remove):
                shutil.rmtree(remove, ignore_errors=True)
            else:
                try:
                    os.remove(remove)
                except OSError as error:
                    if error.errno != 2:
                        raise


with open('README.md', 'r') as fh:
    long_description = fh.read()


setup(
    name='traitlite',
    version='0.0.3',
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
        'mypy': MyPy,
        'clean': Clean,
    },
)
