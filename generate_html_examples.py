"""
Generate HTML visualizations from saved configuration examples.
Uses examples collected during data extraction to avoid re-parsing.
"""

import os
import pickle
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
from tqdm import tqdm
import numpy as np


def calculate_position_stats(examples, global_stats=None):
    """
    Calculate geometric mean of span sizes for each position (Left/Right) across all examples.
    Optionally compare with global stats.
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
    
    # Legend
    if global_stats:
        stats_html += "<div style='font-size: 0.9em; color: #666; margin-bottom: 10px;'>Values: <b>Sample Mean</b> (Global Language Mean)</div>"
    else:
        stats_html += "<div style='font-size: 0.9em; color: #666; margin-bottom: 10px;'>Values: <b>Sample Mean</b></div>"
    
    has_content = False
    
    # Left
    if left_sizes:
        # Sort indices
        indices = sorted(left_sizes.keys())
        items = []
        for i in indices:
            vals = left_sizes[i]
            if vals:
                # GM = exp(mean(log(vals)))
                gm = np.exp(np.mean(np.log(vals)))
                
                # Get global stat if available
                global_val_str = ""
                if global_stats:
                    # Key is left_{i+1}
                    key = f"left_{i+1}"
                    if key in global_stats:
                        global_gm = global_stats[key]
                        global_val_str = f" <span style='color: #666; font-weight: normal;'>({global_gm:.2f})</span>"
                
                items.append(f"Left {i+1}: <b>{gm:.2f}</b>{global_val_str}")
        
        if items:
            stats_html += f"<p><strong>Pre-verbal (X...V):</strong> {', '.join(items)}</p>"
            has_content = True

    # Right
    if right_sizes:
        indices = sorted(right_sizes.keys())
        items = []
        for i in indices:
            vals = right_sizes[i]
            if vals:
                gm = np.exp(np.mean(np.log(vals)))
                
                # Get global stat
                global_val_str = ""
                if global_stats:
                    # Key is right_{i+1}
                    key = f"right_{i+1}"
                    if key in global_stats:
                        global_gm = global_stats[key]
                        global_val_str = f" <span style='color: #666; font-weight: normal;'>({global_gm:.2f})</span>"
                
                items.append(f"Right {i+1}: <b>{gm:.2f}</b>{global_val_str}")
                
        if items:
            stats_html += f"<p><strong>Post-verbal (V...X):</strong> {', '.join(items)}</p>"
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
    
    return f'''<reactive-dep-tree
  interactive="true"
  shown-features="UPOS,LEMMA,FORM,MISC.span"
  conll="{conll_str}"
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
    # Create language folder with matching naming convention
    lang_folder = os.path.join(output_dir, f"{lang_name}_{lang_code}")
    os.makedirs(lang_folder, exist_ok=True)
    
    # Generate HTML file for each configuration
    for config, examples in config_examples.items():
        if not examples:
            continue
            
        # Calculate stats for these examples, comparing with global stats
        stats_block = calculate_position_stats(examples, global_stats=lang_stats)
        
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
            html_parts.append(f'    <div class="example-number">Example {i}</div>')
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
        
        # Save to file (sanitize config name for filename)
        safe_config = config.replace(' ', '_')
        output_file = os.path.join(lang_folder, f'{safe_config}.html')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)


def process_language(args):
    """Process a single language (for parallel execution)."""
    lang_code, config_examples, lang_names, average_sizes_all, output_dir = args
    lang_name = lang_names.get(lang_code, lang_code)
    lang_stats = average_sizes_all.get(lang_code, {})
    generate_language_html(lang_code, lang_name, config_examples, lang_stats, output_dir)
    return lang_code


def classify_configuration(config):
    """
    Classify configuration as left-only, right-only, or both.
    
    Parameters
    ----------
    config : str
        Configuration string like "VXX" or "XXV"
    
    Returns
    -------
    str
        'left' if all X's before V, 'right' if all X's after V, 'both' otherwise
    """
    if 'V' not in config:
        return 'both'
    
    v_index = config.index('V')
    has_left = any(c == 'X' for c in config[:v_index])
    has_right = any(c == 'X' for c in config[v_index + 1:])
    
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
        Configuration string like "VXX", "XXV", "XVX"
    
    Returns
    -------
    str or None
        Position key like 'right_2', 'left_2', or None for mixed configs
    """
    if 'V' not in config:
        return None
    
    v_index = config.index('V')
    left_count = v_index
    right_count = len(config) - v_index - 1
    
    # Only return key for pure left or pure right configs
    if left_count > 0 and right_count == 0:
        return f'left_{left_count}'
    elif right_count > 0 and left_count == 0:
        return f'right_{right_count}'
    else:
        return None


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


