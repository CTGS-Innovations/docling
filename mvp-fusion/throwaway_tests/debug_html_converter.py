#!/usr/bin/env python3
"""
Debug HTML-to-Markdown converter
"""

from bs4 import BeautifulSoup

def debug_html_structure():
    """Debug BeautifulSoup parsing"""
    simple_html = '<p>This is a <strong>test</strong> paragraph.</p>'
    soup = BeautifulSoup(simple_html, 'html.parser')
    
    print("HTML structure:")
    print(simple_html)
    print()
    
    print("BeautifulSoup parsing:")
    p_tag = soup.find('p')
    print(f"P tag: {p_tag}")
    print(f"P tag children: {list(p_tag.children)}")
    print()
    
    print("Iterating through children:")
    for i, child in enumerate(p_tag.children):
        print(f"  Child {i}: {repr(child)} (type: {type(child)})")
        if hasattr(child, 'name'):
            print(f"    Has name: {child.name}")
        if hasattr(child, 'children'):
            print(f"    Has children: {list(child.children)}")
        print()

if __name__ == "__main__":
    debug_html_structure()