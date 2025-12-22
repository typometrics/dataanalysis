"""
Corpus preparation module.

Functions for handling CoNLL file splitting and organization.
"""

import os
import re
from tqdm import tqdm

def make_shorter_conll_files(langConllFiles, version):
    """
    Split large CoNLL files into chunks of 10,000 sentences each.
    
    Parameters
    ----------
    langConllFiles : dict
        Dictionary mapping language codes to lists of CoNLL file paths
    version : str
        Version string (e.g., 'ud-treebanks-v2.17')
        
    Returns
    -------
    tuple
        (lang2shortconll, allshortconll) where:
        - lang2shortconll: dict mapping language codes to lists of short file paths
        - allshortconll: flat list of all short file paths
    """
    # Load excluded treebanks
    excluded_treebanks = set()
    excluded_file = "excluded_treebanks.txt"
    if os.path.exists(excluded_file):
        with open(excluded_file, "r") as f:
            excluded_treebanks = set(line.strip() for line in f if line.strip())
    
    directory = version + "_short"
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    lang2shortconll = {}
    allshortconll = []
    
    for lang in tqdm(langConllFiles, desc="Processing languages"):
        lang2shortconll[lang] = []
        
        for conllfile in langConllFiles[lang]:
            # Check if this file is from an excluded treebank
            file_path_parts = conllfile.split(os.sep)
            if any(excluded in file_path_parts for excluded in excluded_treebanks):
                continue
            
            basename = os.path.basename(conllfile)
            starter = '' if basename.startswith(lang + '_') else lang + '_'
            
            with open(conllfile) as f:
                conll = f.read()
            sentences = conll.split('\n\n')
            
            for i in range(0, len(sentences), 10000):
                shortconll = '\n\n'.join(sentences[i:i+10000])
                shortconllfile = os.path.join(
                    directory, 
                    starter + basename.replace('.conllu', '') + f'_{i}.conllu'
                )
                lang2shortconll[lang].append(shortconllfile)
                allshortconll.append(shortconllfile)
                with open(shortconllfile, 'w') as f:
                    f.write(shortconll)
    
    print(f"Created {len(allshortconll)} short CoNLL files in {directory}")
    return lang2shortconll, allshortconll


def read_shorter_conll_files(langConllFiles, version):
    """
    Read existing shorter CoNLL files from directory.
    
    Parameters
    ----------
    langConllFiles : dict
        Dictionary mapping language codes to lists of CoNLL file paths
    version : str
        Version string (e.g., 'ud-treebanks-v2.17')
        
    Returns
    -------
    tuple
        (lang2shortconll, allshortconll)
    """
    # Load excluded treebanks and build exclusion patterns
    excluded_keywords = set()
    excluded_file = "excluded_treebanks.txt"
    if os.path.exists(excluded_file):
        with open(excluded_file, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    # Extract meaningful keywords from UD treebank names
                    # e.g., UD_French-ALTS -> fr_alts
                    # e.g., UD_French-PoitevinDIVITAL -> fr_poitevindivital
                    if line.startswith("UD_"):
                        parts = line[3:].split("-")
                        if len(parts) >= 2:
                            lang = parts[0].lower()
                            variant = parts[1].lower()
                            # Create keyword: language_variant (e.g., french_alts -> fr_alts)
                            if lang.startswith("french"):
                                excluded_keywords.add(f"fr_{variant}")
                            elif lang.startswith("german"):
                                excluded_keywords.add(f"de_{variant}")
                            # Also add the full variant
                            excluded_keywords.add(variant.lower())
    
    directory = version + "_short"
    if not os.path.exists(directory):
        print(f"Directory {directory} does not exist. Please run make_shorter_conll_files first.")
        return {}, []

    lang2shortconll = {}
    allshortconll = []
    
    for lang in langConllFiles:
        lang2shortconll[lang] = []
        # Check if directory exists before listing (handled above but good to be safe inside loop if something weird happens)
        try:
            for shortconllfile in os.listdir(directory):
                if shortconllfile.startswith(lang + '_'):
                    # Check if this file matches any excluded pattern
                    file_lower = shortconllfile.lower()
                    if any(keyword in file_lower for keyword in excluded_keywords):
                        continue
                    lang2shortconll[lang].append(os.path.join(directory, shortconllfile))
            allshortconll.extend(lang2shortconll[lang])
        except OSError:
            pass # Directory might not exist or empty
    
    print(f"Found {len(allshortconll)} short CoNLL files in {directory}")
    return lang2shortconll, allshortconll
