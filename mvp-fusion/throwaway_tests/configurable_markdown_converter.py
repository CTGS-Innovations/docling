#!/usr/bin/env python3
"""
Configurable Markdown Converter - THROWAWAY TEST
================================================

GOAL: Create configurable HTML-to-markdown conversion system
REASON: Allow switching between converters via configuration
PROBLEM: Need flexible solution that can use different converters

This creates a factory pattern for markdown converters.
"""

from typing import Dict, Any
from abc import ABC, abstractmethod

# Import all available converters
try:
    import html2text
    HAS_HTML2TEXT = True
except ImportError:
    HAS_HTML2TEXT = False

try:
    from markdownify import markdownify
    HAS_MARKDOWNIFY = True
except ImportError:
    HAS_MARKDOWNIFY = False

# Import current converter
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.html_to_markdown_converter import HTMLToMarkdownConverter


class MarkdownConverterInterface(ABC):
    """Interface for all markdown converters."""
    
    @abstractmethod
    def convert(self, html_content: str, base_url: str = None) -> str:
        """Convert HTML to markdown."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Converter name."""
        pass


class BeautifulSoupConverter(MarkdownConverterInterface):
    """Current BeautifulSoup-based converter (existing implementation)."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.converter = HTMLToMarkdownConverter(config or {})
        self._name = "beautifulsoup"
    
    def convert(self, html_content: str, base_url: str = None) -> str:
        return self.converter.convert(html_content, base_url)
    
    @property
    def name(self) -> str:
        return self._name


class Html2TextConverter(MarkdownConverterInterface):
    """Fast html2text-based converter."""
    
    def __init__(self, config: Dict[str, Any] = None):
        if not HAS_HTML2TEXT:
            raise ImportError("html2text not installed. Run: pip install html2text")
        
        self.config = config or {}
        self._name = "html2text"
        
        # Configure html2text for optimal performance and quality
        self.h = html2text.HTML2Text()
        self.h.body_width = 0  # Don't wrap text
        self.h.ignore_emphasis = False
        self.h.ignore_links = False
        self.h.ignore_images = self.config.get('ignore_images', True)  # Default: ignore for cleaner text
        self.h.wrap_links = False  # Performance optimization
        self.h.unicode_snob = True  # Better Unicode handling
        self.h.escape_all = False  # Don't escape everything
        self.h.bypass_tables = False  # Convert tables to markdown
        
    def convert(self, html_content: str, base_url: str = None) -> str:
        if base_url:
            self.h.base_url = base_url
        return self.h.handle(html_content)
    
    @property
    def name(self) -> str:
        return self._name


class MarkdownifyConverter(MarkdownConverterInterface):
    """Markdownify-based converter."""
    
    def __init__(self, config: Dict[str, Any] = None):
        if not HAS_MARKDOWNIFY:
            raise ImportError("markdownify not installed. Run: pip install markdownify")
        
        self.config = config or {}
        self._name = "markdownify"
        
        # Configure markdownify options
        self.options = {
            'heading_style': 'ATX',  # Use # style headings
            'bullets': '*',  # Use * for lists
            'escape_asterisks': True,
            'escape_underscores': True,
            'wrap': False,  # Don't wrap text
            'strip': self.config.get('strip_tags', [])  # Optional tag stripping
        }
    
    def convert(self, html_content: str, base_url: str = None) -> str:
        return markdownify(html_content, **self.options)
    
    @property
    def name(self) -> str:
        return self._name


class ConfigurableMarkdownConverter:
    """Factory for creating markdown converters based on configuration."""
    
    AVAILABLE_CONVERTERS = {
        'beautifulsoup': BeautifulSoupConverter,
        'html2text': Html2TextConverter,
        'markdownify': MarkdownifyConverter
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Get converter type from config
        converter_type = self.config.get('markdown_converter', {}).get('type', 'html2text')
        converter_config = self.config.get('markdown_converter', {}).get('config', {})
        
        # Create the converter
        self.converter = self._create_converter(converter_type, converter_config)
    
    def _create_converter(self, converter_type: str, converter_config: Dict[str, Any]) -> MarkdownConverterInterface:
        """Create a converter instance."""
        if converter_type not in self.AVAILABLE_CONVERTERS:
            available = list(self.AVAILABLE_CONVERTERS.keys())
            raise ValueError(f"Unknown converter '{converter_type}'. Available: {available}")
        
        converter_class = self.AVAILABLE_CONVERTERS[converter_type]
        
        try:
            return converter_class(converter_config)
        except ImportError as e:
            # Fall back to BeautifulSoup if the preferred converter isn't available
            print(f"⚠️  {converter_type} not available ({e}), falling back to beautifulsoup")
            return BeautifulSoupConverter(converter_config)
    
    def convert(self, html_content: str, base_url: str = None) -> str:
        """Convert HTML to markdown using the configured converter."""
        return self.converter.convert(html_content, base_url)
    
    @property
    def name(self) -> str:
        """Get the active converter name."""
        return self.converter.name
    
    @classmethod
    def get_available_converters(cls) -> list:
        """Get list of available converter types."""
        available = []
        for name, converter_class in cls.AVAILABLE_CONVERTERS.items():
            try:
                # Try to instantiate to check if dependencies are available
                converter_class({})
                available.append(name)
            except ImportError:
                continue
        return available


def create_markdown_converter(config: Dict[str, Any] = None) -> ConfigurableMarkdownConverter:
    """Factory function to create a configured markdown converter."""
    return ConfigurableMarkdownConverter(config)


# Convenience function that maintains the existing API
def convert_html_to_markdown_configurable(html_content: str, base_url: str = None, config: Dict[str, Any] = None) -> str:
    """Convert HTML to markdown using configurable converter.
    
    This function maintains the same API as the original convert_html_to_markdown
    but uses the configurable system underneath.
    """
    converter = create_markdown_converter(config)
    return converter.convert(html_content, base_url)


if __name__ == "__main__":
    # Test the configurable system
    print("🧪 Testing Configurable Markdown Converter")
    print("=" * 50)
    
    # Test HTML
    test_html = """
    <html>
    <head><title>Test</title></head>
    <body>
        <h1>Test Document</h1>
        <p>This is a <strong>test</strong> with a <a href="https://example.com">link</a>.</p>
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
        </ul>
    </body>
    </html>
    """
    
    # Show available converters
    available = ConfigurableMarkdownConverter.get_available_converters()
    print(f"Available converters: {available}")
    print()
    
    # Test each available converter
    for converter_type in available:
        print(f"Testing {converter_type}:")
        print("-" * 30)
        
        config = {
            'markdown_converter': {
                'type': converter_type,
                'config': {}
            }
        }
        
        try:
            converter = create_markdown_converter(config)
            result = converter.convert(test_html, "https://example.com")
            print(f"Active converter: {converter.name}")
            print(f"Output ({len(result)} chars):")
            print(result[:200] + "..." if len(result) > 200 else result)
            print()
        except Exception as e:
            print(f"Error: {e}")
            print()