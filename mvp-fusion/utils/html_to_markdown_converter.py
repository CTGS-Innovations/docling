#!/usr/bin/env python3
"""
HTML to Markdown Converter
==========================

High-performance HTML-to-markdown conversion for URL processing pipeline.
Converts raw HTML content to clean, structured markdown suitable for document processing.
"""

import re
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import html


class HTMLToMarkdownConverter:
    """High-performance HTML to Markdown converter optimized for web content."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Configure conversion options
        self.preserve_links = self.config.get('preserve_links', True)
        self.preserve_images = self.config.get('preserve_images', False)  # Disable images for web content
        self.clean_whitespace = self.config.get('clean_whitespace', True)
        self.remove_scripts = self.config.get('remove_scripts', True)
        self.remove_styles = self.config.get('remove_styles', True)
        self.max_heading_level = self.config.get('max_heading_level', 6)
        
    def convert(self, html_content: str, base_url: str = None) -> str:
        """Convert HTML content to clean markdown.
        
        Args:
            html_content: Raw HTML content
            base_url: Base URL for resolving relative links
            
        Returns:
            Clean markdown content
        """
        if not html_content:
            return ""
            
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove unwanted elements
        if self.remove_scripts:
            for script in soup.find_all(['script', 'noscript']):
                script.decompose()
                
        if self.remove_styles:
            for style in soup.find_all(['style', 'link']):
                if style.name == 'link' and style.get('rel') == ['stylesheet']:
                    style.decompose()
                elif style.name == 'style':
                    style.decompose()
        
        # Remove other unwanted elements
        for element in soup.find_all(['nav', 'footer', 'header', 'aside']):
            element.decompose()
            
        # Convert to markdown
        markdown_content = self._convert_element(soup, base_url)
        
        # Clean up whitespace
        if self.clean_whitespace:
            markdown_content = self._clean_whitespace(markdown_content)
            
        return markdown_content
    
    def _convert_element(self, element, base_url: str = None) -> str:
        """Convert a BeautifulSoup element to markdown recursively."""
        if hasattr(element, 'name') and element.name:
            tag_name = element.name
            
            # Handle different HTML tags
            if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                level = min(int(tag_name[1]), self.max_heading_level)
                heading_text = self._get_text_content(element)
                return f"\n{'#' * level} {heading_text}\n\n"
                
            elif tag_name == 'p':
                paragraph_text = self._convert_children(element, base_url)
                return f"{paragraph_text.strip()}\n\n"
                
            elif tag_name in ['strong', 'b']:
                text_content = self._convert_children(element, base_url)
                return f" **{text_content}** "
                
            elif tag_name in ['em', 'i']:
                text_content = self._convert_children(element, base_url)
                return f" *{text_content}* "
                
            elif tag_name == 'a' and self.preserve_links:
                href = element.get('href', '')
                if href and base_url:
                    href = urljoin(base_url, href)
                text_content = self._convert_children(element, base_url)
                if href:
                    return f"[{text_content}]({href})"
                else:
                    return text_content
                    
            elif tag_name == 'img' and self.preserve_images:
                src = element.get('src', '')
                alt = element.get('alt', '')
                if src and base_url:
                    src = urljoin(base_url, src)
                if src:
                    return f"![{alt}]({src})"
                else:
                    return f"[Image: {alt}]" if alt else "[Image]"
                    
            elif tag_name in ['ul', 'ol']:
                items = []
                for i, li in enumerate(element.find_all('li', recursive=False)):
                    item_text = self._convert_children(li, base_url)
                    if tag_name == 'ul':
                        items.append(f"- {item_text}")
                    else:
                        items.append(f"{i+1}. {item_text}")
                return "\n" + "\n".join(items) + "\n\n"
                
            elif tag_name == 'blockquote':
                quote_text = self._convert_children(element, base_url)
                lines = quote_text.strip().split('\n')
                quoted_lines = [f"> {line}" for line in lines]
                return "\n" + "\n".join(quoted_lines) + "\n\n"
                
            elif tag_name == 'code':
                return f"`{element.get_text()}`"
                
            elif tag_name == 'pre':
                code_content = element.get_text()
                return f"\n```\n{code_content}\n```\n\n"
                
            elif tag_name in ['br']:
                return "\n"
                
            elif tag_name in ['hr']:
                return "\n---\n\n"
                
            elif tag_name in ['table']:
                return self._convert_table(element, base_url)
                
            else:
                # For other tags, just process children
                return self._convert_children(element, base_url)
        else:
            # Text node (NavigableString)
            text = str(element).strip()
            if text:  # Only return non-empty text
                # Decode HTML entities
                text = html.unescape(text)
                return text
            return ""
    
    def _convert_children(self, element, base_url: str = None) -> str:
        """Convert all children of an element."""
        result = ""
        if hasattr(element, 'children'):
            for child in element.children:
                result += self._convert_element(child, base_url)
        return result
    
    def _get_text_content(self, element) -> str:
        """Get clean text content from an element."""
        text = element.get_text()
        text = html.unescape(text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _convert_table(self, table_element, base_url: str = None) -> str:
        """Convert HTML table to markdown table."""
        rows = []
        
        # Process table rows
        for tr in table_element.find_all('tr'):
            cells = []
            for td in tr.find_all(['td', 'th']):
                cell_text = self._get_text_content(td)
                # Escape pipe characters in cells
                cell_text = cell_text.replace('|', '\\|')
                cells.append(cell_text)
            
            if cells:
                rows.append('| ' + ' | '.join(cells) + ' |')
        
        if not rows:
            return ""
            
        # Add header separator if first row contains th elements
        first_row_has_headers = table_element.find('tr') and table_element.find('tr').find('th')
        if first_row_has_headers and len(rows) > 0:
            header_row = rows[0]
            separator = '| ' + ' | '.join(['---'] * (header_row.count('|') - 1)) + ' |'
            rows.insert(1, separator)
        
        return "\n" + "\n".join(rows) + "\n\n"
    
    def _clean_whitespace(self, markdown_content: str) -> str:
        """Clean up excessive whitespace in markdown content."""
        # Remove excessive blank lines (more than 2 consecutive)
        markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)
        
        # Fix excessive spaces (more than 1 consecutive space)
        markdown_content = re.sub(r' {2,}', ' ', markdown_content)
        
        # Remove leading/trailing whitespace from lines
        lines = markdown_content.split('\n')
        cleaned_lines = [line.strip() for line in lines]
        markdown_content = '\n'.join(cleaned_lines)
        
        # Remove leading/trailing whitespace from entire content
        markdown_content = markdown_content.strip()
        
        # Ensure single newline at end
        if markdown_content and not markdown_content.endswith('\n'):
            markdown_content += '\n'
            
        return markdown_content


def convert_html_to_markdown(html_content: str, base_url: str = None, config: Dict[str, Any] = None) -> str:
    """Convenience function to convert HTML to markdown.
    
    Args:
        html_content: Raw HTML content
        base_url: Base URL for resolving relative links
        config: Conversion configuration options
        
    Returns:
        Clean markdown content
    """
    converter = HTMLToMarkdownConverter(config)
    return converter.convert(html_content, base_url)


if __name__ == "__main__":
    # Test the converter
    test_html = """
    <html>
    <head><title>Test Page</title></head>
    <body>
        <h1>Main Heading</h1>
        <p>This is a <strong>test</strong> paragraph with <em>italic</em> text.</p>
        <h2>Sub Heading</h2>
        <ul>
            <li>List item 1</li>
            <li>List item 2</li>
        </ul>
        <a href="https://example.com">External link</a>
        <blockquote>This is a quote</blockquote>
    </body>
    </html>
    """
    
    converter = HTMLToMarkdownConverter()
    markdown = converter.convert(test_html, "https://example.com")
    print(markdown)