from Executor import Executor
import pandas as pd

exe = Executor('sample_data/test.csv')
exe.df = pd.DataFrame({'a':[1,2,3]})
exe.rules = {'a':'def clean_a(s):\n    eval("1+1")\n    return s'}
try:
    exe.apply_rules()
except Exception as exc:
    print('caught', exc)
