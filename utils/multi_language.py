"""
Multi-Language Support Module
Extends code analysis beyond Python to JavaScript, TypeScript, Java, Go, Rust
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class Language(Enum):
    """Supported programming languages"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    GO = "go"
    RUST = "rust"

@dataclass
class SecurityPattern:
    """Security vulnerability pattern"""
    pattern: str
    severity: str
    description: str
    suggestion: str
    is_regex: bool = True

class LanguageConfig:
    """Configuration for language-specific analysis"""
    
    def __init__(self, language: Language):
        self.language = language
        self.security_patterns = self._get_security_patterns()
        self.code_smell_patterns = self._get_code_smell_patterns()
        self.complexity_keywords = self._get_complexity_keywords()
    
    def _get_security_patterns(self) -> List[SecurityPattern]:
        """Get security patterns for the language"""
        common_patterns = [
            SecurityPattern(
                pattern=r'(password|passwd|pwd|secret|api[_-]?key|token)\s*=\s*["\'][\w\-\.]+["\']',
                severity="critical",
                description="Hardcoded secret detected",
                suggestion="Use environment variables or secure vault for secrets"
            ),
        ]
        
        if self.language == Language.PYTHON:
            return common_patterns + [
                SecurityPattern(
                    pattern=r'eval\s*\(',
                    severity="high",
                    description="Use of eval() detected",
                    suggestion="Avoid eval() as it can execute arbitrary code"
                ),
                SecurityPattern(
                    pattern=r'exec\s*\(',
                    severity="high",
                    description="Use of exec() detected",
                    suggestion="Avoid exec() as it can execute arbitrary code"
                ),
                SecurityPattern(
                    pattern=r'pickle\.loads?\s*\(',
                    severity="high",
                    description="Unsafe pickle usage",
                    suggestion="Use JSON or other safe serialization formats"
                ),
                SecurityPattern(
                    pattern=r'shell\s*=\s*True',
                    severity="high",
                    description="Command injection risk with shell=True",
                    suggestion="Use shell=False and pass commands as list"
                ),
            ]
        
        elif self.language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            return common_patterns + [
                SecurityPattern(
                    pattern=r'eval\s*\(',
                    severity="high",
                    description="Use of eval() detected",
                    suggestion="Avoid eval() as it can execute arbitrary code"
                ),
                SecurityPattern(
                    pattern=r'innerHTML\s*=',
                    severity="medium",
                    description="XSS risk with innerHTML",
                    suggestion="Use textContent or sanitize input"
                ),
                SecurityPattern(
                    pattern=r'dangerouslySetInnerHTML',
                    severity="high",
                    description="XSS risk with dangerouslySetInnerHTML",
                    suggestion="Sanitize HTML content or use safe alternatives"
                ),
                SecurityPattern(
                    pattern=r'document\.write\s*\(',
                    severity="medium",
                    description="Security risk with document.write",
                    suggestion="Use safer DOM manipulation methods"
                ),
            ]
        
        elif self.language == Language.JAVA:
            return common_patterns + [
                SecurityPattern(
                    pattern=r'Runtime\.getRuntime\(\)\.exec',
                    severity="high",
                    description="Command injection risk",
                    suggestion="Validate and sanitize input before executing commands"
                ),
                SecurityPattern(
                    pattern=r'new\s+File\s*\([^)]*\+',
                    severity="medium",
                    description="Path traversal risk",
                    suggestion="Validate file paths and use Path.normalize()"
                ),
                SecurityPattern(
                    pattern=r'\.setAccessible\s*\(\s*true\s*\)',
                    severity="medium",
                    description="Reflection security risk",
                    suggestion="Avoid modifying accessibility of private members"
                ),
            ]
        
        elif self.language == Language.GO:
            return common_patterns + [
                SecurityPattern(
                    pattern=r'exec\.Command\(',
                    severity="medium",
                    description="Command execution detected",
                    suggestion="Validate input to prevent command injection"
                ),
                SecurityPattern(
                    pattern=r'sql\.Query\([^,]*\+',
                    severity="high",
                    description="SQL injection risk",
                    suggestion="Use parameterized queries"
                ),
            ]
        
        elif self.language == Language.RUST:
            return common_patterns + [
                SecurityPattern(
                    pattern=r'unsafe\s+{',
                    severity="medium",
                    description="Unsafe code block detected",
                    suggestion="Minimize unsafe code and document safety invariants"
                ),
                SecurityPattern(
                    pattern=r'\.unwrap\(\)',
                    severity="low",
                    description="Panic risk with unwrap()",
                    suggestion="Use pattern matching or expect() with descriptive message"
                ),
            ]
        
        return common_patterns
    
    def _get_code_smell_patterns(self) -> List[SecurityPattern]:
        """Get code smell patterns for the language"""
        if self.language == Language.PYTHON:
            return [
                SecurityPattern(
                    pattern=r'except\s*:',
                    severity="low",
                    description="Bare except clause",
                    suggestion="Catch specific exceptions",
                    is_regex=True
                ),
                SecurityPattern(
                    pattern=r'print\s*\(',
                    severity="low",
                    description="Using print() for output",
                    suggestion="Use logging module",
                    is_regex=True
                ),
            ]
        
        elif self.language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            return [
                SecurityPattern(
                    pattern=r'console\.log\s*\(',
                    severity="low",
                    description="Console.log in production code",
                    suggestion="Use proper logging framework",
                    is_regex=True
                ),
                SecurityPattern(
                    pattern=r'var\s+\w+',
                    severity="low",
                    description="Using var instead of let/const",
                    suggestion="Use let or const for block scoping",
                    is_regex=True
                ),
            ]
        
        elif self.language == Language.JAVA:
            return [
                SecurityPattern(
                    pattern=r'System\.out\.print',
                    severity="low",
                    description="Using System.out for logging",
                    suggestion="Use proper logging framework (slf4j, log4j)",
                    is_regex=True
                ),
            ]
        
        return []
    
    def _get_complexity_keywords(self) -> List[str]:
        """Get keywords that contribute to complexity"""
        if self.language == Language.PYTHON:
            return ['if', 'elif', 'else', 'for', 'while', 'and', 'or', 'try', 'except', 'with']
        
        elif self.language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            return ['if', 'else', 'for', 'while', 'switch', 'case', '&&', '||', 'try', 'catch']
        
        elif self.language == Language.JAVA:
            return ['if', 'else', 'for', 'while', 'switch', 'case', '&&', '||', 'try', 'catch']
        
        elif self.language == Language.GO:
            return ['if', 'else', 'for', 'switch', 'case', '&&', '||', 'defer', 'select']
        
        elif self.language == Language.RUST:
            return ['if', 'else', 'for', 'while', 'match', '&&', '||', 'loop']
        
        return []

