#!/usr/bin/env python3
"""
Extract the 'OV vs NDO vs VO' strip plots from the website HTML files
and save them as PDF for the poster (via cairosvg).
"""
import re
import os
import cairosvg

HTML_DIR = "html_analyses"
OUT_DIR = "plots"
os.makedirs(OUT_DIR, exist_ok=True)

pages = {
    'mal':  'mal_effect_mal.html',
    'rmal': 'mal_effect_rmal.html',
    'lmal': 'mal_effect_lmal.html',
}

for key, fname in pages.items():
    fpath = os.path.join(HTML_DIR, fname)
    with open(fpath, 'r') as f:
        html = f.read()
    
    # Split HTML into individual SVG blocks
    svg_blocks = re.findall(r'(<svg\b[^>]*>.*?</svg>)', html, re.DOTALL)
    
    # Find the one with "OV vs NDO vs VO"
    target_svg = None
    for block in svg_blocks:
        if 'OV vs NDO vs VO' in block:
            target_svg = block
            break  # take the first match (the OV/NDO/VO grouped strip)
    
    if target_svg is None:
        print(f"WARNING: No OV vs NDO vs VO chart found in {fname}")
        continue
    
    # Sanitize for XML validity
    # Replace HTML character references with actual unicode
    target_svg = target_svg.replace('→', '→')
    target_svg = target_svg.replace('−', '−')
    target_svg = target_svg.replace('β', 'β')
    target_svg = target_svg.replace('&nbsp;', ' ')
    # Also handle raw unicode that's already fine
    # Remove <title> tooltip elements (not needed for print)
    target_svg = re.sub(r'<title>.*?</title>', '', target_svg)
    
    # Ensure xmlns is present
    if 'xmlns=' not in target_svg.split('>')[0]:
        target_svg = target_svg.replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" ', 1)
    
    svg_full = '<?xml version="1.0" encoding="UTF-8"?>\n' + target_svg
    
    svg_path = os.path.join(OUT_DIR, f'poster_strip_{key}.svg')
    pdf_path = os.path.join(OUT_DIR, f'poster_strip_{key}.pdf')
    
    with open(svg_path, 'w', encoding='utf-8') as f:
        f.write(svg_full)
    print(f"Saved {svg_path}")
    
    # Convert to PDF
    cairosvg.svg2pdf(bytestring=svg_full.encode('utf-8'), write_to=pdf_path)
    print(f"Saved {pdf_path}")

print("Done.")
