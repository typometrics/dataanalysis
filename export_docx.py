import pypandoc
import os
import sys

# Ensure we have the right paths
base_dir = '/bigstorage/kim/typometrics/dataanalysis'
input_file = os.path.join(base_dir, 'draft_section_MAL.md')
output_file = os.path.join(base_dir, 'draft_section_MAL.docx')

print(f"Converting {input_file} to {output_file}...")

try:
    # Check if pypandoc can find the binary
    print(f"Pandoc version: {pypandoc.get_pandoc_version()}")
    
    # Explicitly set resource path to base_dir so pandoc finds 'plots/...'
    # relative to base_dir
    extra_args = [
        f'--resource-path={base_dir}',
        '--verbose' # Try to get more info if it fails
    ]
    
    output = pypandoc.convert_file(
        input_file, 
        'docx', 
        outputfile=output_file,
        extra_args=extra_args
    )
    print(f"Successfully created {output_file}")
except Exception as e:
    print(f"Error converting file: {e}")
    # Print stderr if available in exception
    sys.exit(1)
