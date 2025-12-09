
import pickle
import os

def find_de_files():
    with open('data/metadata.pkl', 'rb') as f:
        metadata = pickle.load(f)
    
    langShortConllFiles = metadata['langShortConllFiles']
    if 'de' in langShortConllFiles:
        print("German files found:")
        for p in langShortConllFiles['de'][:5]:
            print(p)
    else:
        print("No German files found in metadata.")

if __name__ == "__main__":
    find_de_files()