def generate_index_html(all_config_examples, lang_names, position2num_all, output_dir='html_examples'):
    """
    Generate index.html with organized navigation.
    
    Parameters
    ----------
    all_config_examples : dict
        Dictionary mapping language codes to config examples
    lang_names : dict
        Dictionary mapping language codes to language names
    position2num_all : dict
        Dictionary mapping language codes to position2num data (contains counts)
    output_dir : str
        Output directory for HTML files
    """
    # Organize languages and their configurations
    lang_configs = {}
    for lang_code, configs in all_config_examples.items():
        lang_name = lang_names.get(lang_code, lang_code)
        lang_configs[lang_code] = {
            'name': lang_name,
            'configs': list(configs.keys())
        }
    
    html_parts = []
    html_parts.append('<!DOCTYPE html>')
    html_parts.append('<html>')
    html_parts.append('<head>')
    html_parts.append('  <meta charset="utf-8">')
    html_parts.append('  <title>Verb Configuration Examples</title>')
    html_parts.append('  <style>')
    html_parts.append('    body { font-family: Arial, sans-serif; margin: 20px; max-width: 1200px; }')
    html_parts.append('    h1 { color: #333; text-align: center; }')
    html_parts.append('    .stats { text-align: center; margin: 20px 0; color: #666; }')
    html_parts.append('    .quick-nav { background: #f5f5f5; padding: 15px; margin: 20px 0; border-radius: 5px; }')
    html_parts.append('    .quick-nav a { margin-right: 15px; color: #0066cc; text-decoration: none; }')
    html_parts.append('    .quick-nav a:hover { text-decoration: underline; }')
    html_parts.append('    .language { margin-bottom: 30px; padding: 15px; background: #fafafa; border-radius: 5px; }')
    html_parts.append('    .language h3 { margin: 0 0 15px 0; color: #333; border-bottom: 2px solid #ddd; padding-bottom: 5px; }')
    html_parts.append('    .config-table { display: table; width: 100%; border-collapse: collapse; }')
    html_parts.append('    .config-row { display: table-row; }')
    html_parts.append('    .config-column { display: table-cell; padding: 10px; vertical-align: top; width: 33.33%; border: 1px solid #ddd; }')
    html_parts.append('    .config-column h4 { margin: 0 0 10px 0; color: #555; font-size: 0.9em; }')
    html_parts.append('    .config-links { display: flex; flex-direction: column; gap: 5px; }')
    html_parts.append('    .config-link { display: inline-block; padding: 4px 8px; background: #e0e0e0; ')
    html_parts.append('                   border-radius: 3px; text-decoration: none; color: #333; font-size: 0.9em; }')
    html_parts.append('    .config-link:hover { background: #d0d0d0; }')
    html_parts.append('  </style>')
    html_parts.append('</head>')
    html_parts.append('<body>')
    html_parts.append('  <h1>Verb Configuration Examples by Language</h1>')
    
    total_langs = len(all_config_examples)
    html_parts.append(f'  <div class="stats">')
    html_parts.append(f'    <p><strong>{total_langs}</strong> languages</p>')
    html_parts.append(f'  </div>')
    
    # Quick access by language code
    html_parts.append('  <div class="quick-nav">')
    html_parts.append('    <strong>Quick Access by Language:</strong><br>')
    all_langs_sorted = sorted(lang_configs.items(), key=lambda x: x[0])
    for lang_code, info in all_langs_sorted:
        html_parts.append(f'    <a href="#{lang_code}">{lang_code}</a>')
    html_parts.append('  </div>')
    
    # List all languages with their configurations in a table
    for lang_code, info in sorted(lang_configs.items(), key=lambda x: x[1]['name']):
        lang_name = info['name']
        configs = info['configs']
        
        # Calculate total verb instances for percentage calculation
        total_verbs = 0
        if lang_code in position2num_all:
            total_verbs = get_total_verb_instances(position2num_all[lang_code])
        
        # Categorize configurations by type
        left_configs = []  # X...V
        mixed_configs = []  # X...VX...
        right_configs = []  # VX...
        
        for config in configs:
            config_type = classify_configuration(config)
            if config_type == 'left':
                left_configs.append(config)
            elif config_type == 'right':
                right_configs.append(config)
            else:
                mixed_configs.append(config)
        
        html_parts.append(f'  <div class="language" id="{lang_code}">')
        html_parts.append(f'    <h3>{lang_name} ({lang_code})</h3>')
        html_parts.append(f'    <div class="config-table">')
        html_parts.append(f'      <div class="config-row">')
        
        # Column 1: Left branching (X...V)
        html_parts.append(f'        <div class="config-column">')
        html_parts.append(f'          <h4>Left Branching (X...V)</h4>')
        html_parts.append(f'          <div class="config-links">')
        if left_configs:
            for config in sorted(left_configs):
                safe_config = config.replace(' ', '_')
                # Get count and percentage from position2num
                count_str = ''
                pos_key = config_to_position_key(config)
                if pos_key and lang_code in position2num_all:
                    count = position2num_all[lang_code].get(pos_key, 0)
                    if total_verbs > 0:
                        percentage = (count / total_verbs) * 100
                        count_str = f' ({count:,}, {percentage:.1f}%)'
                    else:
                        count_str = f' ({count:,})'
                html_parts.append(f'            <a class="config-link" href="{lang_name}_{lang_code}/{safe_config}.html">{config}{count_str}</a>')
        else:
            html_parts.append(f'            <span style="color: #999;">—</span>')
        html_parts.append(f'          </div>')
        html_parts.append(f'        </div>')
        
        # Column 2: Mixed (X...VX...)
        html_parts.append(f'        <div class="config-column">')
        html_parts.append(f'          <h4>Mixed (X...VX...)</h4>')
        html_parts.append(f'          <div class="config-links">')
        if mixed_configs:
            for config in sorted(mixed_configs):
                safe_config = config.replace(' ', '_')
                html_parts.append(f'            <a class="config-link" href="{lang_name}_{lang_code}/{safe_config}.html">{config}</a>')
        else:
            html_parts.append(f'            <span style="color: #999;">—</span>')
        html_parts.append(f'          </div>')
        html_parts.append(f'        </div>')
        
        # Column 3: Right branching (VX...)
        html_parts.append(f'        <div class="config-column">')
        html_parts.append(f'          <h4>Right Branching (VX...)</h4>')
        html_parts.append(f'          <div class="config-links">')
        if right_configs:
            for config in sorted(right_configs):
                safe_config = config.replace(' ', '_')
                # Get count and percentage from position2num
                count_str = ''
                pos_key = config_to_position_key(config)
                if pos_key and lang_code in position2num_all:
                    count = position2num_all[lang_code].get(pos_key, 0)
                    if total_verbs > 0:
                        percentage = (count / total_verbs) * 100
                        count_str = f' ({count:,}, {percentage:.1f}%)'
                    else:
                        count_str = f' ({count:,})'
                html_parts.append(f'            <a class="config-link" href="{lang_name}_{lang_code}/{safe_config}.html">{config}{count_str}</a>')
        else:
            html_parts.append(f'            <span style="color: #999;">—</span>')
        html_parts.append(f'          </div>')
        html_parts.append(f'        </div>')
        
        html_parts.append(f'      </div>')
        html_parts.append(f'    </div>')
        html_parts.append(f'  </div>')
    
    html_parts.append('</body>')
    html_parts.append('</html>')
    
    html_content = '\n'.join(html_parts)
    index_path = os.path.join(output_dir, 'index.html')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Generated index at {index_path}")


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
        (lang_code, config_examples, lang_names, average_sizes_all, output_dir)
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
    generate_index_html(all_config_examples, lang_names, position2num_all, output_dir)
    
    print(f"Done! HTML files saved to {output_dir}/")


if __name__ == '__main__':
    generate_all_html()
