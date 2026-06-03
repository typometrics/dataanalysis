import os
from sbl_html_utils import get_header, get_nav, get_footer

def generate(out_dir):
    html = [
        get_header("Short Before Long (SBL) Analyses"),
        get_nav("index.html"),
        "<h1>Short Before Long (SBL) / Helix Analysis</h1>",
        "<div class='explanation'>",
        "<h3>Introduction</h3>",
        "<p>This dashboard presents a global typological analysis of the <strong>Short-Before-Long (SBL)</strong> principle across 180 languages, using Universal Dependencies (UD) treebanks. The analysis relies on <em>Helix tables</em>, which compute the mean sizes of constituents at specific distances from the verb.</p>",
        "</div>",
        "<h2>Dashboard Contents</h2>",
        "<ul>",
        "<li><strong><a href='sbl_laws_explained.html'>The Sy Laws</a></strong>: Intuitive reformulations of the Horizontal, Vertical, and Diagonal laws with concrete examples.</li>",
        "<li><strong><a href='sbl_laws_compliance.html'>Laws Compliance Table</a></strong>: The master table tracking compliance to the laws and the complex SbL $\\beta$ slope for all languages.</li>",
        "<li><strong><a href='sbl_validation.html'>Validation & Diagnostics</a></strong>: A transparent spot-check view showing exactly how the laws are computed mathematically from raw TSV data.</li>",
        "<li><strong><a href='sbl_explorer.html'>Interactive Explorer</a></strong>: Detailed, sortable view of individual language Helix tables.</li>",
        "<li><strong><a href='sbl_laws_visualizations.html'>Visualizations</a></strong>: Graphical distributions and scatter plots of the log-log regressions.</li>",
        "</ul>",
        get_footer()
    ]
    
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write("\n".join(html))
