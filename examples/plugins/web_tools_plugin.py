"""Web Tools Plugin - Example plugin providing web-related functionality."""

import re
from typing import Dict, Any, List
from urllib.parse import urlparse

from tomo import BaseTool, tool
from tomo.plugins import BasePlugin, PluginType, plugin


@plugin(PluginType.TOOL, "web_tools", "1.0.0")
class WebToolsPlugin(BasePlugin):
    """Plugin providing web-related tools."""
    
    @property
    def plugin_type(self) -> PluginType:
        return PluginType.TOOL
    
    @property
    def name(self) -> str:
        return "web_tools"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Web utilities including URL validation, domain extraction, and HTML cleaning"
    
    @property
    def author(self) -> str:
        return "Tomo Community"
    
    @property
    def dependencies(self) -> List[str]:
        return []  # No external dependencies for this basic example
    
    def initialize(self, config: Dict[str, Any] = None) -> None:
        """Initialize the web tools plugin."""
        self.config = config or {}
        print(f"🌐 Initializing {self.name} plugin v{self.version}")
        
        # Set default configuration
        self.max_url_length = self.config.get("max_url_length", 2048)
        self.allowed_schemes = self.config.get("allowed_schemes", ["http", "https"])
    
    def register_components(self, registry) -> None:
        """Register web tools with the registry."""
        registry.tool_registry.register(URLValidator)
        registry.tool_registry.register(DomainExtractor)
        registry.tool_registry.register(HTMLCleaner)
        registry.tool_registry.register(EmailExtractor)


@tool
class URLValidator(BaseTool):
    """Validate if a string is a valid URL."""
    
    url: str
    
    def run(self) -> Dict[str, Any]:
        """Validate the URL and return detailed information."""
        try:
            parsed = urlparse(self.url)
            
            is_valid = bool(
                parsed.scheme and 
                parsed.netloc and 
                parsed.scheme in ['http', 'https', 'ftp', 'ftps']
            )
            
            return {
                "is_valid": is_valid,
                "scheme": parsed.scheme,
                "domain": parsed.netloc,
                "path": parsed.path,
                "query": parsed.query,
                "fragment": parsed.fragment,
                "url": self.url
            }
        except Exception as e:
            return {
                "is_valid": False,
                "error": str(e),
                "url": self.url
            }


@tool
class DomainExtractor(BaseTool):
    """Extract domain from a URL."""
    
    url: str
    
    def run(self) -> str:
        """Extract the domain from the URL."""
        try:
            parsed = urlparse(self.url)
            domain = parsed.netloc
            
            # Remove www. prefix if present
            if domain.startswith('www.'):
                domain = domain[4:]
            
            return domain
        except Exception:
            return ""


@tool
class HTMLCleaner(BaseTool):
    """Clean HTML tags from text."""
    
    html_text: str
    
    def run(self) -> str:
        """Remove HTML tags from text."""
        # Simple HTML tag removal using regex
        clean_text = re.sub(r'<[^>]+>', '', self.html_text)
        
        # Clean up common HTML entities
        clean_text = clean_text.replace('&nbsp;', ' ')
        clean_text = clean_text.replace('&amp;', '&')
        clean_text = clean_text.replace('&lt;', '<')
        clean_text = clean_text.replace('&gt;', '>')
        clean_text = clean_text.replace('&quot;', '"')
        clean_text = clean_text.replace('&#39;', "'")
        
        # Clean up whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text)
        clean_text = clean_text.strip()
        
        return clean_text


@tool
class EmailExtractor(BaseTool):
    """Extract email addresses from text."""
    
    text: str
    
    def run(self) -> List[str]:
        """Extract all email addresses from the text."""
        # Simple email regex pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        emails = re.findall(email_pattern, self.text)
        
        # Remove duplicates and return as list
        return list(set(emails)) 