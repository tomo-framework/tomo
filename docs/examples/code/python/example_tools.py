"""
Example Tomo tools for TypeScript integration.

This module demonstrates various types of tools that can be created with Tomo
and consumed by TypeScript applications via MCP or REST API.
"""

import json
import time
from typing import List, Optional, Dict, Any
from datetime import datetime
from tomo import BaseTool, tool


@tool
class Calculator(BaseTool):
    """Perform basic mathematical calculations."""
    
    operation: str  # add, subtract, multiply, divide, power
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
        elif self.operation == "power":
            return self.a ** self.b
        else:
            raise ValueError(f"Unknown operation: {self.operation}")


@tool
class WeatherChecker(BaseTool):
    """Get weather information for a city (mock implementation)."""
    
    city: str
    country: Optional[str] = None
    units: str = "celsius"  # celsius, fahrenheit
    
    def run(self) -> Dict[str, Any]:
        """Get weather data (mock implementation)."""
        # This is a mock implementation - in real use, you'd call a weather API
        import random
        
        temperature_base = 20 if self.units == "celsius" else 68
        temperature = temperature_base + random.randint(-10, 15)
        
        conditions = ["sunny", "cloudy", "rainy", "partly cloudy", "overcast"]
        
        return {
            "city": self.city,
            "country": self.country or "Unknown",
            "temperature": temperature,
            "units": self.units,
            "condition": random.choice(conditions),
            "humidity": random.randint(30, 90),
            "timestamp": datetime.now().isoformat()
        }


@tool
class TextProcessor(BaseTool):
    """Process text with various operations."""
    
    text: str
    operation: str  # uppercase, lowercase, reverse, word_count, char_count
    
    def run(self) -> Dict[str, Any]:
        """Process the text according to the operation."""
        result = {"original_text": self.text, "operation": self.operation}
        
        if self.operation == "uppercase":
            result["processed_text"] = self.text.upper()
        elif self.operation == "lowercase":
            result["processed_text"] = self.text.lower()
        elif self.operation == "reverse":
            result["processed_text"] = self.text[::-1]
        elif self.operation == "word_count":
            result["count"] = len(self.text.split())
        elif self.operation == "char_count":
            result["count"] = len(self.text)
        else:
            raise ValueError(f"Unknown operation: {self.operation}")
        
        return result


@tool
class DataValidator(BaseTool):
    """Validate data against various criteria."""
    
    value: Any
    validation_type: str  # email, url, positive_number, non_empty_string
    
    def run(self) -> Dict[str, Any]:
        """Validate the value."""
        result = {
            "value": self.value,
            "validation_type": self.validation_type,
            "is_valid": False,
            "message": ""
        }
        
        if self.validation_type == "email":
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            result["is_valid"] = bool(re.match(email_pattern, str(self.value)))
            result["message"] = "Valid email" if result["is_valid"] else "Invalid email format"
            
        elif self.validation_type == "url":
            import re
            url_pattern = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?$'
            result["is_valid"] = bool(re.match(url_pattern, str(self.value)))
            result["message"] = "Valid URL" if result["is_valid"] else "Invalid URL format"
            
        elif self.validation_type == "positive_number":
            try:
                num = float(self.value)
                result["is_valid"] = num > 0
                result["message"] = "Positive number" if result["is_valid"] else "Must be a positive number"
            except (ValueError, TypeError):
                result["message"] = "Not a valid number"
                
        elif self.validation_type == "non_empty_string":
            result["is_valid"] = isinstance(self.value, str) and len(self.value.strip()) > 0
            result["message"] = "Non-empty string" if result["is_valid"] else "Must be a non-empty string"
            
        else:
            raise ValueError(f"Unknown validation type: {self.validation_type}")
        
        return result


