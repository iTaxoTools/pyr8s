# Pyr8s

Contains the core functionality for calculating divergence times and rates
of substitution for phylogenic trees. Implements Non-Parametric Rate Smoothing using Powell.


## Quick start

Install using pip:

```
$ pip install .
```

Run the GUI:

```
$ pyr8s-qt
```

Simple command line tool:

```
$ pyr8s tests/legacy_1
```

## Launch without installing

Before the first time you use the program, you must install any required modules and auto-compile the Qt resource files:
```
$ pip install -r requirements.txt
$ python setup.py build_qt
```

You can now launch the GUI:
```
$ python launcher.py
```

## Packaging

You must first auto-compile Qt resources,
then use PyInstaller on the launcher **spec** file:
```
$ pip install pyinstaller
$ python setup.py build_qt
$ pyinstaller launcher.spec
```

## Module

You may import and use the pyr8s module in your python scripts.

To launch the GUI:
```
>>> import pyr8s.qt
>>> pyr8s.qt.main.show()
```

More examples to follow soon.

### Python interactive example

From the root directory, launch the Python interpreter:
```
$ python -i
```

Interactively parse and analyse a nexus file:
```
>>> import pyr8s.parse as p
>>> a = p.parse('tests/legacy_1')
```
This imports the first tree found and executes any nexus rate commands.
It then creates an instance `a` of `pyr8s.core.RateAnalysis` for manipulation.

If the file included a `divtime` command, the results are saved:
```
>>> a.results.print()
>>> a.results.chronogram.print_plot()
>>> a.results.chronogram.as_string(schema='newick')
```

Explore the arrays used for analysis:
```
>>> a._array.variable
>>> a._array.time
>>> a._array.rate
```

Browse and change parameters:
```
>>> a.param.keys()
>>> a.param.general.keys()
>>> a.param.general.number_of_guesses = 5
```

Run a new test:
```
>>> res = a.run()
```

View and edit output trees:
```
>>> pdc = a.results.chronogram.phylogenetic_distance_matrix()
>>> pdc.mean_pairwise_distance()
>>> pdc.max_pairwise_distance_taxa()
```

### Quick analysis

To quickly analyze a tree without setting any params or calibrations.
Example:
```
import pyr8s.parse
res = pyr8s.parse.quick(file='tests/legacy_1')
newick_tree = '(A:1,(B:2,C:3):4);'
res = pyr8s.parse.quick(tree=newick_tree)
```
You must provide either a file or a tree in newick string form.
The analysis uses nexus rates  settings if available.
By default, the branch length is guessed based on maximum branch length and the root age is set to 100. Please see the source code documentation for more.

## Acknowledgements

Michael J. Sanderson,\
r8s: inferring absolute rates of molecular evolution and divergence times in the absence of a molecular clock,\
(2003)

Michael J. Sanderson,\
A Nonparametric Approach to Estimating Divergence Times in the Absence of Rate Constancy,\
(1997)
