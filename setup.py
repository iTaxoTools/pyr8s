from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()

setup(name='pyr8s',
    version='0.1',
    description='Calculate divergence times and rates of substitution for phylogenic trees',
    long_description=readme(),
    url='https://github.com/stefanpatman/pyr8s',
    author='Patmanidis Stefanos',
    author_email='stefanpatman91@gmail.com',
    install_requires=[
        'dendropy',
        'numpy',
        'scipy',
    ],
    extras_required={
        'pyr8s_qt': ['pyqt5']
    },
    entry_points = {
        'console_scripts': ['pyr8s=pyr8s.run:main'],
        'gui_scripts': [
            # 'pyr8s_tk=pyr8s.run_tk:main',
            'pyr8s_qt=pyr8s.run_qt:main'
            ],
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
