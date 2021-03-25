"""A setuptools based setup module."""

from setuptools import setup, find_packages, Extension, Command
from setuptools.command.build_py import build_py as _build_py
import pathlib

here = pathlib.Path(__file__).parent.resolve()

class CommandQtAutoCompile(Command):
    """Custom command for auto-compiling Qt resource files"""
    description = 'run pyqt5ac on all resource files'
    user_options = []
    def initialize_options(self):
        """virtual overload"""
        pass
    def finalize_options(self):
        """virtual overload"""
        pass
    def run(self):
        """build_qt"""
        try:
            import pyqt5ac
            pyqt5ac.main(ioPaths=[
                [str(here/'**/qt/*.qrc'), '%%DIRNAME%%/%%FILENAME%%.py'],
                ])
        except ModuleNotFoundError as exception:
            raise ModuleNotFoundError('Missing Qt auto-compiler, please try: pip install pyqt5ac')

class build_py(_build_py):
    """Overrides setuptools build to autocompile first"""
    def run(self):
        self.run_command('build_qt')
        _build_py.run(self)

long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(name='pyr8s',
    version='0.3.1',
    description='Calculate divergence times and rates of substitution for phylogenic trees',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Patmanidis Stefanos',
    author_email='stefanpatman91@gmail.com',
    # package_dir={'': 'src'},
    # packages=find_packages(where='src'),
    packages=find_packages(),
    python_requires='>=3.6, <4',
    install_requires=[
        'dendropy',
        'numpy',
        'scipy',
        'pyqt5',
    ],
    extras_require={
        'dev': ['pyqt5ac'],
    },
    entry_points = {
        'console_scripts': [
            'pyr8s=pyr8s.run:main',
            'pyr8s-qt=pyr8s.qt.run:main'
            ],
    },
    cmdclass = {
        'build_qt': CommandQtAutoCompile,
        'build_py': build_py
    },
    classifiers = [
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3 :: Only',
    ]
)
