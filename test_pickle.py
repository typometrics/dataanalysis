import pickle
with open('data/all_langs_position2sizes.pkl', 'rb') as f:
    d = pickle.load(f)
lang = list(d.keys())[0]
print(f"Language: {lang}")
print("Keys:", list(d[lang].keys())[:10])
print("Value for first key:", d[lang][list(d[lang].keys())[0]][:5])
