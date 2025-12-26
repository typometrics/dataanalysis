"""
Generate HTML visualizations from saved configuration examples.
Uses examples collected during data extraction to avoid re-parsing.
"""

import os
import glob
import pickle
import csv
import re
import math
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
from tqdm import tqdm
import numpy as np



def parse_config_structure(config):
    """
    Parse configuration string to get left and right dependent counts.
    Handles both exact configs (VXX, XXV) and partial configs (VXX_anyleft, XXV_anyright).
    """
    if 'V' not in config:
        return 0, 0
    
    # Strip partial suffixes if present
    base_config = config.split('_')[0]
    
    v_index = base_config.index('V')
    # Count X's (assuming X represents a dependent)
    left_count = base_config[:v_index].count('X')
    right_count = base_config[v_index+1:].count('X')
    return left_count, right_count


def calculate_position_stats(examples, global_stats=None, l_count=0, r_count=0, config_type='exact'):
    """
    Calculate geometric mean of span sizes for each position (Left/Right) across all examples.
    Optionally compare with global stats.
    
    Parameters
    ----------
    examples : list
        List of example dictionaries
    global_stats : dict
        Global statistics from Helix table
    l_count : int
        Number of left dependents in base configuration
    r_count : int
        Number of right dependents in base configuration
    config_type : str
        One of: 'exact', 'partial_left', 'partial_right', 'partial_both'
    """
    left_sizes = {}  # index -> list of sizes
    right_sizes = {} # index -> list of sizes
    
    for ex in examples:
        # Skip if dep_sizes not available
        if 'dep_sizes' not in ex:
            return ""
            
        vid = ex['verb_id']
        dids = ex['dep_ids']
        dsizes = ex['dep_sizes']
        
        # Sort dependents by ID
        # Left: d < vid
        # Right: d > vid
        left_deps = sorted([d for d in dids if d < vid])
        right_deps = sorted([d for d in dids if d > vid])
        
        for i, d in enumerate(left_deps):
            if i not in left_sizes: left_sizes[i] = []
            if d in dsizes and dsizes[d] > 0:
                left_sizes[i].append(dsizes[d])
            
        for i, d in enumerate(right_deps):
            if i not in right_sizes: right_sizes[i] = []
            if d in dsizes and dsizes[d] > 0:
                right_sizes[i].append(dsizes[d])
                
    stats_html = "<div style='margin-bottom: 20px; padding: 15px; background: #f0f8ff; border-radius: 5px; border: 1px solid #d0e0f0;'>"
    stats_html += "<h3 style='margin-top: 0; color: #0055aa;'>Geometric Mean Spans</h3>"
    
    # Legend with config type explanation
    context_str = ""
    config_desc = ""
    
    if config_type == 'partial_left':
        config_desc = f"<div style='color: #d87000; margin-bottom: 10px; font-style: italic;'>⚠ Partial Configuration: {l_count} left dependents, any right side</div>"
        context_str = f"L={l_count}, any R"
    elif config_type == 'partial_right':
        config_desc = f"<div style='color: #d87000; margin-bottom: 10px; font-style: italic;'>⚠ Partial Configuration: {r_count} right dependents, any left side</div>"
        context_str = f"any L, R={r_count}"
    elif config_type == 'partial_both':
        config_desc = f"<div style='color: #d87000; margin-bottom: 10px; font-style: italic;'>⚠ Partial Configuration: At least 1 left AND 1 right, any totals</div>"
        context_str = "bilateral, any totals"
    else:
        # Exact config
        if l_count == 1 and r_count == 1:
            context_str = "XVX Context"
        elif l_count > 0 or r_count > 0:
            parts = []
            if l_count: parts.append(f"L={l_count}")
            if r_count: parts.append(f"R={r_count}")
            context_str = "Totals: " + ", ".join(parts)
    
    if config_desc:
        stats_html += config_desc

    global_label = f"Global Helix Mean [{context_str}]" if context_str else "Global Language Mean"

    if global_stats:
        stats_html += f"<div style='font-size: 0.9em; color: #666; margin-bottom: 10px;'>Values: <b>Sample Mean</b> ({global_label})</div>"
    else:
        stats_html += "<div style='font-size: 0.9em; color: #666; margin-bottom: 10px;'>Values: <b>Sample Mean</b></div>"
    
    has_content = False
    
    # For partial configs, only show the relevant side
    # For exact configs, show the appropriate side(s)
    show_left = (config_type in ['exact', 'both', 'left', 'partial_left', 'partial_both'])
    show_right = (config_type in ['exact', 'both', 'right', 'partial_right', 'partial_both'])
    
    # Left
    if left_sizes and show_left:
        # Sort indices (0 is furthest from V)
        indices = sorted(left_sizes.keys())
        items = []
        
        # Build structure string e.g. (X_2 X_1 V)
        struct_parts = []
        for i in indices:
            dist = l_count - i
            struct_parts.append(f"X<sub>{dist}</sub>")
        struct_parts.append("V")
        struct_str = " ".join(struct_parts)
        
        for i in indices:
            vals = left_sizes[i]
            if vals:
                # GM = exp(mean(log(vals)))
                gm = np.exp(np.mean(np.log(vals)))
                
                # Distance from V (1-based)
                dist = l_count - i
                
                # Get global stat if available
                global_val_str = ""
                if global_stats:
                    # For partial configs, use anyother key
                    if config_type == 'partial_left':
                        key = f"left_{dist}_anyother"
                    elif config_type == 'partial_both' and l_count == 1 and r_count == 1:
                        key = "xvx_left_1_anyother"
                    else:
                        # Default: Aggregate for this distance
                        key = f"left_{dist}"
                        
                        # Specific: XVX
                        if l_count == 1 and r_count == 1 and dist == 1:
                            xvx_key = "xvx_left_1"
                            if xvx_key in global_stats:
                                key = xvx_key
                        # Specific: Total Length
                        elif l_count > 0:
                             tot_key = f"left_{dist}_totleft_{l_count}"
                             if tot_key in global_stats:
                                 key = tot_key
                    
                    if key in global_stats:
                        global_gm = global_stats[key]
                        global_val_str = f" <span style='color: #666; font-weight: normal;'>({global_gm:.2f})</span>"
                
                items.append(f"X<sub>{dist}</sub>: <b>{gm:.2f}</b>{global_val_str}")
        
        if items:
            stats_html += f"<p><strong>Pre-verbal ({struct_str}):</strong> {', '.join(items)}</p>"
            has_content = True

    # Right
    if right_sizes and show_right:
        indices = sorted(right_sizes.keys())
        items = []
        
        # Build structure string e.g. (V X_1 X_2)
        struct_parts = ["V"]
        for i in indices:
            dist = i + 1
            struct_parts.append(f"X<sub>{dist}</sub>")
        struct_str = " ".join(struct_parts)
        
        for i in indices:
            vals = right_sizes[i]
            if vals:
                gm = np.exp(np.mean(np.log(vals)))
                
                dist = i + 1
                
                # Get global stat
                global_val_str = ""
                if global_stats:
                    # For partial configs, use anyother key
                    if config_type == 'partial_right':
                        key = f"right_{dist}_anyother"
                    elif config_type == 'partial_both' and l_count == 1 and r_count == 1:
                        key = "xvx_right_1_anyother"
                    else:
                        # Default: Aggregate
                        key = f"right_{dist}"
                        
                        # Specific: XVX
                        if l_count == 1 and r_count == 1 and dist == 1:
                            xvx_key = "xvx_right_1"
                            if xvx_key in global_stats:
                                key = xvx_key
                        # Specific: Total Length
                        elif r_count > 0:
                             tot_key = f"right_{dist}_totright_{r_count}"
                             if tot_key in global_stats:
                                 key = tot_key

                    if key in global_stats:
                        global_gm = global_stats[key]
                        global_val_str = f" <span style='color: #666; font-weight: normal;'>({global_gm:.2f})</span>"
                
                items.append(f"X<sub>{dist}</sub>: <b>{gm:.2f}</b>{global_val_str}")
                
        if items:
            stats_html += f"<p><strong>Post-verbal ({struct_str}):</strong> {', '.join(items)}</p>"
            has_content = True
            
    stats_html += "</div>"
    
    return stats_html if has_content else ""



