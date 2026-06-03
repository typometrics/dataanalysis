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
.modal-content { background-color: #fefefe; margin: 5% auto; padding: 20px; border: 1px solid #888; width: 90%; max-width: 1200px; border-radius: 5px; position: relative; }
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
        ('index.html', 'Home'),
        ('sbl_laws_explained.html', 'The Sy Laws'),
        ('sbl_laws_compliance.html', 'Laws Compliance Table'),
        ('sbl_validation.html', 'Validation & Diagnostics'),
        ('sbl_explorer.html', 'Interactive Explorer'),
        ('sbl_significance.html', 'Significance Analysis'),
        ('sbl_laws_visualizations.html', 'Visualizations'),
        ('sbl_typology.html', 'Typological Maps'),
        ('sbl_summary.html', 'Global Summary')
    ]
    
    parts = ['<nav class="nav-top"><ul>']
    for href, label in menu:
        cls = ' class="crumb-current"' if href == current_page else ''
        parts.append(f'<li{cls}><a href="{href}">{label}</a></li>')
    parts.append('<li class="nav-spacer"></li>')
    parts.append('</ul></nav>')
    return ''.join(parts)

def get_footer():
    return '\n</body>\n</html>'

def get_table_sort_js():
    return r"""
<script>
var sortDirections = {};
function sortTable(tableId, colIndex, type) {
    const table = document.getElementById(tableId);
    if (!table) return;
    const tbody = table.tBodies[0];
    const rows = Array.from(tbody.rows);
    const k = tableId + '_' + colIndex;
    sortDirections[k] = !sortDirections[k];
    const asc = sortDirections[k];
    
    rows.sort((a, b) => {
        let av = a.cells[colIndex].textContent.trim();
        let bv = b.cells[colIndex].textContent.trim();
        
        if (type === 'number') {
            let an = parseFloat(av);
            let bn = parseFloat(bv);
            if (isNaN(an)) an = -Infinity;
            if (isNaN(bn)) bn = -Infinity;
            return asc ? an - bn : bn - an;
        } else {
            return asc ? av.localeCompare(bv) : bv.localeCompare(av);
        }
    });
    rows.forEach(r => tbody.appendChild(r));
}
</script>
"""
