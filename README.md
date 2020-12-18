# Pyr8s

Contains the core functionality for calculating divergence times and rates
of substitution for phylogenic trees. Implements NPRS using Powell.


## Quick start

To launch the gui without installing:
```
$ python launcher.py
```

You may need to install the required libraries first:
```
$ pip install -r requirements.txt
```

## Installation

Install using pip:
```
$ pip install .
```

Try parsing a file using the console tool:
```
$ pyr8s tests/legacy_1
```

Or launch the graphical interface:
```
$ pyr8s_qt tests/legacy_1
```

## Building

Simply use PyInstaller on the launcher **spec** file:
```
$ pyinstaller launcher.spec
```

## Module

You may import and use the pyr8s module in your python scripts.
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
