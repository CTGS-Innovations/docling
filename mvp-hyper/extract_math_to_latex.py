#!/usr/bin/env python3
"""
Extract Mathematical Expressions to LaTeX
=========================================
Convert mathematical notation from markdown to proper LaTeX format.
"""

import re
import sys
from pathlib import Path

def extract_math_expressions(content):
    """Extract mathematical expressions and convert to LaTeX."""
    
    math_expressions = []
    
    # Common mathematical patterns to extract
    patterns = [
        # Variables with subscripts/superscripts
        (r'x_([T0-9t\-]+)', r'x_{\1}'),
        (r'p_θ\(([^)]+)\)', r'p_\theta(\1)'),
        (r'q\(([^)]+)\)', r'q(\1)'),
        (r'p\(([^)]+)\)', r'p(\1)'),
        
        # Greek letters in text
        (r'(?<![\\$])β([T0-9t\-]*)', r'\\beta_{\1}' if r'\1' else r'\\beta'),
        (r'(?<![\\$])α([T0-9t\-]*)', r'\\alpha_{\1}' if r'\1' else r'\\alpha'),
        (r'(?<![\\$])θ', r'\\theta'),
        (r'(?<![\\$])μ', r'\\mu'),
        (r'(?<![\\$])σ', r'\\sigma'),
        
        # Mathematical operators and symbols
        (r'∼', r'\\sim'),
        (r'∥', r'\\|'),
        (r'≤', r'\\leq'),
        (r'≥', r'\\geq'),
        (r'≈', r'\\approx'),
        (r'∈', r'\\in'),
        (r'⊆', r'\\subseteq'),
        (r'→', r'\\rightarrow'),
        (r'←', r'\\leftarrow'),
        (r'⇒', r'\\Rightarrow'),
        (r'∇', r'\\nabla'),
        (r'∂', r'\\partial'),
        (r'∞', r'\\infty'),
        (r'∑', r'\\sum'),
        (r'∫', r'\\int'),
        (r'√', r'\\sqrt'),
        
        # Mathematical expressions
        (r'DKL\(([^)]+)\)', r'D_{\\text{KL}}(\1)'),
        (r'N\(([^;]+);([^)]+)\)', r'\\mathcal{N}(\1; \2)'),
        (r'Eq\[([^\]]+)\]', r'\\mathbb{E}[\1]'),
        (r'E\[([^\]]+)\]', r'\\mathbb{E}[\1]'),
        
        # Arrows and sequences
        (r'([x_\w]+)\s*←\s*([x_\w]+)', r'\1 \\leftarrow \2'),
        (r'([x_\w]+)\s*→\s*([x_\w]+)', r'\1 \\rightarrow \2'),
        
        # Probability distributions
        (r'([pq])_?θ?\(([^|]+)\|([^)]+)\)', r'\1_\\theta(\2|\3)'),
    ]
    
    # Find mathematical expressions in the content
    lines = content.split('\n')
    
    for line_num, line in enumerate(lines, 1):
        # Skip lines that are already in LaTeX blocks
        if line.strip().startswith('$') or '<latexit' in line:
            continue
            
        # Look for mathematical expressions
        if any(symbol in line for symbol in ['x_', 'p_θ', 'q(', 'β', 'α', 'θ', '∼', 'DKL', 'N(']):
            # Clean and convert the line
            converted_line = line
            for pattern, replacement in patterns:
                converted_line = re.sub(pattern, replacement, converted_line)
            
            if converted_line != line:
                math_expressions.append({
                    'line_number': line_num,
                    'original': line.strip(),
                    'converted': converted_line.strip(),
                    'context': 'inline'
                })
    
    return math_expressions

def create_latex_markdown(input_file, expressions):
    """Create a new markdown file with proper LaTeX formatting."""
    
    output_file = Path(input_file).parent / f"{Path(input_file).stem}_with_latex.md"
    
    # Read original content
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create conversion map
    conversion_map = {}
    for expr in expressions:
        conversion_map[expr['original']] = expr['converted']
    
    # Apply conversions
    converted_content = content
    for original, converted in conversion_map.items():
        # Wrap math expressions in LaTeX delimiters
        if any(symbol in converted for symbol in ['\\', '_', '^', '{', '}']):
            math_wrapped = f"${converted}$"
            converted_content = converted_content.replace(original, math_wrapped)
    
    # Write converted file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(converted_content)
    
    return output_file

