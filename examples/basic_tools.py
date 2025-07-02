"""Basic example tools for demonstrating Tomo."""

from tomo import BaseTool, tool


@tool
class Calculator(BaseTool):
    """Perform basic mathematical calculations."""
    
    operation: str  # add, subtract, multiply, divide
    a: float
    b: float
    
    def run(self) -> float:
        """Execute the calculation."""
        if self.operation == "add":
            return self.a + self.b
        elif self.operation == "subtract":
            return self.a - self.b
        elif self.operation == "multiply":
            return self.a * self.b
        elif self.operation == "divide":
            if self.b == 0:
                raise ValueError("Cannot divide by zero")
            return self.a / self.b
        else:
            raise ValueError(f"Unknown operation: {self.operation}")


@tool
class TextProcessor(BaseTool):
    """Process text with various operations."""
    
    text: str
    operation: str  # uppercase, lowercase, reverse, word_count
    
    def run(self) -> str:
        """Process the text."""
        if self.operation == "uppercase":
            return self.text.upper()
        elif self.operation == "lowercase":
            return self.text.lower()
        elif self.operation == "reverse":
            return self.text[::-1]
        elif self.operation == "word_count":
            word_count = len(self.text.split())
            return f"Word count: {word_count}"
        else:
            raise ValueError(f"Unknown operation: {self.operation}")


@tool
class Weather(BaseTool):
    """Get weather information for a city (mock implementation)."""
    
    city: str
    units: str = "celsius"  # celsius, fahrenheit
    
    def run(self) -> dict:
        """Get weather information (mock data)."""
        # This is a mock implementation
        temp_c = 22  # Mock temperature
        
        if self.units == "fahrenheit":
            temp = temp_c * 9/5 + 32
            unit = "°F"
        else:
            temp = temp_c
            unit = "°C"
        
        return {
            "city": self.city,
            "temperature": f"{temp}{unit}",
            "condition": "Sunny",
            "humidity": "65%",
            "wind": "10 km/h"
        }


@tool
class Translator(BaseTool):
    """Translate text between languages (mock implementation)."""
    
    text: str
    from_lang: str = "auto"
    to_lang: str = "en"
    
    def run(self) -> dict:
        """Translate text (mock implementation)."""
        # This is a mock translation
        translations = {
            ("hello", "es"): "hola",
            ("hello", "fr"): "bonjour", 
            ("hello", "de"): "hallo",
            ("goodbye", "es"): "adiós",
            ("goodbye", "fr"): "au revoir",
            ("goodbye", "de"): "auf wiedersehen"
        }
        
        translated = translations.get((self.text.lower(), self.to_lang), 
                                     f"[Translated: {self.text}]")
        
        return {
            "original": self.text,
            "translated": translated,
            "from_language": self.from_lang,
            "to_language": self.to_lang
        }


@tool
class FileInfo(BaseTool):
    """Get information about a file path."""
    
    file_path: str
    
    def run(self) -> dict:
        """Get file information."""
        import os
        from pathlib import Path
        
        path = Path(self.file_path)
        
        if not path.exists():
            return {
                "exists": False,
                "path": str(path),
                "error": "File does not exist"
            }
        
        stat = path.stat()
        
        return {
            "exists": True,
            "path": str(path),
            "name": path.name,
            "size_bytes": stat.st_size,
            "is_file": path.is_file(),
            "is_directory": path.is_dir(),
            "parent": str(path.parent),
            "extension": path.suffix
        } 