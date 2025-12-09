import pandas as pd
import matplotlib.pyplot as plt
import plotting
import sys

print("Checking adjustText...")
try:
    import adjustText
    print("adjustText passed")
except ImportError:
    print("adjustText NOT FOUND")

print("Testing plotting.plot_scatter_2d...")
df = pd.DataFrame({
    'x': [1, 2, 3],
    'y': [1, 2, 3],
    'group': ['A', 'A', 'B'],
    'label': ['L1', 'L2', 'L3']
})
appearance = {'A': 'red', 'B': 'blue'}

try:
    plotting.plot_scatter_2d(df, 'x', 'y', 'group', appearance, label_col='label', with_labels=True, figsize=(5,5))
    print("Plotting function executed successfully")
except Exception as e:
    print(f"Plotting failed: {e}")
