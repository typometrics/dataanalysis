import os
import shutil
import sbl_page_home
import sbl_page_laws
import sbl_page_compliance
import sbl_page_validation
import sbl_page_explorer
import sbl_page_visualizations
import sbl_page_typology
import sbl_page_summary
import sbl_page_significance
import sbl_page_outer_effects

def build_site():
    out_dir = "html_sbl_analyses"
    os.makedirs(out_dir, exist_ok=True)
    
    print(f"Building SBL HTML site in {out_dir}/...")
    
    sbl_page_home.generate(out_dir)
    print("  Generated index.html")
    
    sbl_page_laws.generate(out_dir)
    print("  Generated sbl_laws_explained.html")
    
    sbl_page_compliance.generate(out_dir)
    print("  Generated sbl_laws_compliance.html")
    
    sbl_page_validation.generate(out_dir)
    print("  Generated sbl_validation.html")
    
    sbl_page_explorer.generate(out_dir)
    print("  Generated sbl_explorer.html")
    
    sbl_page_significance.generate(out_dir)
    print("  Generated sbl_significance.html")
    
    sbl_page_visualizations.generate(out_dir)
    print("  Generated sbl_laws_visualizations.html")
    
    sbl_page_typology.generate(out_dir)
    print("  Generated sbl_typology.html")
    
    sbl_page_summary.generate(out_dir)
    print("  Generated sbl_summary.html")
    
    sbl_page_outer_effects.generate(out_dir)
    print("  Generated sbl_outer_effects.html")
    
    # Copy examples directory
    src_examples = os.path.join("html_analyses", "examples")
    dst_examples = os.path.join(out_dir, "examples")
    if os.path.exists(src_examples):
        print(f"  Copying {src_examples} to {dst_examples}...")
        if os.path.exists(dst_examples):
            shutil.rmtree(dst_examples)
        shutil.copytree(src_examples, dst_examples)
    else:
        print(f"  Warning: Examples source directory {src_examples} not found. Skipping examples copy.")
    
    print("Site build complete!")

if __name__ == '__main__':
    build_site()
