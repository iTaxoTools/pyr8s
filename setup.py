"""A setuptools based setup module."""

from setuptools import setup, find_namespace_packages, Extension, Command
from setuptools.command.build_py import build_py as _build_py
import pathlib

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(name='pyr8s',
    version='0.3.2',
    description='Calculate divergence times and rates of substitution for phylogenic trees',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Patmanidis Stefanos',
    author_email='stefanpatman91@gmail.com',
    package_dir={'': 'src'},
    packages=find_namespace_packages(
        # exclude=('itaxotools.common*',),
        include=('itaxotools*',),
        where='src',
    ),
    python_requires='>=3.6, <4',
    install_requires=[
        'dendropy',
        'numpy',
        'scipy',
        'pyside6',
    ],
    entry_points = {
        'console_scripts': [
            'pyr8s = itaxotools.pyr8s.run:main',
            'pyr8s-qt = itaxotools.pyr8s.gui.run:main'
            ],
        'pyinstaller40': [
          'hook-dirs = itaxotools.__pyinstaller:get_hook_dirs',
          'tests = itaxotools.__pyinstaller:get_PyInstaller_tests'
        ]
    },
    classifiers = [
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3 :: Only',
    ],
    include_package_data=True,
)
