"""Custom tools for code analysis.

This module provides custom tools that can be used by agents for:
- Code parsing and AST analysis
- Complexity calculation
- Pattern detection
- Security vulnerability scanning
"""

import ast
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class CodeMetrics:
    """Container for code metrics."""
    lines_of_code: int
    num_functions: int
    num_classes: int
    complexity: int
    max_function_complexity: int
    average_function_complexity: float


@dataclass
class SecurityIssue:
    """Container for security issues."""
    severity: str  # 'critical', 'high', 'medium', 'low'
    issue_type: str
    line_number: Optional[int]
    description: str
    recommendation: str


@dataclass
class CodeIssue:
    """Container for code quality issues."""
    severity: str
    issue_type: str
    line_number: Optional[int]
    description: str
    suggestion: str


class CodeAnalysisTools:
    """Custom tools for code analysis.
    
    This class provides various tools that agents can use to analyze code:
    - parse_code: Parse code into AST
    - calculate_complexity: Calculate cyclomatic complexity
    - detect_patterns: Detect common patterns and anti-patterns
    - scan_security: Scan for security vulnerabilities
    """
    
    def __init__(self):
        """Initialize code analysis tools."""
        logger.info("Initializing CodeAnalysisTools")
        self.security_patterns = self._load_security_patterns()
        self.code_smell_patterns = self._load_code_smell_patterns()
    
    def _load_security_patterns(self) -> Dict[str, List[str]]:
        """Load security vulnerability patterns."""
        return {
            'sql_injection': [
                r'execute\s*\(\s*[\'"].*?\%s.*?[\'"]',
                r'\.format\s*\(',
                r'f[\'"].*?{.*?}.*?[\'"].*?(SELECT|INSERT|UPDATE|DELETE)',
            ],
            'hardcoded_secrets': [
                r'password\s*=\s*[\'"][^\'"]+[\'"]',
                r'api[_-]?key\s*=\s*[\'"][^\'"]+[\'"]',
                r'secret\s*=\s*[\'"][^\'"]+[\'"]',
                r'token\s*=\s*[\'"][^\'"]+[\'"]',
            ],
            'insecure_functions': [
                r'\beval\s*\(',
                r'\bexec\s*\(',
                r'pickle\.loads?\s*\(',
                r'yaml\.load\s*\(',
            ],
            'command_injection': [
                r'os\.system\s*\(',
                r'subprocess\.call\s*\([^)]*shell\s*=\s*True',
                r'subprocess\.Popen\s*\([^)]*shell\s*=\s*True',
            ],
            'path_traversal': [
                r'open\s*\(\s*[^)]*\+',
                r'file\s*=.*?\+',
            ],
        }
    
    def _load_code_smell_patterns(self) -> Dict[str, str]:
        """Load code smell patterns."""
        return {
            'long_function': 'Function has more than 50 lines',
            'too_many_parameters': 'Function has more than 5 parameters',
            'deep_nesting': 'Nesting depth exceeds 4 levels',
            'broad_except': 'Catching broad Exception',
            'print_statements': 'Using print instead of logging',
            'todo_comments': 'TODO comments found',
        }
    
    def parse_code(self, code: str, language: str = 'python') -> Optional[ast.AST]:
        """Parse code into an Abstract Syntax Tree.
        
        Args:
            code: Source code to parse
            language: Programming language (currently only Python supported)
        
        Returns:
            AST tree or None if parsing fails
        """
        if language.lower() != 'python':
            logger.warning(f"Language {language} not supported, only Python is supported")
            return None
        
        try:
            tree = ast.parse(code)
            logger.info("Successfully parsed code into AST")
            return tree
        except SyntaxError as e:
            logger.error(f"Syntax error in code: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing code: {e}")
            return None
    
    def calculate_metrics(self, code: str, language: str = 'python') -> CodeMetrics:
        """Calculate various code metrics.
        
        Args:
            code: Source code to analyze
            language: Programming language
        
        Returns:
            CodeMetrics object with calculated metrics
        """
        logger.info("Calculating code metrics")
        
        tree = self.parse_code(code, language)
        if not tree:
            return CodeMetrics(
                lines_of_code=len(code.splitlines()),
                num_functions=0,
                num_classes=0,
                complexity=0,
                max_function_complexity=0,
                average_function_complexity=0.0
            )
        
        # Count functions and classes
        num_functions = sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
        num_classes = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
        
        # Calculate complexity for each function
        function_complexities = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_complexity(node)
                function_complexities.append(complexity)
        
        total_complexity = sum(function_complexities) if function_complexities else 0
        max_complexity = max(function_complexities) if function_complexities else 0
        avg_complexity = total_complexity / len(function_complexities) if function_complexities else 0.0
        
        metrics = CodeMetrics(
            lines_of_code=len(code.splitlines()),
            num_functions=num_functions,
            num_classes=num_classes,
            complexity=total_complexity,
            max_function_complexity=max_complexity,
            average_function_complexity=avg_complexity
        )
        
        logger.info(f"Metrics calculated: {metrics}")
        return metrics
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity for a function.
        
        Args:
            node: AST node representing a function
        
        Returns:
            Cyclomatic complexity score
        """
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            # Add complexity for control flow statements
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, (ast.comprehension,)):
                complexity += 1
        
        return complexity
    
    def detect_code_smells(self, code: str, language: str = 'python') -> List[CodeIssue]:
        """Detect code smells and anti-patterns.
        
        Args:
            code: Source code to analyze
            language: Programming language
        
        Returns:
            List of detected code issues
        """
        logger.info("Detecting code smells")
        issues = []
        
        tree = self.parse_code(code, language)
        if not tree:
            return issues
        
        lines = code.splitlines()
        
        # Check for long functions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
                if func_lines > 50:
                    issues.append(CodeIssue(
                        severity='medium',
                        issue_type='long_function',
                        line_number=node.lineno,
                        description=f"Function '{node.name}' is {func_lines} lines long",
                        suggestion="Consider breaking down into smaller functions"
                    ))
                
                # Check for too many parameters
                if len(node.args.args) > 5:
                    issues.append(CodeIssue(
                        severity='medium',
                        issue_type='too_many_parameters',
                        line_number=node.lineno,
                        description=f"Function '{node.name}' has {len(node.args.args)} parameters",
                        suggestion="Consider using a configuration object or reducing parameters"
                    ))
                
                # Check complexity
                complexity = self._calculate_complexity(node)
                if complexity > 10:
                    issues.append(CodeIssue(
                        severity='high',
                        issue_type='high_complexity',
                        line_number=node.lineno,
                        description=f"Function '{node.name}' has complexity {complexity}",
                        suggestion="Refactor to reduce cyclomatic complexity"
                    ))
        
        # Check for broad exception handling
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if node.type is None or (isinstance(node.type, ast.Name) and node.type.id == 'Exception'):
                    issues.append(CodeIssue(
                        severity='medium',
                        issue_type='broad_except',
                        line_number=node.lineno,
                        description="Catching broad Exception",
                        suggestion="Catch specific exceptions instead"
                    ))
        
        # Check for print statements
        for i, line in enumerate(lines, 1):
            if re.search(r'\bprint\s*\(', line):
                issues.append(CodeIssue(
                    severity='low',
                    issue_type='print_statement',
                    line_number=i,
                    description="Using print() for output",
                    suggestion="Use logging module for better control"
                ))
            
            # Check for TODO comments
            if re.search(r'#.*?\bTODO\b', line, re.IGNORECASE):
                issues.append(CodeIssue(
                    severity='low',
                    issue_type='todo_comment',
                    line_number=i,
                    description="TODO comment found",
                    suggestion="Address TODO or create a ticket"
                ))
        
        logger.info(f"Found {len(issues)} code smells")
        return issues
    
    def scan_security(self, code: str, language: str = 'python') -> List[SecurityIssue]:
        """Scan code for security vulnerabilities.
        
        Args:
            code: Source code to scan
            language: Programming language
        
        Returns:
            List of security issues found
        """
        logger.info("Scanning for security vulnerabilities")
        issues = []
        
        lines = code.splitlines()
        
        # Check for SQL injection patterns
        for i, line in enumerate(lines, 1):
            for pattern in self.security_patterns['sql_injection']:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(SecurityIssue(
                        severity='critical',
                        issue_type='sql_injection',
                        line_number=i,
                        description="Potential SQL injection vulnerability",
                        recommendation="Use parameterized queries or ORM"
                    ))
                    break
        
        # Check for hardcoded secrets
        for i, line in enumerate(lines, 1):
            for pattern in self.security_patterns['hardcoded_secrets']:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(SecurityIssue(
                        severity='high',
                        issue_type='hardcoded_secret',
                        line_number=i,
                        description="Hardcoded secret or credential detected",
                        recommendation="Use environment variables or secret management service"
                    ))
                    break
        
        # Check for insecure functions
        for i, line in enumerate(lines, 1):
            for pattern in self.security_patterns['insecure_functions']:
                if re.search(pattern, line):
                    issues.append(SecurityIssue(
                        severity='high',
                        issue_type='insecure_function',
                        line_number=i,
                        description="Use of dangerous function (eval/exec/pickle)",
                        recommendation="Avoid eval/exec, use safer alternatives"
                    ))
                    break
        
        # Check for command injection
        for i, line in enumerate(lines, 1):
            for pattern in self.security_patterns['command_injection']:
                if re.search(pattern, line):
                    issues.append(SecurityIssue(
                        severity='critical',
                        issue_type='command_injection',
                        line_number=i,
                        description="Potential command injection vulnerability",
                        recommendation="Use subprocess with shell=False and argument list"
                    ))
                    break
        
        # Check for path traversal
        for i, line in enumerate(lines, 1):
            for pattern in self.security_patterns['path_traversal']:
                if re.search(pattern, line):
                    issues.append(SecurityIssue(
                        severity='medium',
                        issue_type='path_traversal',
                        line_number=i,
                        description="Potential path traversal vulnerability",
                        recommendation="Validate and sanitize file paths"
                    ))
                    break
        
        logger.info(f"Found {len(issues)} security issues")
        return issues
    
    def get_function_info(self, code: str, language: str = 'python') -> List[Dict[str, Any]]:
        """Extract information about all functions in the code.
        
        Args:
            code: Source code to analyze
            language: Programming language
        
        Returns:
            List of dictionaries containing function information
        """
        logger.info("Extracting function information")
        
        tree = self.parse_code(code, language)
        if not tree:
            return []
        
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append({
                    'name': node.name,
                    'line_number': node.lineno,
                    'num_parameters': len(node.args.args),
                    'complexity': self._calculate_complexity(node),
                    'has_docstring': ast.get_docstring(node) is not None,
                })
        
        logger.info(f"Found {len(functions)} functions")
        return functions