def load_config_examples(data_dir='data'):
    """Load saved configuration examples."""
    path = os.path.join(data_dir, 'all_config_examples.pkl')
    with open(path, 'rb') as f:
        return pickle.load(f)


def load_metadata(data_dir='data'):
    """Load language metadata for language names."""
    path = os.path.join(data_dir, 'metadata.pkl')
    with open(path, 'rb') as f:
        return pickle.load(f)


def tree_dict_to_reactive_dep_tree_html(tree_dict, verb_id, dep_ids, dep_sizes=None):
    """
    Convert a tree dictionary to reactive-dep-tree HTML format.
    
    Parameters
    ----------
    tree_dict : dict
        Dictionary with keys: 'forms', 'lemmas', 'upos', 'heads', 'deprels'
    verb_id : int
        1-based ID of the verb token
    dep_ids : list of int
        1-based IDs of dependent tokens
    dep_sizes : dict, optional
        Dictionary mapping token ID to span size
    
    Returns
    -------
    str
        HTML string for reactive-dep-tree
    """
    forms = tree_dict['forms']
    upos = tree_dict['upos']
    heads = tree_dict['heads']
    deprels = tree_dict['deprels']
    
    # Create text line
    sentence_text = ' '.join(forms)
    
    lines = [f'# text = {sentence_text}']
    for i, (form, pos, head, rel) in enumerate(zip(forms, upos, heads, deprels), 1):
        # Determine highlight color: red for verb, green for dependents
        misc_feats = []
        if i == verb_id:
            misc_feats.append('highlight=red')
        elif i in dep_ids:
            misc_feats.append('highlight=green')
            # Add span size if available
            if dep_sizes and i in dep_sizes:
                misc_feats.append(f'span={dep_sizes[i]}')
        
        misc_str = '|'.join(misc_feats) if misc_feats else '_'
        
        # Format: ID FORM LEMMA UPOS XPOS FEATS HEAD DEPREL DEPS MISC
        # Use FORM for LEMMA, UPOS for both UPOS and XPOS, highlight in MISC
        line = f"{i}\t{form}\t{form}\t{pos}\t{pos}\t_\t{head}\t{rel}\t_\t{misc_str}"
        lines.append(line)
    
    # Build CoNLL string without extra indentation
    conll_str = '\n'.join(lines)
    conll_str_escaped = conll_str.replace('"', '&quot;')
    
    return f'''<reactive-dep-tree
  interactive="true"
  shown-features="UPOS,LEMMA,FORM,MISC.span"
  conll="{conll_str_escaped}"
></reactive-dep-tree>'''


