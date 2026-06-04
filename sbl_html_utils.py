import json

_COMMON_CSS = """
:root { color-scheme: light; }
html, body { background: #fff; }
body { font-family: Arial, sans-serif; max-width: 1500px; margin: 0 auto; padding: 20px; color: #222; }
h1 { color: #333; scroll-margin-top: 60px; }
h2 { color: #555; margin-top: 30px; scroll-margin-top: 60px; }
h3 { color: #666; margin-top: 20px; scroll-margin-top: 60px; }
a { color: #1976d2; }
table { border-collapse: collapse; width: 100%; margin-bottom: 30px; scroll-margin-top: 60px; }
th, td { border: 1px solid #ddd; padding: 6px 8px; text-align: center; font-size: 13px; }
th { background-color: #4CAF50; color: white; position: sticky; top: 38px; z-index: 5; cursor: pointer; }
th:hover { background-color: #45a049; }
.lang-name { text-align: left; font-weight: bold; white-space: nowrap; }
.score-positive { background-color: #c8e6c9; }
.score-negative { background-color: #ffcdd2; }
.score-neutral  { background-color: #fff9c4; }
.na-cell { color: #999; }
tr:nth-child(even) { background-color: #f9f9f9; }
tr:hover { background-color: #f1f1f1; }
.info-box { background: #f0f0f0; padding: 15px; border-radius: 5px; margin: 10px 0 20px 0; }
.nav-top { background: #333; color: white; padding: 0; margin: -20px -20px 20px -20px;
           border-radius: 0 0 6px 6px; position: sticky; top: 0; z-index: 100; }
.nav-top > ul { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; }
.nav-top > ul > li > a { display: block; color: #fff; padding: 10px 16px; text-decoration: none; }
.nav-top > ul > li:hover > a { background: #555; }
.nav-top .crumb-current > a { color: #ffeb3b; font-weight: bold; }
.nav-top .nav-spacer { flex: 1; }
.nav-top .nav-github { padding: 10px 16px; color: #fff; text-decoration: none; opacity: 0.85; }
.explanation { background: #fff3e0; padding: 15px; border-left: 4px solid #ff9800; margin: 20px 0; line-height: 1.5; }
.formula { font-family: monospace; background: #e0e0e0; padding: 2px 5px; border-radius: 3px; font-size: 14px; }
/* Modal CSS */
.modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; overflow: auto; background-color: rgba(0,0,0,0.4); }
.modal-content { background-color: #fefefe; margin: 2% auto; padding: 20px; border: 1px solid #888; width: 98%; max-width: 1800px; border-radius: 5px; position: relative; }
.close-modal { color: #aaa; float: right; font-size: 28px; font-weight: bold; cursor: pointer; position: absolute; right: 20px; top: 10px; }
.close-modal:hover, .close-modal:focus { color: black; text-decoration: none; cursor: pointer; }
.tsv-table { font-size: 12px; margin-top: 20px; width: 100%; overflow-x: auto; display: block; }
.tsv-table th, .tsv-table td { padding: 4px 6px; }
"""

def get_modal_js():
    return r"""
<script>
function openModal(id) {
    document.getElementById(id).style.display = "block";
}
function closeModal(id) {
    document.getElementById(id).style.display = "none";
}
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = "none";
    }
}
</script>
"""

def get_header(title):
    mathjax_js = """
<script>
MathJax = {
  tex: {
    inlineMath: [['$', '$'], ['\\\\(', '\\\\)']]
  }
};
</script>
<script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
"""
    return f'''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>{_COMMON_CSS}</style>
{mathjax_js}
{get_table_sort_js()}
{get_modal_js()}
<script src="https://unpkg.com/reactive-dep-tree/dist/reactive-dep-tree.umd.js" async deferred></script>
</head>
<body>
'''