@tool
class FileGenerator(BaseTool):
    """Generate files with different formats."""
    
    filename: str
    content_type: str  # json, csv, txt
    data: List[Dict[str, Any]]
    
    def run(self) -> Dict[str, Any]:
        """Generate file content."""
        result = {
            "filename": self.filename,
            "content_type": self.content_type,
            "row_count": len(self.data)
        }
        
        if self.content_type == "json":
            result["content"] = json.dumps(self.data, indent=2)
            
        elif self.content_type == "csv":
            if not self.data:
                result["content"] = ""
            else:
                import csv
                import io
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=self.data[0].keys())
                writer.writeheader()
                writer.writerows(self.data)
                result["content"] = output.getvalue()
                
        elif self.content_type == "txt":
            lines = []
            for item in self.data:
                line = " | ".join(str(v) for v in item.values())
                lines.append(line)
            result["content"] = "\n".join(lines)
            
        else:
            raise ValueError(f"Unknown content type: {self.content_type}")
        
        return result


@tool
class NumberSequence(BaseTool):
    """Generate number sequences."""
    
    sequence_type: str  # fibonacci, prime, even, odd, squares
    count: int
    
    def run(self) -> List[int]:
        """Generate the requested sequence."""
        if self.count <= 0:
            return []
        
        if self.sequence_type == "fibonacci":
            sequence = [0, 1]
            while len(sequence) < self.count:
                sequence.append(sequence[-1] + sequence[-2])
            return sequence[:self.count]
            
        elif self.sequence_type == "prime":
            primes = []
            num = 2
            while len(primes) < self.count:
                is_prime = True
                for p in primes:
                    if p * p > num:
                        break
                    if num % p == 0:
                        is_prime = False
                        break
                if is_prime:
                    primes.append(num)
                num += 1
            return primes
            
        elif self.sequence_type == "even":
            return [i * 2 for i in range(self.count)]
            
        elif self.sequence_type == "odd":
            return [i * 2 + 1 for i in range(self.count)]
            
        elif self.sequence_type == "squares":
            return [i * i for i in range(1, self.count + 1)]
            
        else:
            raise ValueError(f"Unknown sequence type: {self.sequence_type}")


@tool
class DateTimeUtility(BaseTool):
    """Utility for date and time operations."""
    
    operation: str  # current_time, format_date, days_between, add_days
    date_string: Optional[str] = None
    format_string: Optional[str] = None
    days: Optional[int] = None
    end_date: Optional[str] = None
    
    def run(self) -> Dict[str, Any]:
        """Perform date/time operations."""
        result = {"operation": self.operation}
        
        if self.operation == "current_time":
            result.update({
                "iso_format": datetime.now().isoformat(),
                "unix_timestamp": int(time.time()),
                "formatted": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
        elif self.operation == "format_date":
            if not self.date_string or not self.format_string:
                raise ValueError("date_string and format_string required for format_date")
            
            # Try to parse the date
            try:
                dt = datetime.fromisoformat(self.date_string.replace('Z', '+00:00'))
                result["formatted_date"] = dt.strftime(self.format_string)
            except ValueError:
                raise ValueError(f"Invalid date format: {self.date_string}")
                
        elif self.operation == "add_days":
            if not self.date_string or self.days is None:
                raise ValueError("date_string and days required for add_days")
            
            try:
                from datetime import timedelta
                dt = datetime.fromisoformat(self.date_string.replace('Z', '+00:00'))
                new_dt = dt + timedelta(days=self.days)
                result.update({
                    "original_date": self.date_string,
                    "days_added": self.days,
                    "new_date": new_dt.isoformat()
                })
            except ValueError:
                raise ValueError(f"Invalid date format: {self.date_string}")
                
        else:
            raise ValueError(f"Unknown operation: {self.operation}")
        
        return result


# Example of registering tools
if __name__ == "__main__":
    from tomo import ToolRegistry, ToolRunner
    
    # Create registry and register all tools
    registry = ToolRegistry()
    registry.register(Calculator)
    registry.register(WeatherChecker)
    registry.register(TextProcessor)
    registry.register(DataValidator)
    registry.register(FileGenerator)
    registry.register(NumberSequence)
    registry.register(DateTimeUtility)
    
    print("Registered tools:", registry.list())
    
    # Test some tools
    runner = ToolRunner(registry)
    
    # Test Calculator
    calc_result = runner.run_tool("Calculator", {
        "operation": "add",
        "a": 15,
        "b": 25
    })
    print(f"Calculator result: {calc_result}")
    
    # Test Weather
    weather_result = runner.run_tool("WeatherChecker", {
        "city": "Tokyo",
        "country": "Japan"
    })
    print(f"Weather result: {weather_result}") 