import pandas as pd
from impact_calculator import ImpactCalculator

# create test data
orig = pd.DataFrame({
    'a': [1, 2, None, 4],
    'b': ['x', 'y', 'z', None],
})

clean = pd.DataFrame({
    'a': [1.0, 2.0, 3.0],
    'b': ['X', 'Y', 'Z'],
})

calc = ImpactCalculator(orig, clean, [])
metrics = calc.calculate()
print("Metrics:")
for key, val in metrics.items():
    print(f"  {key}: {val}")
