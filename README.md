# Pyr8s

Contains the core functionality for calculating divergence times and rates
of substitution for phylogenic trees. Implements NPRS using Powell.

Please make sure you have all required libraries:
```
$ pip install -r requirements.txt
```

Try running some samples in interactive mode:
```
$ python -i run.py tests/legacy_1
```

This automatically creates RateAnalysis object `a`.
It then parses selected file, imports the first tree and executes any nexus rate commands.

Explore the created arrays:
```
>>> a._array.variable
>>> a._array.time
>>> a._array.rate
```

Change parameters:
```
>>> a.param.general['number_of_guesses'] = 5
```

Run a new test:
```
>>> res = a.run()
```

Print results:
```
>>> res.print()
```

View and edit output trees:
```
>>> res.chronogram.print_plot()
>>> pdc = a._results.chronogram.phylogenetic_distance_matrix()
>>> pdc.mean_pairwise_distance()
>>> pdc.max_pairwise_distance_taxa()
```
