
import pickle
import os

data_path = 'data/sentence_disorder_percentages.pkl'
if os.path.exists(data_path):
    with open(data_path, 'rb') as f:
        data = pickle.load(f)
    stats = data.get('fr', {})
    
    # Check keys present
    print("Keys sample:")
    keys = list(stats.keys())[:10]
    print(keys)
    
    # Check if Tot=1 exists?
    t1_keys = [k for k in stats.keys() if k[1] == 1]
    print(f"Tot=1 keys: {t1_keys}")
    
    # Check Tot=2 pair 0
    if ('right', 2, 0) in stats:
        d = stats[('right', 2, 0)]
        print(f"Right Tot=2 Pair 0: {d}")
        print(f"Sum: {d['lt'] + d['eq'] + d['gt']}")
else:
    print("Data not found")
