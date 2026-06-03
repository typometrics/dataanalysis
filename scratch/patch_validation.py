import os
import re

with open('sbl_page_validation.py', 'r') as f:
    content = f.read()

# Replace legends
content = content.replace("1: $R_2^1<R_2^2$, 2: $R_3^1<R_3^2$, 3: $R_3^2<R_3^3$, 4: $R_4^1<R_4^2$, 5: $R_4^2<R_4^3$, 6: $R_4^3<R_4^4$", 
                          "1: $R_2^1 < R_2^2$, 2: $R_3^1 < R_3^2$, 3: $R_3^2 < R_3^3$, 4: $R_4^1 < R_4^2$, 5: $R_4^2 < R_4^3$, 6: $R_4^3 < R_4^4$")
content = content.replace("1: $R_2^1<R_1^1$, 2: $R_3^1<R_2^1$, 3: $R_4^1<R_3^1$, 4: $R_3^2<R_2^2$, 5: $R_4^2<R_3^2$, 6: $R_4^3<R_3^3$",
                          "1: $R_2^1 < R_1^1$, 2: $R_3^1 < R_2^1$, 3: $R_4^1 < R_3^1$, 4: $R_3^2 < R_2^2$, 5: $R_4^2 < R_3^2$, 6: $R_4^3 < R_3^3$")
content = content.replace("1: $R_1^1<R_2^2$, 2: $R_2^2<R_3^3$, 3: $R_3^3<R_4^4$, 4: $R_2^1<R_3^2$, 5: $R_3^2<R_4^3$, 6: $R_3^1<R_4^2$",
                          "1: $R_1^1 < R_2^2$, 2: $R_2^2 < R_3^3$, 3: $R_3^3 < R_4^4$, 4: $R_2^1 < R_3^2$, 5: $R_3^2 < R_4^3$, 6: $R_3^1 < R_4^2$")

# Insert French Example
french_code = """
    fr_tsv = "data/helix_tables/French_fr/Helix_French_fr.tsv"
    if os.path.exists(fr_tsv):
        fdata = parse_helix_tsv(fr_tsv)
        if fdata and 'R' in fdata:
            d_fr = fdata['R']
            def val(n, k): return get_val(d_fr, n, k)
            def _check_fr(v1, v2):
                if v1 is None or v2 is None: return "<td>-</td>"
                if v1 < v2: return f"<td style='color:green;'>✅ PASS ({v1:.3f} &lt; {v2:.3f})</td>"
                return f"<td style='color:red;'>❌ FAIL ({v1:.3f} &ge; {v2:.3f})</td>"
            
            html.extend([
                "<h3>Example: French (Right Side)</h3>",
                "<table style='width: auto; margin-bottom: 30px;'>",
                "<tr><th>Law</th><th>Rule</th><th>Values</th><th>Result</th></tr>",
                f"<tr><td>Horizontal 1</td><td>$R_2^1 < R_2^2$</td><td>{val(2,1):.3f} vs {val(2,2):.3f}</td>{_check_fr(val(2,1), val(2,2))}</tr>",
                f"<tr><td>Horizontal 2</td><td>$R_3^1 < R_3^2$</td><td>{val(3,1):.3f} vs {val(3,2):.3f}</td>{_check_fr(val(3,1), val(3,2))}</tr>",
                f"<tr><td>Horizontal 3</td><td>$R_3^2 < R_3^3$</td><td>{val(3,2):.3f} vs {val(3,3):.3f}</td>{_check_fr(val(3,2), val(3,3))}</tr>",
                f"<tr><td>Vertical 1</td><td>$R_2^1 < R_1^1$</td><td>{val(2,1):.3f} vs {val(1,1):.3f}</td>{_check_fr(val(2,1), val(1,1))}</tr>",
                f"<tr><td>Vertical 2</td><td>$R_3^1 < R_2^1$</td><td>{val(3,1):.3f} vs {val(2,1):.3f}</td>{_check_fr(val(3,1), val(2,1))}</tr>",
                f"<tr><td>Diagonal 1</td><td>$R_1^1 < R_2^2$</td><td>{val(1,1):.3f} vs {val(2,2):.3f}</td>{_check_fr(val(1,1), val(2,2))}</tr>",
                "</table>",
                "<h3>Global Matrix (All Languages)</h3>"
            ])
"""

content = content.replace("        \"<table id='validationTable' style='white-space: nowrap;'>\",", french_code + "\n        \"<div style='overflow-x:auto;'>\",\n        \"<table id='validationTable' style='white-space: nowrap;'>\",")

# Fix Header CSS
content = content.replace("style='text-align:center; background:#e8f5e9;'", "style='text-align:center; background:#e8f5e9; color:#333;'")
content = content.replace("style='text-align:center; background:#e3f2fd;'", "style='text-align:center; background:#e3f2fd; color:#333;'")
content = content.replace("style='text-align:center; background:#fff3e0;'", "style='text-align:center; background:#fff3e0; color:#333;'")

content = content.replace("background:#c8e6c9;'", "background:#c8e6c9; color:#333; top:74px;'")
content = content.replace("background:#bbdefb;'", "background:#bbdefb; color:#333; top:74px;'")
content = content.replace("background:#ffe0b2;'", "background:#ffe0b2; color:#333; top:74px;'")

with open('sbl_page_validation.py', 'w') as f:
    f.write(content)
