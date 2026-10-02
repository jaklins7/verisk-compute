# compute

Applying a threshold and an aggregate limit to a column of numbers.

Usage:
```
cat input | python ./compute.py <threshold> <limit>
```

Each input is reduced by the threshold. Outputs are capped so
their running total never exceeds the limit. The last line is the total. 
In reinsurance terms this is an excess-of-loss layer.

## Tests

```
python -m unittest discover -v
```