def generate_language_html(lang_code, lang_name, config_examples, lang_stats=None, output_dir='html_examples'):
    """
    Generate HTML file for one language with all its configuration examples.
    
    Parameters
    ----------
    lang_code : str
        Language code (e.g., 'ab')
    lang_name : str
        Language name (e.g., 'Abkhaz')
    config_examples : dict
        Dictionary mapping config strings to list of example dicts
    lang_stats : dict, optional
        Dictionary of global average span sizes for this language
    output_dir : str
        Output directory for HTML files
    """
    # Extract language code from treebank code (e.g., 'fr' from 'fr_gsd')
    base_lang_code = lang_code.split('_')[0]
    
    # Create language folder with base language code
    lang_folder = os.path.join(output_dir, f"{lang_name}_{base_lang_code}")
    os.makedirs(lang_folder, exist_ok=True)
    
    # Create samples subfolder inside language folder
    samples_folder = os.path.join(lang_folder, "samples")
    os.makedirs(samples_folder, exist_ok=True)
    
    # Generate HTML file for each configuration
    for config, examples in config_examples.items():
        if not examples:
            continue
            
        # Calculate stats for these examples, comparing with global stats
        l_count, r_count = parse_config_structure(config)
        config_class = classify_configuration(config)
        stats_block = calculate_position_stats(
            examples, 
            global_stats=lang_stats, 
            l_count=l_count, 
            r_count=r_count,
            config_type=config_class
        )
        
        html_parts = []
        html_parts.append('<!DOCTYPE html>')
        html_parts.append('<html>')
        html_parts.append('<head>')
        html_parts.append('  <meta charset="utf-8">')
        html_parts.append(f'  <title>{lang_name} - {config}</title>')
        html_parts.append('  <script src="https://unpkg.com/reactive-dep-tree/dist/reactive-dep-tree.umd.js" async deferred></script>')
        html_parts.append('  <style>')
        html_parts.append('    body { font-family: Arial, sans-serif; margin: 20px; }')
        html_parts.append('    h1 { color: #333; }')
        html_parts.append('    .example { margin-bottom: 40px; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }')
        html_parts.append('    .example-number { font-weight: bold; color: #666; margin-bottom: 10px; }')
        html_parts.append('  </style>')
        html_parts.append('</head>')
        html_parts.append('<body>')
        html_parts.append(f'  <h1>{lang_name} ({lang_code}): {config}</h1>')
        html_parts.append(stats_block)
        html_parts.append(f'  <p>{len(examples)} examples</p>')
        
        for i, example in enumerate(examples, 1):
            html_parts.append(f'  <div class="example">')
            source_file = example.get('source_file', '')
            source_html = f' <span style="font-weight:normal; font-size:0.9em; color:#888;">({source_file})</span>' if source_file else ''
            html_parts.append(f'    <div class="example-number">Example {i}{source_html}</div>')
            tree_html = tree_dict_to_reactive_dep_tree_html(
                example['tree'], 
                example['verb_id'], 
                example['dep_ids'],
                example.get('dep_sizes')
            )
            html_parts.append(f'    {tree_html}')
            html_parts.append('  </div>')
        
        html_parts.append('</body>')
        html_parts.append('</html>')
        
        html_content = '\n'.join(html_parts)
        
        # Save to file in samples subfolder (sanitize config name for filename)
        safe_config = config.replace(' ', '_')
        output_file = os.path.join(samples_folder, f'{safe_config}.html')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)


def parse_tsv_to_html(tsv_path, link_map=None):
    """
    Read TSV and Convert to HTML Table.
    
    Parameters
    ----------
    tsv_path : str
        Path to TSV file
    link_map : dict, optional
        Dictionary mapping cell text (e.g., "R tot=2") to URL (e.g., "samples/VXX_anyleft.html")
    """
    if not os.path.exists(tsv_path):
        return "<p><em>Table file not found.</em></p>"
    
    html = ['<div class="table-container">']
    html.append('<table class="helix-table">')
    
    with open(tsv_path, 'r', encoding='utf-8') as f:
        # Read all lines
        lines = [line.rstrip('\n') for line in f]
    
    # Simple TSV parsing
    for i, line in enumerate(lines):
        if not line.strip():
            continue
            
        cells = line.split('\t')
        
        # Determine row type (Header vs Data vs Comment)
        is_header = (i == 0) # Assumption
        
        html.append('<tr>')
        for cell in cells:
            tag = 'th' if is_header else 'td'
            # Simple content cleaning
            content = cell.strip()
            if not content:
                content = "&nbsp;"
            
            # Add Link if map provided and content matches
            if link_map and content in link_map:
                url = link_map[content]
                content = f'<a href="{url}" title="show samples" style="text-decoration:none; color:inherit; border-bottom:1px dotted #999;">{content}</a>'
            
            # Highlight special content
            style = ""
            # Strip tags for style check
            clean_content = re.sub(r'<[^>]+>', '', content).lower()
            
            if "→" in content or "←" in content or "↘" in content or "factor" in clean_content:
                style = ' style="color: #0066cc; font-size: 0.9em;"'
            elif "gm:" in content or "global:" in content: # Comment cell
                 style = ' style="color: #666; font-style: italic; font-size: 0.85em;"'
            
            html.append(f'<{tag}{style}>{content}</{tag}>')
        html.append('</tr>')
        
    html.append('</table>')
    html.append('</div>')
    return '\n'.join(html)


def get_helix_factors(tsv_path):
    """
    Extract specific factors from Helix Table.
    Returns (diag_right_last, diag_left_first) as floats (or None).
    """
    if not os.path.exists(tsv_path):
        return None, None
        
    diag_right = None
    diag_left = None
    
    try:
        with open(tsv_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f]
            
        for line in lines:
            if not line: continue
            cells = [c.strip() for c in line.split('\t')]
            if not cells: continue
            
            row_label = cells[0].lower()
            
            # M Diag Right: Last non-empty number
            if 'm diag right' in row_label:
                # Find last numeric-ish cell
                for cell in reversed(cells[1:]):
                    if not cell: continue
                    # Clean cell: remove ×, ↗, →, etc
                    val_str = re.sub(r'[×↗→←↘]', '', cell).strip()
                    try:
                        diag_right = float(val_str)
                        break
                    except ValueError:
                        continue
            
            # M Diag Left: First non-empty number
            if 'm diag left' in row_label:
                # Find first numeric-ish cell
                for cell in cells[1:]:
                    if not cell: continue
                    val_str = re.sub(r'[×↗→←↘]', '', cell).strip()
                    try:
                        diag_left = float(val_str)
                        break
                    except ValueError:
                        continue
                        
    except Exception as e:
        print(f"Error reading factors from {tsv_path}: {e}")
        
    return diag_right, diag_left