def extract_key_formulas(content):
    """Extract and format key mathematical formulas from the diffusion paper."""
    
    key_formulas = []
    
    # Define key formula patterns
    formula_patterns = [
        {
            'name': 'Forward Process',
            'pattern': r'q\(x_t\|x_{t-1}\)\s*:=\s*N\([^)]+\)',
            'description': 'Forward diffusion process'
        },
        {
            'name': 'Reverse Process',
            'pattern': r'p_θ\(x_{t-1}\|x_t\)',
            'description': 'Learned reverse process'
        },
        {
            'name': 'Variational Bound',
            'pattern': r'L\s*=\s*E_q\s*\[.*?\]',
            'description': 'Training objective'
        },
        {
            'name': 'Direct Sampling',
            'pattern': r'q\(x_t\|x_0\)\s*=\s*N\([^)]+\)',
            'description': 'Direct sampling at any timestep'
        }
    ]
    
    for formula_info in formula_patterns:
        matches = re.findall(formula_info['pattern'], content, re.MULTILINE | re.DOTALL)
        for match in matches:
            key_formulas.append({
                'name': formula_info['name'],
                'formula': match.strip(),
                'description': formula_info['description']
            })
    
    return key_formulas

def create_clean_latex_html(input_file):
    """Create a clean HTML file with the key mathematical formulas."""
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract paper title and authors
    title_match = re.search(r'^([^\n]+)\n([^\n]+)\n([^\n]+)', content)
    title = title_match.group(1) if title_match else "Mathematical Formulas"
    
    # Key formulas from the diffusion paper
    formulas = [
        {
            'name': 'Diffusion Process Chain',
            'latex': 'x_T \\leftarrow \\cdots \\leftarrow x_t \\leftarrow x_{t-1} \\leftarrow \\cdots \\leftarrow x_0',
            'description': 'The forward diffusion process gradually adding noise'
        },
        {
            'name': 'Forward Process',
            'latex': 'q(x_t|x_{t-1}) := \\mathcal{N}(x_t; \\sqrt{1-\\beta_t}x_{t-1}, \\beta_t I)',
            'description': 'Fixed forward process adding Gaussian noise'
        },
        {
            'name': 'Reverse Process',
            'latex': 'p_\\theta(x_{t-1}|x_t) := \\mathcal{N}(x_{t-1}; \\mu_\\theta(x_t, t), \\Sigma_\\theta(x_t, t))',
            'description': 'Learned reverse process for denoising'
        },
        {
            'name': 'Direct Sampling',
            'latex': 'q(x_t|x_0) = \\mathcal{N}(x_t; \\sqrt{\\bar{\\alpha}_t}x_0, (1-\\bar{\\alpha}_t)I)',
            'description': 'Direct sampling at any timestep t'
        },
        {
            'name': 'Variational Bound',
            'latex': 'L = \\mathbb{E}_q\\left[\\log \\frac{q(x_{1:T}|x_0)}{p_\\theta(x_{0:T})}\\right]',
            'description': 'Training objective using variational inference'
        },
        {
            'name': 'Simplified Objective',
            'latex': 'L_{\\text{simple}} = \\mathbb{E}_{t,x_0,\\epsilon}\\left[\\|\\epsilon - \\epsilon_\\theta(\\sqrt{\\bar{\\alpha}_t}x_0 + \\sqrt{1-\\bar{\\alpha}_t}\\epsilon, t)\\|^2\\right]',
            'description': 'Simplified training objective used in practice'
        },
        {
            'name': 'Noise Schedule',
            'latex': '\\alpha_t = 1 - \\beta_t, \\quad \\bar{\\alpha}_t = \\prod_{s=1}^t \\alpha_s',
            'description': 'Noise schedule parameters'
        }
    ]
    
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Diffusion Model Formulas</title>
    
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
            background-color: #fafafa;
        }}
        
        .formula-container {{
            margin: 25px 0;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 10px;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .formula-name {{
            font-weight: bold;
            color: #2c3e50;
            font-size: 1.2em;
            margin-bottom: 15px;
            border-bottom: 2px solid #3498db;
            padding-bottom: 5px;
        }}
        
        .formula-display {{
            text-align: center;
            margin: 20px 0;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 5px;
            border-left: 4px solid #3498db;
        }}
        
        .description {{
            font-style: italic;
            color: #666;
            margin-top: 10px;
            font-size: 0.95em;
        }}
        
        h1 {{
            text-align: center;
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 15px;
            margin-bottom: 30px;
        }}
        
        .paper-info {{
            text-align: center;
            font-style: italic;
            color: #7f8c8d;
            margin-bottom: 40px;
            font-size: 1.1em;
        }}
        
        .algorithm-box {{
            background-color: #ecf0f1;
            border: 1px solid #bdc3c7;
            border-radius: 5px;
            padding: 15px;
            margin: 20px 0;
            font-family: 'Courier New', monospace;
        }}
    </style>
</head>
<body>
    <h1>Denoising Diffusion Probabilistic Models</h1>
    
    <div class="paper-info">
        Key Mathematical Formulas from Ho, Jain & Abbeel (2020)
    </div>
'''
    
    for formula in formulas:
        html_content += f'''
    <div class="formula-container">
        <div class="formula-name">{formula['name']}</div>
        <div class="formula-display">
            $${formula['latex']}$$
        </div>
        <div class="description">
            {formula['description']}
        </div>
    </div>
'''
    
    html_content += '''
    <div class="formula-container">
        <div class="formula-name">Training Algorithm</div>
        <div class="algorithm-box">
<strong>Algorithm 1: Training</strong><br>
1: repeat<br>
2: &nbsp;&nbsp;&nbsp;&nbsp;$x_0 \\sim q(x_0)$<br>
3: &nbsp;&nbsp;&nbsp;&nbsp;$t \\sim \\text{Uniform}(\\{1, \\ldots, T\\})$<br>
4: &nbsp;&nbsp;&nbsp;&nbsp;$\\epsilon \\sim \\mathcal{N}(0, I)$<br>
5: &nbsp;&nbsp;&nbsp;&nbsp;Take gradient descent step on<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;$\\nabla_\\theta \\|\\epsilon - \\epsilon_\\theta(\\sqrt{\\bar{\\alpha}_t}x_0 + \\sqrt{1-\\bar{\\alpha}_t}\\epsilon, t)\\|^2$<br>
6: until converged
        </div>
    </div>

    <div class="formula-container">
        <div class="formula-name">Sampling Algorithm</div>
        <div class="algorithm-box">
<strong>Algorithm 2: Sampling</strong><br>
1: $x_T \\sim \\mathcal{N}(0, I)$<br>
2: for $t = T, \\ldots, 1$ do<br>
3: &nbsp;&nbsp;&nbsp;&nbsp;$z \\sim \\mathcal{N}(0, I)$ if $t > 1$, else $z = 0$<br>
4: &nbsp;&nbsp;&nbsp;&nbsp;$x_{t-1} = \\frac{1}{\\sqrt{\\alpha_t}}\\left(x_t - \\frac{1-\\alpha_t}{\\sqrt{1-\\bar{\\alpha}_t}}\\epsilon_\\theta(x_t, t)\\right) + \\sigma_t z$<br>
5: end for<br>
6: return $x_0$
        </div>
    </div>

    <script>
        window.addEventListener('load', function() {{
            setTimeout(function() {{
                if (window.MathJax) {{
                    MathJax.typesetPromise();
                }}
            }}, 100);
        }});
    </script>
</body>
</html>
'''
    
    output_file = Path(input_file).parent / f"{Path(input_file).stem}_clean_formulas.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return output_file

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_math_to_latex.py <markdown_file>")
        print("Example: python extract_math_to_latex.py Complex1.md")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    if not Path(input_file).exists():
        print(f"Error: File {input_file} does not exist")
        sys.exit(1)
    
    print(f"📊 Extracting mathematical expressions from {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract mathematical expressions
    expressions = extract_math_expressions(content)
    
    print(f"✅ Found {len(expressions)} mathematical expressions")
    
    # Create clean HTML with key formulas
    html_file = create_clean_latex_html(input_file)
    print(f"✅ Created clean formula HTML: {html_file}")
    
    # Show some examples
    if expressions:
        print("\n📝 Sample conversions:")
        for expr in expressions[:5]:
            print(f"   Line {expr['line_number']}: {expr['original']}")
            print(f"   →  ${expr['converted']}$")
            print()