def get_nav(current_page):
    menu = [
        ('index.html', 'Home', 'Return to the main dashboard'),
        ('sbl_laws_explained.html', 'The Laws', 'Detailed explanations of the Short-Before-Long (Sy) laws and metrics'),
        ('sbl_laws_compliance.html', 'Compliance', 'Master table of how well each language complies with the SBL laws'),
        ('sbl_validation.html', 'Validation', 'Diagnostics on N-sizes, empty fields, and statistical validity'),
        ('sbl_explorer.html', 'Explorer', 'Interactive tool to drill down into raw Helix tables per language'),
        ('sbl_significance.html', 'Significance', 'Statistical significance (p-values) across laws and metrics'),
        ('sbl_laws_visualizations.html', 'Visualizations', 'Scatter plots and histograms of SBL effects vs linguistic typology'),
        ('sbl_outer_effects.html', 'Outer Effects', 'Detailed plots of Outer Constituent size curves for n=1,2,3,4'),
        ('sbl_typology.html', 'Maps', 'Geographic distribution maps of compliance scores'),
        ('sbl_summary.html', 'Summary', 'Global summary statistics across language families and overall')
    ]
    
    parts = ['<nav class="nav-top"><ul>']
    for href, label, tooltip in menu:
        cls = ' class="crumb-current"' if href == current_page else ''
        parts.append(f'<li{cls}><a href="{href}" title="{tooltip}">{label}</a></li>')
    parts.append('<li class="nav-spacer"></li>')
    parts.append('</ul></nav>')
    return ''.join(parts)

def get_footer():
    return '\n</body>\n</html>'

def get_table_sort_js():
    return r"""
<style>
/* Ensure sticky header remains on top and doesn't get overlapped */
table th {
    position: sticky;
    top: 38px;
    z-index: 10;
    cursor: pointer;
    background-color: #4CAF50;
    color: white;
}
table th:hover {
    background-color: #45a049;
}
/* Sort icons */
th.sort-asc::after {
    content: " \25B2";
    font-size: 0.8em;
}
th.sort-desc::after {
    content: " \25BC";
    font-size: 0.8em;
}
</style>
<script>
document.addEventListener('DOMContentLoaded', function() {
    const tables = document.querySelectorAll('table');
    tables.forEach(table => {
        const headers = table.querySelectorAll('th');
        headers.forEach((header, index) => {
            header.addEventListener('click', () => {
                const tbody = table.querySelector('tbody') || table;
                const rows = Array.from(tbody.querySelectorAll('tr'));
                
                // If the table doesn't have a tbody, make sure we skip the header row
                const startIndex = table.querySelector('tbody') ? 0 : 1;
                const dataRows = rows.slice(startIndex);
                
                let isAsc = header.classList.contains('sort-asc');
                
                // Clear all sorting classes
                headers.forEach(h => {
                    h.classList.remove('sort-asc');
                    h.classList.remove('sort-desc');
                });
                
                // Toggle direction
                isAsc = !isAsc;
                if (isAsc) {
                    header.classList.add('sort-asc');
                } else {
                    header.classList.add('sort-desc');
                }
                
                // Sort the rows
                dataRows.sort((a, b) => {
                    const cellA = a.children[index];
                    const cellB = b.children[index];
                    
                    if (!cellA || !cellB) return 0;
                    
                    let valA = cellA.innerText.trim();
                    let valB = cellB.innerText.trim();
                    
                    // Try to parse as numbers
                    const numA = parseFloat(valA.replace(/[^0-9.-]+/g,""));
                    const numB = parseFloat(valB.replace(/[^0-9.-]+/g,""));
                    
                    const isNumA = !isNaN(numA) && valA !== '';
                    const isNumB = !isNaN(numB) && valB !== '';
                    
                    if (isNumA && isNumB) {
                        return isAsc ? numA - numB : numB - numA;
                    }
                    
                    return isAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
                });
                
                // Re-append rows in sorted order
                dataRows.forEach(row => tbody.appendChild(row));
            });
        });
    });
});
</script>
"""