def get_corpus_stats(file_list):
    """
    Compute basic stats from CoNLL files.
    Returns (n_sentences, n_tokens).
    """
    n_sent = 0
    n_tok = 0
    
    for filepath in file_list:
        if not os.path.exists(filepath):
            continue
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                sent_count = content.count('\n\n')
                # Approximate token count (lines that are not empty string, not comments)
                # But fast way: total lines - sent_count usually works for simple conll
                # Better: count lines that start with digit
                # Even faster match for standard notebook logic:
                # langDict['nSentences'] = all_conll.count('\n\n')
                # langDict['nTokens'] = all_conll.count('\n') - langDict['nSentences']
                
                n_sent += sent_count
                # Note: this simple token count includes comments if they are on own lines
                # But let's stick to the user's cited notebook logic if possible
                n_tok += content.count('\n') - sent_count
        except Exception:
            pass
            
    return n_sent, n_tok



def generate_language_index(lang_folder, lang_code, lang_name, position2num_data):
    """Generate index.html for a specific language folder."""
    
    # 1. Find Tables
    # Try different naming conventions
    base_table_path = os.path.join(lang_folder, f"Helix_{lang_name}_{lang_code}.tsv")
    any_table_path = os.path.join(lang_folder, f"Helix_{lang_name}_{lang_code}_AnyOtherSide.tsv")
    
    if not os.path.exists(base_table_path):
        tsvs = glob.glob(os.path.join(lang_folder, "*.tsv"))
        base_candidates = [t for t in tsvs if "AnyOtherSide" not in t]
        if base_candidates:
            base_table_path = base_candidates[0]
            
    if not os.path.exists(any_table_path):
        tsvs = glob.glob(os.path.join(lang_folder, "*AnyOtherSide.tsv"))
        if tsvs:
            any_table_path = tsvs[0]

    # 2. Find Samples
    samples_dir = os.path.join(lang_folder, "samples")
    sample_files = []
    if os.path.exists(samples_dir):
        sample_files = glob.glob(os.path.join(samples_dir, "*.html"))
    
    # 3. Categorize Samples
    configs_by_type = {
        'left': [], 'right': [], 'mixed': [], 
        'partial_left': [], 'partial_right': [], 'partial_both': []
    }
    
    total_verbs = get_total_verb_instances(position2num_data) if position2num_data else 0
    
    for s_path in sample_files:
        filename = os.path.basename(s_path)
        config_name = os.path.splitext(filename)[0].replace('_', ' ') # Undo safe name
        
        ctype = classify_configuration(config_name)
        
        # Get Stats
        count_str = ""
        if position2num_data:
            pos_key = config_to_position_key(config_name)
            if pos_key:
                count = position2num_data.get(pos_key, 0)
                if total_verbs > 0:
                    pct = (count / total_verbs) * 100
                    count_str = f" ({count:,}, {pct:.1f}%)"
                else:
                    count_str = f" ({count:,})"
        
        link_html = f'<a href="samples/{filename}" class="config-link">{config_name}{count_str}</a>'
        
        # Classify logic in generate_html_examples returns 'both' for mixed
        # Map to our display categories
        target_cat = ctype
        if target_cat == 'both': target_cat = 'mixed'
            
        if target_cat in configs_by_type:
            configs_by_type[target_cat].append((config_name, link_html))
        else:
            configs_by_type['mixed'].append((config_name, link_html))
            
    # Sort
    for k in configs_by_type:
        configs_by_type[k].sort(key=lambda x: x[0])

    # 3b. Build Link Maps for Tables
    # We want to link row labels (e.g. "R tot=2") to sample files (e.g. "samples/VXX_anyleft.html")
    standard_link_map = {}
    anyother_link_map = {}
    
    for s_path in sample_files:
        filename = os.path.basename(s_path)
        config = os.path.splitext(filename)[0].replace('_', ' ') # e.g. "VXX anyleft"
        
        # Determine specific totals from config structure
        if 'V' not in config: continue
        
        base_config = config.split(' ')[0].split('_')[0] # "VXX" or "VXX_anyleft" -> "VXX"
        try:
            v_idx = base_config.index('V')
            left_part = base_config[:v_idx]
            right_part = base_config[v_idx+1:]
            l_count = left_part.count('X')
            r_count = right_part.count('X')
            
            # Map for Standard Table (Exact matches mostly, but if we have VXX we can link R tot=2)
            # Standard table usually implies exact contexts or "tot" contexts. 
            # If we have "VXX.html" (exact), it matches R tot=2 in a standard table better than nothing.
            # But the user specifically asked for "AnyOtherSide" table improvements.
            # We can try to populate both if sensible.
            
            ref_url = f"samples/{filename}"
            
            # 1. AnyOtherSide Logic
            # R tot=N -> V + X*N + _anyleft
            if 'anyleft' in config and l_count == 0 and r_count > 0:
                anyother_link_map[f'R tot={r_count}'] = ref_url
            
            # L tot=N -> X*N + V + _anyright
            if 'anyright' in config and r_count == 0 and l_count > 0:
                anyother_link_map[f'L tot={l_count}'] = ref_url
                
            # 2. Standard Table Logic (Zero-Other-Side)
            # Standard table usually implies exact contexts or "tot" contexts (where other side is ignored but for standard visualization it often aligns with zero-other-side).
            # The row "R tot=2" in a standard helix table specifically means VXX (with 0 left dependents).
            # So we check for exact configurations (no 'any' suffix).
            is_partial = 'any' in config
            if not is_partial:
                # R tot=N -> VXX (l=0, r=N)
                if l_count == 0 and r_count > 0:
                     standard_link_map[f'R tot={r_count}'] = ref_url
                # L tot=N -> XXV (l=N, r=0)
                if r_count == 0 and l_count > 0:
                     standard_link_map[f'L tot={l_count}'] = ref_url

            # Mixed / XVX
            if 'anyboth' in config:
                 # heuristic for XVX row?
                 pass

        except ValueError:
            pass

    # 4. Generate HTML
    html_parts = []
    html_parts.append('<!DOCTYPE html>')
    html_parts.append('<html><head><meta charset="utf-8">')
    html_parts.append(f'<title>{lang_name} ({lang_code}) - Typometrics Dashboard</title>')
    html_parts.append('''
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background: #f9f9f9; color: #333; }
        .container { max-width: 1400px; margin: 0 auto; background: #fff; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); border-radius: 8px; }
        h1 { border-bottom: 2px solid #eee; padding-bottom: 15px; margin-top: 0; color: #2c3e50; }
        h2 { color: #34495e; margin-top: 30px; border-left: 5px solid #3498db; padding-left: 10px; }
        
        /* Table Styles */
        .table-container { overflow-x: auto; margin-bottom: 20px; border: 1px solid #eee; border-radius: 4px; }
        .helix-table { border-collapse: collapse; width: 100%; font-family: 'Consolas', monospace; font-size: 0.95em; }
        .helix-table th, .helix-table td { padding: 8px 12px; border-bottom: 1px solid #eee; text-align: left; white-space: nowrap; }
        .helix-table th { background: #f8f9fa; font-weight: 600; color: #555; border-bottom: 2px solid #ddd; }
        .helix-table tr:hover { background: #f1f7ff; }
        
        /* Config Grid */
        .config-grid { display: flex; gap: 20px; margin-bottom: 30px; }
        .config-col { flex: 1; background: #f8f9fa; padding: 15px; border-radius: 6px; border: 1px solid #e9ecef; }
        .config-col h3 { margin-top: 0; font-size: 1.1em; color: #555; border-bottom: 1px solid #ddd; padding-bottom: 8px; }
        .config-list { display: flex; flex-direction: column; gap: 6px; }
        .config-link { text-decoration: none; color: #2c3e50; padding: 4px 8px; background: #fff; border: 1px solid #dee2e6; border-radius: 4px; font-size: 0.9em; transition: all 0.2s; }
        .config-link:hover { border-color: #3498db; color: #3498db; transform: translateX(2px); }
        
        .partial-section { background: #fff8f0; border-color: #ffe8cc; }
        .partial-section h3 { color: #d35400; border-color: #ffe8cc; }
        .partial-section .config-link { border-color: #ffe8cc; }
        .partial-section .config-link:hover { border-color: #e67e22; color: #e67e22; }
    </style>
    ''')
    html_parts.append('</head><body>')
    html_parts.append('<div class="container">')
    
    html_parts.append(f'<h1>{lang_name} <span style="font-weight: normal; color: #777; font-size: 0.7em;">({lang_code})</span></h1>')
    
    html_parts.append('<h2>Helix Table (Standard)</h2>')
    html_parts.append(parse_tsv_to_html(base_table_path, link_map=standard_link_map))
    
    html_parts.append('<h2>Partial Configurations (AnyOtherSide)</h2>')
    html_parts.append(parse_tsv_to_html(any_table_path, link_map=anyother_link_map))
    
    html_parts.append('<h2>Configuration Examples</h2>')
    
    # Exact Configs Row
    html_parts.append('<div class="config-grid">')
    
    # Left
    html_parts.append('<div class="config-col"><h3>Left Branching (X...V)</h3><div class="config-list">')
    if configs_by_type['left']:
        for _, link in configs_by_type['left']: html_parts.append(link)
    else: html_parts.append('<span style="color:#999">—</span>')
    html_parts.append('</div></div>')
    
    # Mixed
    html_parts.append('<div class="config-col"><h3>Mixed (X...VX...)</h3><div class="config-list">')
    if configs_by_type['mixed']:
        for _, link in configs_by_type['mixed']: html_parts.append(link)
    else: html_parts.append('<span style="color:#999">—</span>')
    html_parts.append('</div></div>')
    
    # Right
    html_parts.append('<div class="config-col"><h3>Right Branching (VX...)</h3><div class="config-list">')
    if configs_by_type['right']:
        for _, link in configs_by_type['right']: html_parts.append(link)
    else: html_parts.append('<span style="color:#999">—</span>')
    html_parts.append('</div></div>')
    
    html_parts.append('</div>') # End Grid
    
    # Partial Configs Row
    if configs_by_type['partial_left'] or configs_by_type['partial_right'] or configs_by_type['partial_both']:
        html_parts.append('<div class="config-grid">')
        
        # Partial Left
        html_parts.append('<div class="config-col partial-section"><h3>Left + Any Right</h3><div class="config-list">')
        for _, link in configs_by_type['partial_left']: html_parts.append(link)
        html_parts.append('</div></div>')
        
        # Partial Mixed
        html_parts.append('<div class="config-col partial-section"><h3>Bilateral Any</h3><div class="config-list">')
        for _, link in configs_by_type['partial_both']: html_parts.append(link)
        html_parts.append('</div></div>')
        
        # Partial Right
        html_parts.append('<div class="config-col partial-section"><h3>Right + Any Left</h3><div class="config-list">')
        for _, link in configs_by_type['partial_right']: html_parts.append(link)
        html_parts.append('</div></div>')
        
        html_parts.append('</div>')
    
    html_parts.append('</div></body></html>')
    
    with open(os.path.join(lang_folder, 'index.html'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(html_parts))


def process_language(args):
    """Process a single language (for parallel execution)."""
    lang_code, config_examples, lang_names, average_sizes_all, output_dir, position2num_data = args
    lang_name = lang_names.get(lang_code, lang_code)
    lang_stats = average_sizes_all.get(lang_code, {})
    
    # 1. Generate normal HTML examples
    generate_language_html(lang_code, lang_name, config_examples, lang_stats, output_dir)
    
    # NEW: 2. Generate Index automatically
    # Need to know the folder where it generated things
    base_lang_code = lang_code.split('_')[0]
    lang_folder = os.path.join(output_dir, f"{lang_name}_{base_lang_code}")
    
    generate_language_index(lang_folder, lang_code, lang_name, position2num_data)
    
    return lang_code


def classify_configuration(config):
    """
    Classify configuration as left-only, right-only, both, or partial.
    
    Parameters
    ----------
    config : str
        Configuration string like "VXX", "XXV", "VXX_anyleft", "XXV_anyright"
    
    Returns
    -------
    str
        'left', 'right', 'both', 'partial_left', 'partial_right', or 'partial_both'
    """
    if 'V' not in config:
        return 'both'
    
    # Check for partial suffixes
    if '_anyleft' in config:
        return 'partial_right'  # Right deps, any left
    elif '_anyright' in config:
        return 'partial_left'  # Left deps, any right
    elif '_anyboth' in config:
        return 'partial_both'  # Both sides, any totals
    
    # Standard exact configs
    base_config = config.split('_')[0]
    v_index = base_config.index('V')
    has_left = any(c == 'X' for c in base_config[:v_index])
    has_right = any(c == 'X' for c in base_config[v_index + 1:])
    
    if has_left and has_right:
        return 'both'
    elif has_left:
        return 'left'
    elif has_right:
        return 'right'
    else:
        return 'both'


def config_to_position_key(config):
    """
    Convert configuration string to position2num key.
    
    Parameters
    ----------
    config : str
        Configuration string like "VXX", "XXV", "XVX", "VXX_anyleft"
    
    Returns
    -------
    str or None
        Position key like 'right_2', 'left_2', 'right_3_anyother', or None
    """
    original_config = config
    
    # Handle suffixes for AnyOtherSide configs
    is_any = False
    
    # Check for suffixes (added by classify_configuration logic or file naming)
    # Note: filenames might use underscores, display names spaces.
    # The input here comes from the index generation loop:
    # config_name = os.path.splitext(filename)[0].replace('_', ' ')
    
    if 'anyleft' in config:
        config = config.replace(' anyleft', '').replace('_anyleft', '')
        is_any = True
    elif 'anyright' in config:
        config = config.replace(' anyright', '').replace('_anyright', '')
        is_any = True
    elif 'anyboth' in config:
        config = config.replace(' anyboth', '').replace('_anyboth', '')
        is_any = True
        
    if 'V' not in config:
        return None
    
    config = config.strip()
    try:
        v_index = config.index('V')
    except ValueError:
        return None
        
    left_count = v_index
    right_count = len(config) - v_index - 1
    
    key = None
    
    # Only return key for pure left or pure right configs (OR bilateral if keys exist?)
    if left_count > 0 and right_count == 0:
        key = f'left_{left_count}'
    elif right_count > 0 and left_count == 0:
        key = f'right_{right_count}'
    elif left_count > 0 and right_count > 0:
         # Bilateral. 
         # Keys like xvx_left_1, xvx_right_1 exist but correspond to SIDES of the config
         # The config itself is a whole.
         # For now, we might not have a direct exact key for "XVX" as a whole unit in position2num
         # position2num stores "left_1", "right_1", "xvx_left_1"...
         # But the HTML file is for the *configuration*.
         # If we can't map it uniquely to a single count, return None or a best guess?
         # Most users care about branching side stats.
         pass
         
    if key and is_any:
        key += '_anyother'
        
    return key


def get_total_verb_instances(position2num_data):
    """
    Calculate total verb instances for a language.
    
    Parameters
    ----------
    position2num_data : dict
        Position2num dictionary for a single language
    
    Returns
    -------
    int
        Total number of verb instances
    """
    total = 0
    
    # Add pure left configs (XV, XXV, etc.)
    for key, value in position2num_data.items():
        if key.startswith('left_') and '_tot' not in key and 'average' not in key and 'xvx' not in key:
            total += value
    
    # Add pure right configs (VX, VXX, etc.)
    for key, value in position2num_data.items():
        if key.startswith('right_') and '_tot' not in key and 'average' not in key:
            total += value
    
    # Add mixed configs (XVX, XXVX, etc.) - use left side count (same as right)
    for key, value in position2num_data.items():
        if key.startswith('xvx_left_'):
            total += value
    
    return total


def generate_root_index(output_dir, lang_names):
    """
    Generate root index.html with links to language indices and aggregate tables.
    """
    # 1. Find Language Indices
    lang_links = []
    # Scan for directories
    for item in os.listdir(output_dir):
        item_path = os.path.join(output_dir, item)
        if os.path.isdir(item_path):
            # Check for index.html inside
            if os.path.exists(os.path.join(item_path, 'index.html')):
                # Parse Name_code
                parts = item.rsplit('_', 1)
                if len(parts) == 2:
                    name, code = parts
                else:
                    name, code = item, '??'
                
                # Use metadata name if available, else dir name
                display_name = lang_names.get(code, name.replace('_', ' '))
                
                lang_links.append({
                    'name': display_name,
                    'code': code,
                    'dir': item
                })
    
    lang_links.sort(key=lambda x: x['name'])
    
    # 2. Find Aggregate Tables
    global_table_path = os.path.join(output_dir, "GLOBAL_average_table.tsv")
    
    family_tables = []
    for f in sorted(glob.glob(os.path.join(output_dir, "FAMILY_*_table.tsv"))):
        fname = os.path.basename(f)
        family_name = fname.replace("FAMILY_", "").replace("_table.tsv", "")
        family_tables.append((family_name, f))
        
    # 3. Generate HTML
    html = []
    html.append('<!DOCTYPE html>')
    html.append('<html><head><meta charset="utf-8">')
    html.append('<title>Helix Tables & Typometrics Dashboard</title>')
    html.append('''
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background: #f9f9f9; color: #333; }
        .container { max-width: 1400px; margin: 0 auto; background: #fff; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); border-radius: 8px; }
        h1 { border-bottom: 2px solid #eee; padding-bottom: 15px; margin-top: 0; color: #2c3e50; text-align: center; }
        h2 { color: #34495e; margin-top: 40px; border-left: 5px solid #3498db; padding-left: 10px; }
        .intro { text-align: center; color: #666; margin-bottom: 30px; }
        
        /* Language Grid */
        .lang-chips { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 40px; justify-content: center; }
        .lang-chip { 
            display: inline-block; padding: 4px 10px; background: #f8f9fa; 
            border: 1px solid #dee2e6; border-radius: 15px; 
            text-decoration: none; color: #333; font-size: 0.9em;
            transition: all 0.2s;
        }
        .lang-chip:hover { 
            background: #3498db; color: #fff; border-color: #3498db; 
            transform: translateY(-1px); box-shadow: 0 2px 5px rgba(52, 152, 219, 0.3);
        }
        .lang-chip strong { font-family: 'Consolas', monospace; font-weight: bold; margin-right: 4px; }
        
        /* Table Styles */
        .table-container { overflow-x: auto; margin-bottom: 20px; border: 1px solid #eee; border-radius: 4px; }
        .helix-table { border-collapse: collapse; width: 100%; font-family: 'Consolas', monospace; font-size: 0.9em; }
        .helix-table th, .helix-table td { padding: 6px 10px; border-bottom: 1px solid #eee; text-align: left; white-space: nowrap; }
        .helix-table th { background: #f8f9fa; font-weight: 600; color: #555; border-bottom: 2px solid #ddd; }
        .helix-table tr:hover { background: #f1f7ff; }
        
        .family-section { margin-bottom: 30px; }
    </style>
    ''')
    html.append('</head><body>')
    html.append('<div class="container">')
    
    html.append('<h1>Helix Tables & Typometrics Dashboard</h1>')
    html.append(f'<p class="intro">Analysis of {len(lang_links)} languages processed.</p>')
    
    # ---------------------------------------------------------
    # GATHER DATA FOR TABLE
    # ---------------------------------------------------------
    print("Gathering statistics for Root Index Table...")
    
    # Load Metadata
    meta = {}
    try:
        with open(os.path.join(output_dir, '..', 'metadata.pkl'), 'rb') as f:
            meta = pickle.load(f)
    except Exception:
        pass # fallback
        
    lang_files_map = meta.get('langConllFiles', {})
    lang_groups = meta.get('langnameGroup', {})
    
    # Load Bastard Stats
    bastard_pct_map = {}
    try:
        csv_path = os.path.join(output_dir, '..', 'bastard_stats.csv')
        if os.path.exists(csv_path):
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # CSV cols: Code, Language, Verbs, Bastards, Bastards_per_Verb_Pct, etc.
                    if 'Code' in row and 'Bastard_Pct' in row: # Check exact headers
                        pass
                    # Based on user request sample: Code, Language, Verbs, Bastards, Bastards_per_Verb_Pct
                    if 'Code' in row and 'Bastards_per_Verb_Pct' in row:
                        try:
                            bastard_pct_map[row['Code']] = float(row['Bastards_per_Verb_Pct'])
                        except:
                            pass
    except Exception as e:
        print(f"Warning: Could not load bastard stats: {e}")

    # Build rows
    table_rows = []
    
    # Parallelize this? iterating 100 langs reading files might trigger timeout if files are huge
    # But usually fast enough.
    
    for link in lang_links:
        code = link['code']
        name = link['name']
        folder_item = link['dir']
        
        # 1. Configs Link already exists in 'link' dict
        # We need data for columns
        
        # Metadata
        # Group lookup by name
        group = lang_groups.get(name, "Unknown")
        
        conll_files = lang_files_map.get(code, [])
        n_files = len(conll_files)
        
        # Corpus Stats
        # Resolve paths relative to data root
        # output_dir is 'data/helix_tables' typically?
        # data root is 'data'
        # conll files are relative to notebook root? Usually relative to 'data' or '.' 
        # In notebook 01: open(conllFile) works. 
        # Metadata paths like 'ud-treebanks-v2.17/...'
        # We need to prepend current working dir or similar.
        # generate_html_examples.py is in '.../dataanalysis'.
        
        abs_conll_files = []
        for cf in conll_files:
            # Try plain
            if os.path.exists(cf): abs_conll_files.append(cf)
            # Try data/
            elif os.path.exists(os.path.join('data', cf)): abs_conll_files.append(os.path.join('data', cf))
            # Try ../
            elif os.path.exists(os.path.join('..', cf)): abs_conll_files.append(os.path.join('..', cf))
        
        n_sent, n_tok = get_corpus_stats(abs_conll_files)
        avg_len = (n_tok / n_sent) if n_sent > 0 else 0
        
        # Bastard Stats
        bastard_pct = bastard_pct_map.get(code, -1)
        
        # Helix Factors
        tsv_path = os.path.join(output_dir, folder_item, f"Helix_{name}_{code}.tsv")
        if not os.path.exists(tsv_path):
             # Try glob
             tsvs = glob.glob(os.path.join(output_dir, folder_item, "*.tsv"))
             base = [t for t in tsvs if "AnyOtherSide" not in t]
             if base: tsv_path = base[0]
             
        m_diag_right, m_diag_left = get_helix_factors(tsv_path)
        
        table_rows.append({
            'code': code,
            'name': name,
            'link': f"{folder_item}/index.html",
            'group': group,
            'n_files': n_files,
            'n_sent': n_sent,
            'n_tok': n_tok,
            'avg_len': avg_len,
            'bastard': bastard_pct,
            'diag_right': m_diag_right,
            'diag_left': m_diag_left
        })

    # ---------------------------------------------------------
    # RENDER TABLE
    # ---------------------------------------------------------
    
    html.append('''
    <style>
        /* Detailed Table */
        .sortable-table { width: 100%; border-collapse: collapse; margin-bottom: 40px; font-size: 0.9em; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .sortable-table th, .sortable-table td { padding: 10px 12px; text-align: left; border-bottom: 1px solid #eee; }
        .sortable-table th { background-color: #f1f2f6; color: #2c3e50; font-weight: 600; cursor: pointer; user-select: none; position: sticky; top: 0; }
        .sortable-table th:hover { background-color: #e4e7eb; }
        .sortable-table tr:hover { background-color: #f8f9fa; }
        .sortable-table td.num { text-align: right; font-family: 'Consolas', monospace; }
        .sortable-table th.num { text-align: right; }
        
        .chip { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.85em; background: #eef2f7; color: #2c3e50; text-decoration: none; }
        .chip:hover { background: #3498db; color: white; }
        
        /* Sort indicators */
        .th-sort-asc::after { content: " ▲"; opacity: 0.7; font-size: 0.8em; }
        .th-sort-desc::after { content: " ▼"; opacity: 0.7; font-size: 0.8em; }
    </style>
    
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        const table = document.getElementById('langTable');
        const headers = table.querySelectorAll('th');
        
        headers.forEach((header, index) => {
            header.addEventListener('click', () => {
                const tbody = table.querySelector('tbody');
                const rows = Array.from(tbody.querySelectorAll('tr'));
                const type = header.dataset.type || 'text';
                const isAsc = !header.classList.contains('th-sort-asc');
                
                // Reset headers
                headers.forEach(h => h.classList.remove('th-sort-asc', 'th-sort-desc'));
                header.classList.add(isAsc ? 'th-sort-asc' : 'th-sort-desc');
                
                rows.sort((a, b) => {
                    let aVal = a.children[index].textContent.trim();
                    let bVal = b.children[index].textContent.trim();
                    
                    if (type === 'number') {
                        // Remove commas, %, etc
                        aVal = parseFloat(aVal.replace(/[,%]/g, '')) || 0;
                        bVal = parseFloat(bVal.replace(/[,%]/g, '')) || 0;
                        return isAsc ? aVal - bVal : bVal - aVal;
                    } else {
                        return isAsc ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
                    }
                });
                
                rows.forEach(row => tbody.appendChild(row));
            });
        });
    });
    </script>
    ''')

    html.append('<h2>Language Statistics & Indices</h2>')
    html.append('<div class="table-container">')
    html.append('<table id="langTable" class="sortable-table">')
    html.append('<thead><tr>')
    html.append('<th data-type="text">Code</th>')
    html.append('<th data-type="text">Language</th>')
    html.append('<th data-type="text">Group</th>')
    html.append('<th data-type="number" class="num">Files</th>')
    html.append('<th data-type="number" class="num">Sentences</th>')
    html.append('<th data-type="number" class="num">Tokens</th>')
    html.append('<th data-type="number" class="num">Avg Len</th>')
    html.append('<th data-type="number" class="num">Bastard%</th>')
    html.append('<th data-type="number" class="num">Diag Right</th>')
    html.append('<th data-type="number" class="num">Diag Left</th>')
    html.append('</tr></thead>')
    html.append('tbody')
    
    for r in table_rows:
        html.append('<tr>')
        html.append(f'<td><a href="{r["link"]}" class="chip">{r["code"]}</a></td>')
        html.append(f'<td><a href="{r["link"]}" style="text-decoration:none; color:inherit;">{r["name"]}</a></td>')
        html.append(f'<td>{r["group"]}</td>')
        html.append(f'<td class="num">{r["n_files"]}</td>')
        html.append(f'<td class="num">{r["n_sent"]:,}</td>')
        html.append(f'<td class="num">{r["n_tok"]:,}</td>')
        html.append(f'<td class="num">{r["avg_len"]:.1f}</td>')
        
        bval = f'{r["bastard"]:.1f}%' if r["bastard"] >= 0 else '-'
        html.append(f'<td class="num">{bval}</td>')
        
        dr = f'{r["diag_right"]:.2f}' if r["diag_right"] is not None else '-'
        html.append(f'<td class="num">{dr}</td>')
        
        dl = f'{r["diag_left"]:.2f}' if r["diag_left"] is not None else '-'
        html.append(f'<td class="num">{dl}</td>')
        
        html.append('</tr>')
        
    html.append('</tbody>')
    html.append('</table>')
    html.append('</div>')

    
    if os.path.exists(global_table_path):
        html.append('<h2>Global Analysis</h2>')
        html.append(parse_tsv_to_html(global_table_path))
        
    if family_tables:
        html.append('<h2>Family Analysis</h2>')
        for name, path in family_tables:
            html.append(f'<div class="family-section"><h3>{name}</h3>')
            html.append(parse_tsv_to_html(path))
            html.append('</div>')
            
    html.append('</div></body></html>')
    
    with open(os.path.join(output_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(html))
    
    print(f"Generated root index at {os.path.join(output_dir, 'index.html')}")


def generate_all_html(data_dir='data', output_dir='html_examples'):
    """
    Main function to generate all HTML visualizations from saved examples.
    
    Parameters
    ----------
    data_dir : str
        Directory containing saved data
    output_dir : str
        Directory for HTML output
    """
    print("Loading configuration examples...")
    all_config_examples = load_config_examples(data_dir)
    
    print("Loading metadata...")
    metadata = load_metadata(data_dir)
    lang_names = metadata.get('langNames', {})
    
    print("Loading position counts...")
    position2num_path = os.path.join(data_dir, 'all_langs_position2num.pkl')
    if os.path.exists(position2num_path):
        with open(position2num_path, 'rb') as f:
            position2num_all = pickle.load(f)
        print(f"Loaded position counts for {len(position2num_all)} languages")
    else:
        print(f"Warning: {position2num_path} not found. Counts will not be shown.")
        position2num_all = {}

    print("Loading average sizes (helix stats)...")
    avg_sizes_path = os.path.join(data_dir, 'all_langs_average_sizes.pkl')
    if os.path.exists(avg_sizes_path):
        with open(avg_sizes_path, 'rb') as f:
            average_sizes_all = pickle.load(f)
        print(f"Loaded average sizes for {len(average_sizes_all)} languages")
    else:
        print(f"Warning: {avg_sizes_path} not found. Global stats will not be shown.")
        average_sizes_all = {}
    
    print(f"Generating HTML for {len(all_config_examples)} languages...")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Prepare arguments for parallel processing
    args_list = [
        (lang_code, config_examples, lang_names, average_sizes_all, output_dir, position2num_all.get(lang_code, {}))
        for lang_code, config_examples in all_config_examples.items()
    ]
    
    # Process in parallel
    num_workers = min(multiprocessing.cpu_count(), len(args_list))
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        list(tqdm(
            executor.map(process_language, args_list),
            total=len(args_list),
            desc="Generating HTML files"
        ))
    
    print("Generating index...")
    generate_root_index(output_dir, lang_names)
    
    print(f"Done! HTML files saved to {output_dir}/")


if __name__ == '__main__':
    generate_all_html()
