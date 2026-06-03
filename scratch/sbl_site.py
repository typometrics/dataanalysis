import pandas as pd
import os

def generate_sbl_dashboard(csv_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    df = pd.read_csv(csv_path)
    
    html = [
        "<!DOCTYPE html>",
        "<html><head><meta charset='utf-8'><title>SBL Laws Compliance</title>",
        "<style>",
        "body { font-family: sans-serif; margin: 20px; }",
        "table { border-collapse: collapse; width: 100%; font-size: 13px; }",
        "th, td { border: 1px solid #ddd; padding: 6px; text-align: right; }",
        "th { background-color: #f4f4f4; text-align: center; }",
        "td:first-child { text-align: left; font-weight: bold; }",
        "</style></head><body>",
        "<h1>Short-Before-Long (SBL) Laws Compliance</h1>",
        "<p>This table summarizes the compliance of 180 languages to the Horizontal, Vertical, and Diagonal laws up to n=4.</p>",
        "<table>",
        "<thead><tr>"
    ]
    
    headers = [
        "Language", "Type", 
        "H-Score", "H-GM", "H-Pct(<)", "H-Outer-GM",
        "V-Score", "V-GM", 
        "D-Score", "D-GM",
        "SbL Beta"
    ]
    for h in headers:
        html.append(f"<th>{h}</th>")
    html.append("</tr></thead><tbody>")
    
    for _, row in df.iterrows():
        # filter to just Standard for the simple view
        if row['Table_Type'] != 'Standard': continue
        
        lang = row['Language']
        html.append("<tr>")
        html.append(f"<td>{lang}</td>")
        html.append(f"<td>{row['Table_Type']}</td>")
        
        # Right side horizontal
        html.append(f"<td>{row['R_Horiz_Score']}/6</td>")
        html.append(f"<td>{row['R_Horiz_GM']:.3f}</td>" if pd.notna(row['R_Horiz_GM']) else "<td>-</td>")
        html.append(f"<td>{row['R_Horiz_Pct_Lt']:.1f}%</td>" if pd.notna(row['R_Horiz_Pct_Lt']) else "<td>-</td>")
        html.append(f"<td>{row['R_Horiz_Outer_GM']:.3f}</td>" if pd.notna(row['R_Horiz_Outer_GM']) else "<td>-</td>")
        
        # Right side vertical
        html.append(f"<td>{row['R_Vert_Score']}/6</td>")
        html.append(f"<td>{row['R_Vert_GM']:.3f}</td>" if pd.notna(row['R_Vert_GM']) else "<td>-</td>")
        
        # Right side diagonal
        html.append(f"<td>{row['R_Diag_Score']}/6</td>")
        html.append(f"<td>{row['R_Diag_GM']:.3f}</td>" if pd.notna(row['R_Diag_GM']) else "<td>-</td>")
        
        # Beta
        html.append(f"<td>{row['R_Complex_Beta']:.3f}</td>" if pd.notna(row['R_Complex_Beta']) else "<td>-</td>")
        
        html.append("</tr>")
        
    html.append("</tbody></table>")
    html.append("</body></html>")
    
    output_path = os.path.join(output_dir, 'index.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(html))
    print(f"Generated dashboard at {output_path}")

if __name__ == '__main__':
    generate_sbl_dashboard('data/sbl_laws_summary.csv', 'html_sbl_analyses')
