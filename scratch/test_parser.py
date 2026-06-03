import sys

def parse_helix_tsv(filepath):
    data = {'R': {}, 'L': {}}
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip('\n').split('\t')
            if not parts: continue
            
            row_name = parts[0].strip()
            if row_name.startswith('R tot='):
                n = int(row_name.split('=')[1])
                data['R'][n] = {}
                for k in range(1, n+1):
                    idx = 10 + 2 * (k - 1)
                    if idx < len(parts) and parts[idx].strip():
                        try:
                            data['R'][n][k] = float(parts[idx].strip())
                        except ValueError:
                            pass
            elif row_name.startswith('L tot='):
                n = int(row_name.split('=')[1])
                data['L'][n] = {}
                for k in range(1, n+1):
                    idx = 8 - 2 * (k - 1)
                    if idx >= 0 and idx < len(parts) and parts[idx].strip():
                        try:
                            data['L'][n][k] = float(parts[idx].strip())
                        except ValueError:
                            pass
    return data

import pprint
pprint.pprint(parse_helix_tsv('data/helix_tables/French_fr/Helix_French_fr.tsv'))
