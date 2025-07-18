"""Data Tools Plugin - Example plugin providing data processing functionality."""

import json
import csv
import io
from typing import Dict, Any, List, Union
from collections import Counter

from tomo import BaseTool, tool
from tomo.plugins import BasePlugin, PluginType, plugin


@plugin(PluginType.TOOL, "data_tools", "1.0.0")
class DataToolsPlugin(BasePlugin):
    """Plugin providing data processing and analysis tools."""
    
    @property
    def plugin_type(self) -> PluginType:
        return PluginType.TOOL
    
    @property
    def name(self) -> str:
        return "data_tools"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Data processing tools including JSON parsing, CSV operations, and text analysis"
    
    @property
    def author(self) -> str:
        return "Tomo Community"
    
    @property
    def homepage(self) -> str:
        return "https://github.com/tomo-framework/tomo/tree/main/examples/plugins"
    
    def initialize(self, config: Dict[str, Any] = None) -> None:
        """Initialize the data tools plugin."""
        self.config = config or {}
        print(f"📊 Initializing {self.name} plugin v{self.version}")
    
    def register_components(self, registry) -> None:
        """Register data tools with the registry."""
        registry.tool_registry.register(JSONParser)
        registry.tool_registry.register(JSONValidator)
        registry.tool_registry.register(CSVParser)
        registry.tool_registry.register(TextAnalyzer)
        registry.tool_registry.register(ListProcessor)


@tool
class JSONParser(BaseTool):
    """Parse JSON string and extract values."""
    
    json_string: str
    key_path: str = ""  # Optional: dot-separated path like "user.name"
    
    def run(self) -> Union[Dict[str, Any], Any]:
        """Parse JSON and optionally extract value by key path."""
        try:
            data = json.loads(self.json_string)
            
            if not self.key_path:
                return data
            
            # Navigate through nested keys
            current = data
            for key in self.key_path.split('.'):
                if isinstance(current, dict) and key in current:
                    current = current[key]
                elif isinstance(current, list) and key.isdigit():
                    index = int(key)
                    if 0 <= index < len(current):
                        current = current[index]
                    else:
                        return None
                else:
                    return None
            
            return current
            
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            return {"error": f"JSON parsing failed: {str(e)}"}


@tool
class JSONValidator(BaseTool):
    """Validate if a string is valid JSON."""
    
    json_string: str
    
    def run(self) -> Dict[str, Any]:
        """Validate JSON string and return validation result."""
        try:
            data = json.loads(self.json_string)
            return {
                "is_valid": True,
                "type": type(data).__name__,
                "length": len(data) if hasattr(data, '__len__') else None,
                "keys": list(data.keys()) if isinstance(data, dict) else None
            }
        except (json.JSONDecodeError, ValueError) as e:
            return {
                "is_valid": False,
                "error": str(e),
                "error_type": type(e).__name__
            }


@tool
class CSVParser(BaseTool):
    """Parse CSV data and return as list of dictionaries."""
    
    csv_data: str
    delimiter: str = ","
    has_header: bool = True
    
    def run(self) -> List[Dict[str, str]]:
        """Parse CSV data and return as structured data."""
        try:
            csv_file = io.StringIO(self.csv_data)
            
            if self.has_header:
                reader = csv.DictReader(csv_file, delimiter=self.delimiter)
                return list(reader)
            else:
                reader = csv.reader(csv_file, delimiter=self.delimiter)
                rows = list(reader)
                
                if not rows:
                    return []
                
                # Use column indices as keys
                header = [f"col_{i}" for i in range(len(rows[0]))]
                return [dict(zip(header, row)) for row in rows]
                
        except Exception as e:
            return [{"error": f"CSV parsing failed: {str(e)}"}]


@tool
class TextAnalyzer(BaseTool):
    """Analyze text and provide statistics."""
    
    text: str
    
    def run(self) -> Dict[str, Any]:
        """Analyze text and return various statistics."""
        words = self.text.split()
        sentences = [s.strip() for s in self.text.split('.') if s.strip()]
        lines = self.text.split('\n')
        
        # Character frequency
        char_freq = Counter(self.text.lower())
        most_common_chars = char_freq.most_common(5)
        
        # Word frequency
        word_freq = Counter(word.lower().strip('.,!?;:"()[]') for word in words)
        most_common_words = word_freq.most_common(10)
        
        return {
            "character_count": len(self.text),
            "character_count_no_spaces": len(self.text.replace(' ', '')),
            "word_count": len(words),
            "sentence_count": len(sentences),
            "line_count": len(lines),
            "average_word_length": sum(len(word) for word in words) / len(words) if words else 0,
            "most_common_characters": [{"char": char, "count": count} for char, count in most_common_chars],
            "most_common_words": [{"word": word, "count": count} for word, count in most_common_words],
            "unique_words": len(set(word.lower() for word in words))
        }


@tool
class ListProcessor(BaseTool):
    """Process lists of data with various operations."""
    
    data: List[Union[str, int, float]]
    operation: str  # "sort", "unique", "count", "sum", "average", "max", "min"
    
    def run(self) -> Union[List[Any], Dict[str, Any], float, int]:
        """Process the list based on the specified operation."""
        if not self.data:
            return {"error": "Empty list provided"}
        
        try:
            if self.operation == "sort":
                return sorted(self.data)
            
            elif self.operation == "unique":
                return list(set(self.data))
            
            elif self.operation == "count":
                counter = Counter(self.data)
                return [{"value": value, "count": count} for value, count in counter.most_common()]
            
            elif self.operation == "sum":
                numeric_data = [x for x in self.data if isinstance(x, (int, float))]
                return sum(numeric_data) if numeric_data else 0
            
            elif self.operation == "average":
                numeric_data = [x for x in self.data if isinstance(x, (int, float))]
                return sum(numeric_data) / len(numeric_data) if numeric_data else 0
            
            elif self.operation == "max":
                return max(self.data)
            
            elif self.operation == "min":
                return min(self.data)
            
            else:
                return {"error": f"Unknown operation: {self.operation}"}
                
        except Exception as e:
            return {"error": f"Operation failed: {str(e)}"} 