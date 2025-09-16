#!/usr/bin/env python3
"""
LaTeXit Decoder - Extract LaTeX code from base64-encoded latexit tags
"""

import base64
import re
import sys
from pathlib import Path

def decode_latexit_tag(latexit_content):
    """
    Decode a base64-encoded latexit tag to extract LaTeX code.
    
    Args:
        latexit_content: The base64 content from <latexit sha1_base64="...">content</latexit>
    
    Returns:
        Decoded LaTeX string or None if decoding fails
    """
    try:
        # Remove any whitespace and newlines
        clean_content = ''.join(latexit_content.split())
        
        # Decode from base64
        decoded_bytes = base64.b64decode(clean_content)
        
        # Try to decode as UTF-8 text
        latex_code = decoded_bytes.decode('utf-8', errors='ignore')
        
        return latex_code
    except Exception as e:
        print(f"Error decoding latexit: {e}")
        return None

def extract_latexit_tags(content):
    """Extract all latexit tags from content."""
    # Pattern to match <latexit sha1_base64="...">content</latexit>
    pattern = r'<latexit[^>]*?>(.*?)</latexit>'
    matches = re.findall(pattern, content, re.DOTALL)
    return matches

def process_markdown_file(file_path):
    """Process a markdown file and extract/decode all latexit tags."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        latexit_tags = extract_latexit_tags(content)
        
        if not latexit_tags:
            print(f"No latexit tags found in {file_path}")
            return
        
        print(f"\n🔍 Found {len(latexit_tags)} latexit tags in {file_path}")
        print("=" * 60)
        
        for i, tag_content in enumerate(latexit_tags, 1):
            print(f"\n📐 Formula #{i}:")
            print("-" * 40)
            
            # Show first few characters of encoded content
            preview = ''.join(tag_content.split())[:50]
            print(f"Encoded (preview): {preview}...")
            
            # Try to decode
            latex_code = decode_latexit_tag(tag_content)
            
            if latex_code:
                # Clean up the LaTeX code
                latex_clean = latex_code.strip()
                if latex_clean:
                    print(f"Decoded LaTeX: {latex_clean}")
                else:
                    print("Decoded but empty LaTeX content")
            else:
                print("Failed to decode LaTeX content")
            
            print("-" * 40)
    
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")

def create_html_with_decoded_formulas(file_path, output_path):
    """Create an HTML file with the decoded formulas from a markdown file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        latexit_tags = extract_latexit_tags(content)
        decoded_formulas = []
        
        for tag_content in latexit_tags:
            latex_code = decode_latexit_tag(tag_content)
            if latex_code and latex_code.strip():
                decoded_formulas.append(latex_code.strip())
        
        if not decoded_formulas:
            print("No decodable formulas found")
            return
        
        # Create HTML content
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Decoded LaTeX Formulas from {Path(file_path).name}</title>
    
    <script>
        MathJax = {{
            tex: {{
                inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
                displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
                processEscapes: true,
                processEnvironments: true
            }},
            options: {{
                skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre']
            }}
        }};
    </script>
    
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    
    <style>
        body {{
            font-family: 'Times New Roman', serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }}
        
        .formula-container {{
            margin: 20px 0;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 8px;
            background-color: #f9f9f9;
        }}
        
        .formula-number {{
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        
        .formula-display {{
            text-align: center;
            margin: 15px 0;
            padding: 10px;
            background-color: white;
            border-radius: 4px;
        }}
        
        .latex-code {{
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            color: #666;
            background-color: #f5f5f5;
            padding: 8px;
            border-radius: 3px;
            margin-top: 10px;
            word-break: break-all;
        }}
        
        h1 {{
            text-align: center;
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
    </style>
</head>
<body>
    <h1>Decoded LaTeX Formulas</h1>
    <p style="text-align: center; font-style: italic; color: #666;">
        Extracted from: {Path(file_path).name} | Found {len(decoded_formulas)} formulas
    </p>
"""
        
        for i, formula in enumerate(decoded_formulas, 1):
            html_content += f"""
    <div class="formula-container">
        <div class="formula-number">Formula #{i}</div>
        <div class="formula-display">
            $${formula}$$
        </div>
        <div class="latex-code">
            LaTeX: {formula}
        </div>
    </div>
"""
        
        html_content += """
    <script>
        window.addEventListener('load', function() {
            setTimeout(function() {
                if (window.MathJax) {
                    MathJax.typesetPromise();
                }
            }, 100);
        });
    </script>
</body>
</html>
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Created HTML file with {len(decoded_formulas)} decoded formulas: {output_path}")
        
    except Exception as e:
        print(f"Error creating HTML file: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python latexit_decoder.py <markdown_file> [output_html]")
        print("Example: python latexit_decoder.py Complex1.md decoded_formulas.html")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    if not Path(input_file).exists():
        print(f"Error: File {input_file} does not exist")
        sys.exit(1)
    
    # Process and display decoded formulas
    process_markdown_file(input_file)
    
    # Create HTML file if output path specified
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
        create_html_with_decoded_formulas(input_file, output_file)
    else:
        # Create default output file
        input_path = Path(input_file)
        output_file = input_path.parent / f"{input_path.stem}_decoded_formulas.html"
        create_html_with_decoded_formulas(input_file, str(output_file))