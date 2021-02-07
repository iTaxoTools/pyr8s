"""A setuptools based setup module."""

# Always prefer setuptools over distutils
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

# Get the long description from the README file
long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(name='pyr8s',
    version='0.2',
    description='Calculate divergence times and rates of substitution for phylogenic trees',
    long_description=long_description,
    url='https://github.com/stefanpatman/pyr8s',
    author='Patmanidis Stefanos',
    author_email='stefanpatman91@gmail.com',
    install_requires=[
        'dendropy',
        'numpy',
        'scipy',
    ],
    extras_require={
        'dev': ['pyqt5ac'],
        'gui': ['pyqt5'],
    },
    entry_points = {
        'console_scripts': [
            'pyr8s=pyr8s.run:main',
            'pyr8s-qt=pyr8s.qt.run:main'
            ],
        'gui_scripts': [
            # These won't work as long as sys.stdio is referred in main
            # 'pyr8s_tk=pyr8s.run_tk:main',
            # 'pyr8s_qt=pyr8s.run_qt:main'
            ],
    },
    cmdclass = {
        'build_qt': CommandQtAutoCompile,
        'build_py': build_py
    },
    license='All rights reserved',
    packages=[
        'pyr8s',
        'pyr8s.param',
        # 'pyr8s.tk',
        'pyr8s.qt',
    ],
    include_package_data=True,
    # zip_safe=True,
)
