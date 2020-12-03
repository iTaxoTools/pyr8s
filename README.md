# Pyr8s

Contains the core functionality for calculating divergence times and rates
of substitution for phylogenic trees. Implements NPRS using Powell.

Install using pip:
```
$ pip install .
```

Try parsing a file using the console tool:
```
$ pyr8s tests/legacy_1
```

Or launch the graphical interface (under development):
```
$ pyr8s_tk
```

## Python interactive example

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

## Quick analysis

To quickly analyze a tree without setting any params or calibrations.
Example:
```
import pyr8s.core
res = pyr8s.core.RateAnalysis.quick(tree, nsites=1000)
```
Where `tree` is a string in Newick format and `nsites` is the number of sites
in sequences that branch lengths on input trees were calculated from.
If `nsites` is not provided then it is guessed based on maximum branch length.
The result `res` is a chronogram in Newick string format,
with the root set to an age of 100.
