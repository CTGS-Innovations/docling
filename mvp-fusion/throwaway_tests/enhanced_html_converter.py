#!/usr/bin/env python3
"""
Enhanced HTML to Markdown Converter - THROWAWAY TEST
====================================================

GOAL: Test improved HTML-to-markdown conversion for better semantic extraction
REASON: Current converter preserves too much website chrome and URL artifacts
PROBLEM: Navigation, forms, encoded URLs interfere with entity extraction

This is a throwaway test to demonstrate improvement potential.
"""

import re
from typing import Dict, Any, Optional, Set
from bs4 import BeautifulSoup, Comment
from urllib.parse import urljoin, urlparse, parse_qs
import html


class EnhancedHTMLToMarkdownConverter:
    """Enhanced HTML to Markdown converter optimized for semantic content extraction."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Enhanced configuration options
        self.preserve_links = self.config.get('preserve_links', True)
        self.preserve_images = self.config.get('preserve_images', False)
        self.clean_whitespace = self.config.get('clean_whitespace', True)
        self.aggressive_chrome_removal = self.config.get('aggressive_chrome_removal', True)
        self.clean_urls = self.config.get('clean_urls', True)
        self.max_heading_level = self.config.get('max_heading_level', 6)
        
        # Content area detection selectors (prioritized)
        self.content_selectors = [
            'main', 'article', '[role="main"]', '.main-content', '.content',
            '.post-content', '.entry-content', '.article-content', '#content',
            '.page-content', '.container', '.wrapper'
        ]
        
        # Elements to aggressively remove (website chrome)
        self.chrome_selectors = [
            'nav', 'header', 'footer', 'aside', '.navigation', '.nav',
            '.header', '.footer', '.sidebar', '.menu', '.breadcrumb',
            '.cookie-banner', '.cookie-notice', '.popup', '.modal',
            '.advertisement', '.ad', '.ads', '.social-share', '.share',
            '.comments', '.comment-section', '.related-posts', '.tags',
            '.categories', '.author-bio', '.subscription', '.newsletter',
            'form', '.contact-form', '.search-form', '.login-form',
            '.cta', '.call-to-action', '.banner', '.hero-banner'
        ]
        
        # URL parameters to remove (tracking, analytics, etc.)
        self.url_params_to_remove = {
            'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
            'fbclid', 'gclid', 'msclkid', '_ga', '_gid', 'ref', 'source',
            'elementor-action', 'settings', 'toggle', 'action', 'popup'
        }

    def convert(self, html_content: str, base_url: str = None) -> str:
        """Convert HTML content to clean, semantic markdown.
        
        Args:
            html_content: Raw HTML content
            base_url: Base URL for resolving relative links
            
        Returns:
            Clean markdown content optimized for semantic extraction
        """
        if not html_content:
            return ""
            
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Phase 1: Aggressive chrome removal
        if self.aggressive_chrome_removal:
            self._remove_website_chrome(soup)
        
        # Phase 2: Content area detection and isolation
        main_content = self._extract_main_content(soup)
        if main_content:
            soup = main_content
        
        # Phase 3: Standard element removal
        self._remove_unwanted_elements(soup)
        
        # Phase 4: Convert to markdown
        markdown_content = self._convert_element(soup, base_url)
        
        # Phase 5: Post-processing cleanup
        if self.clean_whitespace:
            markdown_content = self._clean_whitespace(markdown_content)
            
        if self.clean_urls:
            markdown_content = self._clean_url_artifacts(markdown_content)
            
        return markdown_content
    
    def _remove_website_chrome(self, soup: BeautifulSoup) -> None:
        """Aggressively remove website chrome elements."""
        # Remove by selector
        for selector in self.chrome_selectors:
            try:
                for element in soup.select(selector):
                    element.decompose()
            except Exception:
                # Invalid selector, skip
                continue
        
        # Remove comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        # Remove script and style tags
        for element in soup.find_all(['script', 'noscript', 'style', 'link']):
            if element.name == 'link' and element.get('rel') == ['stylesheet']:
                element.decompose()
            elif element.name in ['script', 'noscript', 'style']:
                element.decompose()
        
        # Remove elements with common tracking/analytics attributes
        tracking_attrs = ['data-track', 'data-analytics', 'onclick', 'onload']
        for attr in tracking_attrs:
            for element in soup.find_all(attrs={attr: True}):
                element.decompose()
    
    def _extract_main_content(self, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """Try to extract the main content area from the page."""
        # Try each content selector in order of priority
        for selector in self.content_selectors:
            try:
                content_elements = soup.select(selector)
                if content_elements:
                    # Return the first (and likely main) content area
                    main_content = content_elements[0]
                    # Create a new soup with just this content
                    new_soup = BeautifulSoup('', 'html.parser')
                    new_soup.append(main_content.extract())
                    return new_soup
            except Exception:
                continue
        
        return None  # No specific content area found, use full soup
    
    def _remove_unwanted_elements(self, soup: BeautifulSoup) -> None:
        """Remove additional unwanted elements."""
        # Remove elements with display:none or visibility:hidden
        for element in soup.find_all(style=re.compile(r'display:\s*none|visibility:\s*hidden')):
            element.decompose()
        
        # Remove empty elements that might create noise
        for tag_name in ['div', 'span', 'p']:
            for element in soup.find_all(tag_name):
                if not element.get_text(strip=True) and not element.find_all(['img', 'video', 'audio']):
                    element.decompose()
    
    def _clean_url_artifacts(self, markdown_content: str) -> str:
        """Clean URL artifacts that interfere with entity extraction."""
        # Remove encoded URL parameters that appear in text
        url_artifact_patterns = [
            r'%3[A-F0-9]%[A-F0-9]{2}%[A-F0-9]{2}',  # Encoded parameters
            r'&[a-z]+;',  # HTML entities
            r'#elementor-action[^\s]*',  # Elementor tracking
            r'utm_[a-z]+=[^\s&]*',  # UTM parameters
            r'fbclid=[^\s&]*',  # Facebook click IDs
            r'gclid=[^\s&]*',  # Google click IDs
        ]
        
        for pattern in url_artifact_patterns:
            markdown_content = re.sub(pattern, '', markdown_content, flags=re.IGNORECASE)
        
        return markdown_content
    
    def _clean_url(self, url: str) -> str:
        """Clean tracking parameters from URLs."""
        if not url or not self.clean_urls:
            return url
            
        try:
            parsed = urlparse(url)
            if parsed.query:
                # Parse query parameters
                params = parse_qs(parsed.query)
                # Remove tracking parameters
                clean_params = {k: v for k, v in params.items() 
                              if k.lower() not in self.url_params_to_remove}
                
                # Rebuild URL without tracking params
                if clean_params:
                    from urllib.parse import urlencode, urlunparse
                    clean_query = urlencode(clean_params, doseq=True)
                    clean_url = urlunparse((
                        parsed.scheme, parsed.netloc, parsed.path,
                        parsed.params, clean_query, ''  # Remove fragment too
                    ))
                else:
                    clean_url = urlunparse((
                        parsed.scheme, parsed.netloc, parsed.path,
                        parsed.params, '', ''
                    ))
                return clean_url
            else:
                # Remove fragment if present
                return urlunparse((
                    parsed.scheme, parsed.netloc, parsed.path,
                    parsed.params, parsed.query, ''
                ))
        except Exception:
            return url
    
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
                if paragraph_text.strip():  # Only return non-empty paragraphs
                    return f"{paragraph_text.strip()}\n\n"
                return ""
                
            elif tag_name in ['strong', 'b']:
                text_content = self._convert_children(element, base_url)
                if text_content.strip():
                    return f"**{text_content.strip()}**"
                return ""
                
            elif tag_name in ['em', 'i']:
                text_content = self._convert_children(element, base_url)
                if text_content.strip():
                    return f"*{text_content.strip()}*"
                return ""
                
            elif tag_name == 'a' and self.preserve_links:
                href = element.get('href', '')
                if href and base_url:
                    href = urljoin(base_url, href)
                # Clean the URL
                href = self._clean_url(href)
                text_content = self._convert_children(element, base_url)
                if href and text_content.strip():
                    return f"[{text_content.strip()}]({href})"
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
                    return f"[Image: {alt}]" if alt else ""
                    
            elif tag_name in ['ul', 'ol']:
                items = []
                for i, li in enumerate(element.find_all('li', recursive=False)):
                    item_text = self._convert_children(li, base_url).strip()
                    if item_text:  # Only add non-empty items
                        if tag_name == 'ul':
                            items.append(f"- {item_text}")
                        else:
                            items.append(f"{i+1}. {item_text}")
                if items:
                    return "\n" + "\n".join(items) + "\n\n"
                return ""
                
            elif tag_name == 'blockquote':
                quote_text = self._convert_children(element, base_url).strip()
                if quote_text:
                    lines = quote_text.split('\n')
                    quoted_lines = [f"> {line}" for line in lines if line.strip()]
                    return "\n" + "\n".join(quoted_lines) + "\n\n"
                return ""
                
            elif tag_name == 'code':
                code_text = element.get_text()
                if code_text.strip():
                    return f"`{code_text.strip()}`"
                return ""
                
            elif tag_name == 'pre':
                code_content = element.get_text()
                if code_content.strip():
                    return f"\n```\n{code_content.strip()}\n```\n\n"
                return ""
                
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
                # Clean up excessive whitespace
                text = re.sub(r'\s+', ' ', text)
                return text
            return ""
    
    def _convert_children(self, element, base_url: str = None) -> str:
        """Convert all children of an element."""
        result = ""
        if hasattr(element, 'children'):
            for child in element.children:
                child_result = self._convert_element(child, base_url)
                if child_result:  # Only add non-empty results
                    result += child_result
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
            
            if cells and any(cell.strip() for cell in cells):  # Only add rows with content
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
        cleaned_lines = []
        for line in lines:
            cleaned_line = line.strip()
            # Skip lines that are just whitespace or common website noise
            if cleaned_line and not self._is_noise_line(cleaned_line):
                cleaned_lines.append(cleaned_line)
        
        markdown_content = '\n'.join(cleaned_lines)
        
        # Remove leading/trailing whitespace from entire content
        markdown_content = markdown_content.strip()
        
        # Ensure single newline at end
        if markdown_content and not markdown_content.endswith('\n'):
            markdown_content += '\n'
            
        return markdown_content
    
    def _is_noise_line(self, line: str) -> bool:
        """Check if a line is website noise that should be removed."""
        noise_patterns = [
            r'^(skip to content|menu|navigation|search)$',
            r'^(home|about|contact|privacy|terms)$',
            r'^(facebook|twitter|linkedin|instagram)$',
            r'^(subscribe|newsletter|email)$',
            r'^(cookies?|privacy policy|terms of service)$',
            r'^(close|accept|decline|manage)$',
            r'^\s*[×✕✖]\s*$',  # Close buttons
            r'^\s*[▼▲►◄]\s*$',  # Arrow characters
        ]
        
        line_lower = line.lower().strip()
        for pattern in noise_patterns:
            if re.match(pattern, line_lower):
                return True
        
        return False


def convert_html_to_markdown_enhanced(html_content: str, base_url: str = None, config: Dict[str, Any] = None) -> str:
    """Enhanced convenience function to convert HTML to clean markdown.
    
    Args:
        html_content: Raw HTML content
        base_url: Base URL for resolving relative links
        config: Conversion configuration options
        
    Returns:
        Clean markdown content optimized for semantic extraction
    """
    # Default enhanced config
    enhanced_config = {
        'aggressive_chrome_removal': True,
        'clean_urls': True,
        'preserve_images': False,  # Disable for cleaner text extraction
        'preserve_links': True
    }
    
    if config:
        enhanced_config.update(config)
    
    converter = EnhancedHTMLToMarkdownConverter(enhanced_config)
    return converter.convert(html_content, base_url)


if __name__ == "__main__":
    # Test with CTGS-like content
    test_html = """
    <html>
    <head><title>Test Company</title></head>
    <body>
        <nav class="navigation">
            <a href="#content">Skip to content</a>
            <a href="/home">Home</a>
            <a href="/about">About</a>
        </nav>
        
        <header class="header">
            <h1>Company Logo</h1>
        </header>
        
        <main class="main-content">
            <h1>Crafting Bespoke Solutions</h1>
            <p>We provide <strong>innovative consulting</strong> services with <em>20 years</em> of experience.</p>
            
            <h2>Our Services</h2>
            <ul>
                <li>Strategic consulting for Fortune 500 companies</li>
                <li>Digital transformation with AI integration</li>
                <li>Process optimization and efficiency gains</li>
            </ul>
            
            <a href="https://example.com/contact?utm_source=website&utm_campaign=demo&elementor-action=popup">Contact Us</a>
        </main>
        
        <aside class="sidebar">
            <h3>Newsletter</h3>
            <form class="newsletter">
                <input type="email" placeholder="Subscribe">
                <button>Submit</button>
            </form>
        </aside>
        
        <footer class="footer">
            <p>© 2024 Company. Privacy Policy | Terms</p>
        </footer>
        
        <div class="cookie-banner">
            <p>We use cookies. <button>Accept</button> <button>Decline</button></p>
        </div>
    </body>
    </html>
    """
    
    print("=== ENHANCED CONVERTER TEST ===")
    converter = EnhancedHTMLToMarkdownConverter()
    markdown = converter.convert(test_html, "https://example.com")
    print(markdown)