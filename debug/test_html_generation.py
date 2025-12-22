"""
Test HTML generation from mock configuration examples.
"""
import os
import pickle
import tempfile
from generate_html_examples import generate_all_html

# Create mock data for testing
print("Creating mock data...")
mock_examples = {
    'ab': {
        'V X': [
            {
                'tree': {
                    'forms': ['говорит', 'он'],
                    'upos': ['VERB', 'PRON'],
                    'heads': [0, 1],
                    'deprels': ['root', 'nsubj']
                },
                'verb_id': 1,
                'dep_ids': [2]
            }
        ],
        'X X V': [
            {
                'tree': {
                    'forms': ['он', 'книгу', 'читает'],
                    'upos': ['PRON', 'NOUN', 'VERB'],
                    'heads': [3, 3, 0],
                    'deprels': ['nsubj', 'obj', 'root']
                },
                'verb_id': 3,
                'dep_ids': [1, 2]
            }
        ]
    },
    'en': {
        'V X': [
            {
                'tree': {
                    'forms': ['reads', 'book'],
                    'upos': ['VERB', 'NOUN'],
                    'heads': [0, 1],
                    'deprels': ['root', 'obj']
                },
                'verb_id': 1,
                'dep_ids': [2]
            }
        ]
    }
}

mock_metadata = {
    'langNames': {
        'ab': 'Abkhaz',
        'en': 'English'
    }
}

# Create temporary data directory
with tempfile.TemporaryDirectory() as tmpdir:
    data_dir = os.path.join(tmpdir, 'data')
    os.makedirs(data_dir)
    
    # Save mock data
    with open(os.path.join(data_dir, 'all_config_examples.pkl'), 'wb') as f:
        pickle.dump(mock_examples, f)
    
    with open(os.path.join(data_dir, 'metadata.pkl'), 'wb') as f:
        pickle.dump(mock_metadata, f)
    
    # Generate HTML
    output_dir = os.path.join(tmpdir, 'html_test')
    print(f"Generating HTML in {output_dir}...")
    generate_all_html(data_dir=data_dir, output_dir=output_dir)
    
    # Check outputs
    print("\nVerifying outputs...")
    assert os.path.exists(os.path.join(output_dir, 'index.html')), "index.html not created"
    assert os.path.exists(os.path.join(output_dir, 'Abkhaz_ab')), "Abkhaz folder not created"
    assert os.path.exists(os.path.join(output_dir, 'English_en')), "English folder not created"
    assert os.path.exists(os.path.join(output_dir, 'Abkhaz_ab', 'V_X.html')), "V_X.html not created"
    assert os.path.exists(os.path.join(output_dir, 'Abkhaz_ab', 'X_X_V.html')), "X_X_V.html not created"
    assert os.path.exists(os.path.join(output_dir, 'English_en', 'V_X.html')), "English V_X.html not created"
    
    # Check index content
    with open(os.path.join(output_dir, 'index.html'), 'r') as f:
        index_content = f.read()
        assert 'Abkhaz' in index_content
        assert 'English' in index_content
        assert 'V_X.html' in index_content
    
    # Check example HTML content
    with open(os.path.join(output_dir, 'Abkhaz_ab', 'V_X.html'), 'r') as f:
        html_content = f.read()
        assert 'reactive-dep-tree' in html_content
        assert 'говорит' in html_content  # Check Russian text preserved
    
    print("✅ All tests passed!")
    print(f"\nGenerated files in {output_dir}:")
    print(f"  - index.html")
    print(f"  - Abkhaz_ab/V_X.html")
    print(f"  - Abkhaz_ab/X_X_V.html")
    print(f"  - English_en/V_X.html")
    print("\nHTML generation module working correctly!")
