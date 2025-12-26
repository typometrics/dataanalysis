
import os
import glob
import psutil
import sys
# Ensure we can import conll_processing and conll
sys.path.append("/bigstorage/kim/typometrics/dataanalysis")
import conll_processing
from conll import conllFile2trees
import re
from tqdm import tqdm
import multiprocessing
import functools
import numpy as np
import argparse

# Compile regex pattern for relation splitting (same as conll_processing)
relation_split = re.compile(r'\W')

def get_span_size(tree, node_id, include_bastards=True):
    """Calculate span size for a node."""
    if include_bastards:
        span_nodes = tree[node_id].get('direct_span', tree[node_id]['span'])
    else:
        span_nodes = tree[node_id]['span']
    return len(span_nodes)

def process_file_custom(conll_filename, max_examples_per_config=1_000_000):
    """
    Process a single file to extract config examples with span sizes.
    """
    include_bastards = True
    config_examples = {}
    
    try:
        lang = os.path.basename(conll_filename).split('_')[0]
        
        for tree in conllFile2trees(conll_filename):
            # Add spans (critical for dep sizes and bastards)
            tree.addspan(exclude=['punct'], compute_bastards=include_bastards)
            
            # Extract examples using the shared function from conll_processing
            # This ensures we use the exact same logic for determining configurations
            # The shared function returns list of (config, verb_id, [dep_ids])
            verb_configs = conll_processing.extract_verb_config_examples(tree, include_bastards=include_bastards)
            
            for config, verb_id, dep_ids in verb_configs:
                # Local addition: Calculate span sizes for these dependents (not done in generic export)
                dep_sizes = {kid: get_span_size(tree, kid, include_bastards) for kid in dep_ids}
                
                if config not in config_examples:
                    config_examples[config] = []
                
                # Check limit
                if len(config_examples[config]) < max_examples_per_config:
                    sorted_ids = sorted([i for i in tree if isinstance(i, int)])
                    tree_dict = {
                        'forms': [tree[i].get('t', '_') for i in sorted_ids],
                        'upos': [tree[i].get('tag', '_') for i in sorted_ids],
                        'heads': [list(tree[i].get('gov', {}).keys())[0] if tree[i].get('gov') else 0 for i in sorted_ids],
                        'deprels': [list(tree[i].get('gov', {}).values())[0] if tree[i].get('gov') else 'root' for i in sorted_ids]
                    }
                    config_examples[config].append({
                        'tree': tree_dict,
                        'verb_id': verb_id,
                        'dep_ids': dep_ids,
                        'dep_sizes': dep_sizes # Dictionary {dep_id: size}
                    })
                    
        return config_examples
    except Exception as e:
        print(f"Error processing {conll_filename}: {e}")
        return {}

def tree_dict_to_reactive_dep_tree_html(tree_dict, verb_id, dep_ids, dep_sizes):
    """
    Convert a tree dictionary to reactive-dep-tree HTML format.
    Includes span size in MISC feature.
    """
    forms = tree_dict['forms']
    upos = tree_dict['upos']
    heads = tree_dict['heads']
    deprels = tree_dict['deprels']
    
    # Create text line
    sentence_text = ' '.join(forms)
    
    lines = [f'# text = {sentence_text}']
    for i, (form, pos, head, rel) in enumerate(zip(forms, upos, heads, deprels), 1):
        # Determine highlight color and other features
        misc = []
        
        if i == verb_id:
            misc.append('highlight=red')
        elif i in dep_ids:
            misc.append('highlight=green')
            # Add span size if available
            if i in dep_sizes:
                misc.append(f'span={dep_sizes[i]}') 
        else:
             pass
             
        misc_str = '|'.join(misc) if misc else '_'
        
        # Format: ID FORM LEMMA UPOS XPOS FEATS HEAD DEPREL DEPS MISC
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


def calculate_position_stats(examples):
    """
    Calculate geometric mean of span sizes for each position (Left/Right) across all examples.
    """
    left_sizes = {}  # index -> list of sizes
    right_sizes = {} # index -> list of sizes
    
    for ex in examples:
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
                items.append(f"Left {i+1}: <b>{gm:.2f}</b>")
        
        if items:
            stats_html += f"<p><strong>Pre-verbal (X...V):</strong> {', '.join(items)}</p>"

    # Right
    if right_sizes:
        indices = sorted(right_sizes.keys())
        items = []
        for i in indices:
            vals = right_sizes[i]
            if vals:
                gm = np.exp(np.mean(np.log(vals)))
                items.append(f"Right {i+1}: <b>{gm:.2f}</b>")
                
        if items:
            stats_html += f"<p><strong>Post-verbal (V...X):</strong> {', '.join(items)}</p>"
            
    stats_html += "</div>"
    return stats_html