class MultiLanguageAnalyzer:
    """Analyzes code in multiple programming languages"""
    
    def __init__(self):
        self.language_configs: Dict[Language, LanguageConfig] = {}
    
    def get_config(self, language: str) -> LanguageConfig:
        """Get or create language config"""
        try:
            lang_enum = Language(language.lower())
        except ValueError:
            logger.warning(f"Unsupported language: {language}, falling back to Python")
            lang_enum = Language.PYTHON
        
        if lang_enum not in self.language_configs:
            self.language_configs[lang_enum] = LanguageConfig(lang_enum)
        
        return self.language_configs[lang_enum]
    
    def detect_language(self, code: str, filename: str = "") -> str:
        """Detect programming language from code or filename"""
        # Check file extension first
        if filename:
            ext_map = {
                '.py': 'python',
                '.js': 'javascript',
                '.ts': 'typescript',
                '.tsx': 'typescript',
                '.jsx': 'javascript',
                '.java': 'java',
                '.go': 'go',
                '.rs': 'rust',
            }
            
            for ext, lang in ext_map.items():
                if filename.endswith(ext):
                    return lang
        
        # Analyze code patterns
        if 'def ' in code and 'import ' in code:
            return 'python'
        elif 'function ' in code or 'const ' in code or '=>' in code:
            if ': ' in code and 'interface ' in code:
                return 'typescript'
            return 'javascript'
        elif 'public class ' in code or 'private ' in code:
            return 'java'
        elif 'func ' in code and 'package ' in code:
            return 'go'
        elif 'fn ' in code and ('let ' in code or 'mut ' in code):
            return 'rust'
        
        return 'python'  # Default
    
    def scan_security(self, code: str, language: str) -> List[Dict[str, Any]]:
        """Scan for security vulnerabilities"""
        config = self.get_config(language)
        vulnerabilities = []
        
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern in config.security_patterns:
                if pattern.is_regex:
                    if re.search(pattern.pattern, line, re.IGNORECASE):
                        vulnerabilities.append({
                            'severity': pattern.severity,
                            'type': 'security_vulnerability',
                            'line': i,
                            'description': pattern.description,
                            'suggestion': pattern.suggestion,
                            'code': line.strip()
                        })
                else:
                    if pattern.pattern in line:
                        vulnerabilities.append({
                            'severity': pattern.severity,
                            'type': 'security_vulnerability',
                            'line': i,
                            'description': pattern.description,
                            'suggestion': pattern.suggestion,
                            'code': line.strip()
                        })
        
        return vulnerabilities
    
    def detect_code_smells(self, code: str, language: str) -> List[Dict[str, Any]]:
        """Detect code smells"""
        config = self.get_config(language)
        smells = []
        
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern in config.code_smell_patterns:
                if pattern.is_regex:
                    if re.search(pattern.pattern, line):
                        smells.append({
                            'severity': pattern.severity,
                            'type': pattern.description.lower().replace(' ', '_'),
                            'line': i,
                            'description': pattern.description,
                            'suggestion': pattern.suggestion
                        })
        
        return smells
    
    def calculate_complexity(self, code: str, language: str) -> int:
        """Calculate cyclomatic complexity"""
        config = self.get_config(language)
        complexity = 1  # Base complexity
        
        for keyword in config.complexity_keywords:
            # Count occurrences (word boundaries for keywords)
            if keyword.isalpha():
                pattern = r'\b' + keyword + r'\b'
                complexity += len(re.findall(pattern, code))
            else:
                complexity += code.count(keyword)
        
        return complexity
    
    def count_functions(self, code: str, language: str) -> int:
        """Count number of functions/methods"""
        if language == 'python':
            return len(re.findall(r'\bdef\s+\w+', code))
        elif language in ['javascript', 'typescript']:
            func_count = len(re.findall(r'\bfunction\s+\w+', code))
            func_count += len(re.findall(r'\w+\s*=\s*\([^)]*\)\s*=>', code))
            func_count += len(re.findall(r'\w+\s*:\s*\([^)]*\)\s*=>', code))
            return func_count
        elif language == 'java':
            return len(re.findall(r'(public|private|protected)\s+\w+\s+\w+\s*\([^)]*\)', code))
        elif language == 'go':
            return len(re.findall(r'\bfunc\s+\w+', code))
        elif language == 'rust':
            return len(re.findall(r'\bfn\s+\w+', code))
        
        return 0
    
    def count_classes(self, code: str, language: str) -> int:
        """Count number of classes"""
        if language == 'python':
            return len(re.findall(r'\bclass\s+\w+', code))
        elif language in ['javascript', 'typescript']:
            return len(re.findall(r'\bclass\s+\w+', code))
        elif language == 'java':
            return len(re.findall(r'\bclass\s+\w+', code))
        elif language == 'go':
            return len(re.findall(r'\btype\s+\w+\s+struct', code))
        elif language == 'rust':
            return len(re.findall(r'\bstruct\s+\w+', code))
        
        return 0

# Global instance
multi_language_analyzer = MultiLanguageAnalyzer()
