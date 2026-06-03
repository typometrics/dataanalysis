import pickle

with open('data/all_langs_position2sizes.pkl', 'rb') as f:
    d = pickle.load(f)

lang = list(d.keys())[0]
print(f"Language: {lang}")

for k, v in list(d[lang].items())[:10]:
    if isinstance(v, list):
        print(f"Key: {k}, type: list, len: {len(v)}, first 5: {v[:5]}")
    elif isinstance(v, int):
        print(f"Key: {k}, type: int, val: {v}")
    elif isinstance(v, float):
        print(f"Key: {k}, type: float, val: {v}")
    else:
        print(f"Key: {k}, type: {type(v)}")