def generate_html_for_config(config, examples, output_file, treebank_name):
    """
    Generate HTML file for one configuration with all its examples.
    """
    
    # Calculate stats
    stats_block = calculate_position_stats(examples)
    
    html_parts = []
    html_parts.append('<!DOCTYPE html>')
    html_parts.append('<html>')
    html_parts.append('<head>')
    html_parts.append('  <meta charset="utf-8">')
    html_parts.append(f'  <title>{treebank_name} - {config}</title>')
    html_parts.append('  <script src="https://unpkg.com/reactive-dep-tree/dist/reactive-dep-tree.umd.js" async deferred></script>')
    html_parts.append('  <style>')
    html_parts.append('    body { font-family: Arial, sans-serif; margin: 20px; }')
    html_parts.append('    h1 { color: #333; }')
    html_parts.append('    .example { margin-bottom: 40px; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }')
    html_parts.append('    .example-number { font-weight: bold; color: #666; margin-bottom: 10px; }')
    html_parts.append('  </style>')
    html_parts.append('</head>')
    html_parts.append('<body>')
    html_parts.append(f'  <h1>{treebank_name}: {config}</h1>')
    html_parts.append(stats_block)
    html_parts.append(f'  <p>{len(examples)} examples</p>')
    
    for i, example in enumerate(examples, 1):
        html_parts.append(f'  <div class="example">')
        html_parts.append(f'    <div class="example-number">Example {i}</div>')
        tree_html = tree_dict_to_reactive_dep_tree_html(
            example['tree'], 
            example['verb_id'], 
            example['dep_ids'],
            example['dep_sizes']
        )
        html_parts.append(f'    {tree_html}')
        html_parts.append('  </div>')
    
    html_parts.append('</body>')
    html_parts.append('</html>')
    
    html_content = '\n'.join(html_parts)
    
    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

def extract_configs(input_dir, output_dir, treebank_name, max_examples=1_000_000):
    """
    Main function to extract configurations from a treebank directory.
    """
    # 1. Find Files
    files = glob.glob(os.path.join(input_dir, "*.conllu"))
    if not files:
        print(f"No .conllu files found in {input_dir}")
        return

    print(f"Found {len(files)} files in {input_dir}")
    print(f"Processing with MAX_EXAMPLES={max_examples}")
    
    # 2. Process Files
    all_config_examples = {}
    
    with multiprocessing.Pool(psutil.cpu_count()) as pool:
        process_func = functools.partial(process_file_custom, max_examples_per_config=max_examples)
        results = list(tqdm(
            pool.imap(process_func, files),
            total=len(files),
            desc="Processing files"
        ))
        
        # Combine results
        for res in results:
            for config, examples in res.items():
                if config not in all_config_examples:
                    all_config_examples[config] = []
                all_config_examples[config].extend(examples)
    
    print("Processing complete. Generating HTML...")

    # 3. Generate HTML
    total_configs = 0
    total_examples = 0
    
    final_output_path = os.path.join(output_dir, treebank_name)
    os.makedirs(final_output_path, exist_ok=True)
    
    for config, examples in all_config_examples.items():
        safe_config = config.replace(' ', '_') + ".html"
        output_file = os.path.join(final_output_path, safe_config)
        generate_html_for_config(config, examples, output_file, treebank_name)
        
        total_configs += 1
        total_examples += len(examples)

    print(f"Done! Generated {total_configs} configuration files with {total_examples} total examples.")
    print(f"Output directory: {os.path.abspath(final_output_path)}")

def main():
    parser = argparse.ArgumentParser(description="Extract verb configurations from a treebank and generate HTML visualizations.")
    parser.add_argument("--input", "-i", required=True, help="Input directory containing .conllu files")
    parser.add_argument("--output", "-o", default="html_examples", help="Output directory (default: html_examples)")
    parser.add_argument("--name", "-n", required=True, help="Name of the treebank (used for folder name and titles)")
    parser.add_argument("--max", "-m", type=int, default=1_000_000, help="Maximum examples per configuration (default: 1,000,000)")
    
    args = parser.parse_args()
    
    extract_configs(args.input, args.output, args.name, args.max)

# Alias for notebook usage match
main_func = extract_configs

if __name__ == "__main__":
    main()
