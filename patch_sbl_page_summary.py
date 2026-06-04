import sbl_page_summary
with open('sbl_page_summary.py', 'r') as f:
    code = f.read()

# Replace metric extractions
code = code.replace(
    "name2beta_r = {row['Language']: row['R_Complex_Beta'] for _, row in df_std.iterrows() if pd.notna(row['R_Complex_Beta'])}",
    """import numpy as np
    name2_r_outer = {row['Language']: np.log(row['R_Outer_Effect']) for _, row in df_std.iterrows() if pd.notna(row['R_Outer_Effect']) and row['R_Outer_Effect'] > 0}
    name2_l_outer = {row['Language']: np.log(row['L_Outer_Effect']) for _, row in df_std.iterrows() if pd.notna(row['L_Outer_Effect']) and row['L_Outer_Effect'] > 0}
    name2_horiz = {row['Language']: np.log(row['Horizontal_Right_Left_Effect']) for _, row in df_std.iterrows() if pd.notna(row['Horizontal_Right_Left_Effect']) and row['Horizontal_Right_Left_Effect'] > 0}"""
)
code = code.replace(
    "name2beta_l = {row['Language']: -row['L_Complex_Beta'] for _, row in df_std.iterrows() if pd.notna(row['L_Complex_Beta'])} # Negated so positive=compliant",
    ""
)

# Update chart generation
code = code.replace(
    """    create_chart(name2beta_r, "Right SbL Compliance (Beta Slope)", "Average Right Beta (positive = compliant)", "summary_family_r.svg")
    create_chart(name2beta_l, "Left SbL Compliance (Beta Slope, inverted)", "Average Left Beta (positive = compliant)", "summary_family_l.svg")
    
    # Combined
    name2beta_comb = {}
    for lang in set(name2beta_r.keys()).intersection(set(name2beta_l.keys())):
        name2beta_comb[lang] = (name2beta_r[lang] + name2beta_l[lang]) / 2
        
    create_chart(name2beta_comb, "Combined SbL Compliance (Beta Slope)", "Average Joint Beta (positive = compliant)", "summary_family.svg")""",
    """    create_chart(name2_r_outer, "Right Outer Constituent Ratio Effect", "Log(Effect Ratio) [>0 is compliant]", "summary_family_r_outer.svg")
    create_chart(name2_l_outer, "Left Outer Constituent Ratio Effect", "Log(Effect Ratio) [>0 is compliant]", "summary_family_l_outer.svg")
    create_chart(name2_horiz, "Horizontal Right-Left Effect", "Log(Effect Ratio) [>0 means Right > Left]", "summary_family_horiz.svg")"""
)

# Update HTML insertions
code = code.replace(
    """        "<div class='explanation'>",
        "<p>This chart aggregates the Short-Before-Long principle across WALS language families. ",
        "For the Left side, slopes are negated so that a positive value consistently means compliance with the SbL principle. ",
        "Families with at least 3 analyzed languages are included.</p>",
        "</div>",
        
        "<h3>Combined Right & Left Compliance</h3>",
        "<img src='summary_family.svg' alt='Combined Summary' style='width:100%; max-width:800px;'>",
        
        "<h3>Right Side Compliance</h3>",
        "<img src='summary_family_r.svg' alt='Right Summary' style='width:100%; max-width:800px;'>",
        
        "<h3>Left Side Compliance</h3>",
        "<img src='summary_family_l.svg' alt='Left Summary' style='width:100%; max-width:800px;'>",""",
    """        "<div class='explanation'>",
        "<p>These charts aggregate the new Short-Before-Long metrics across WALS language families. ",
        "Because these metrics are geometric mean ratios, we plot their Natural Logarithm ($\\ln$). This centers neutral effects at 0, making compliant effects positive (Green) and anti-compliant effects negative (Red). ",
        "Families with at least 3 analyzed languages are included.</p>",
        "</div>",
        
        "<h3>Right Outer Constituent Ratio Effect</h3>",
        "<img src='summary_family_r_outer.svg' alt='Right Outer Summary' style='width:100%; max-width:800px;'>",
        
        "<h3>Left Outer Constituent Ratio Effect</h3>",
        "<img src='summary_family_l_outer.svg' alt='Left Outer Summary' style='width:100%; max-width:800px;'>",
        
        "<h3>Horizontal Right-Left Effect</h3>",
        "<img src='summary_family_horiz.svg' alt='Horizontal Effect Summary' style='width:100%; max-width:800px;'>","""
)

# Update chart color logic
code = code.replace(
    "colors = ['#4CAF50' if v > 0.1 else ('#f39c12' if v >= 0 else '#e74c3c') for v in values]",
    "colors = ['#4CAF50' if v > 0.05 else ('#f39c12' if v >= -0.05 else '#e74c3c') for v in values]"
)

with open('sbl_page_summary.py', 'w') as f:
    f.write(code)
