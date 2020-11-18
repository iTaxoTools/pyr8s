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
    entry_points = {
        'console_scripts': ['pyr8s=pyr8s.run:main'],
    },
    # license='N/A',
    packages=[
        'pyr8s',
    ],
    include_package_data=True
    # zip_safe=False
)
