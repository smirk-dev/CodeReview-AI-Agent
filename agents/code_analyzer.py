"""CodeAnalyzerAgent - Performs initial code analysis.

This agent specializes in:
- Code structure analysis using AST
- Complexity metrics calculation
- Pattern detection
- Basic code quality assessment
"""

from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class CodeAnalyzerAgent:
    """Agent specialized in code structure and complexity analysis.
    
    This agent uses custom tools to:
    1. Parse code into AST
    2. Calculate cyclomatic complexity
    3. Extract code metrics
    4. Detect common patterns
    5. Identify potential code smells
    """
    
    def __init__(self, client, code_tools):
        """Initialize the CodeAnalyzerAgent.
        
        Args:
            client: Google GenAI client for LLM access
            code_tools: CodeAnalysisTools instance
        """
        self.client = client
        self.code_tools = code_tools
        self.model_name = "gemini-2.0-flash-exp"
        logger.info(f"CodeAnalyzerAgent initialized with model: {self.model_name}")
    
    def analyze(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Perform comprehensive code analysis.
        
        Args:
            code: Source code to analyze
            language: Programming language
        
        Returns:
            Dictionary containing analysis results
        """
        logger.info(f"Starting code analysis for {language} code ({len(code)} chars)")
        
        results = {
            'status': 'success',
            'language': language,
            'metrics': {},
            'functions': [],
            'code_smells': [],
            'summary': '',
            'issues': []
        }
        
        try:
            # Calculate code metrics
            metrics = self.code_tools.calculate_metrics(code, language)
            results['metrics'] = {
                'lines_of_code': metrics.lines_of_code,
                'num_functions': metrics.num_functions,
                'num_classes': metrics.num_classes,
                'total_complexity': metrics.complexity,
                'max_function_complexity': metrics.max_function_complexity,
                'average_function_complexity': round(metrics.average_function_complexity, 2)
            }
            logger.info(f"Metrics calculated: {metrics.lines_of_code} LOC, {metrics.num_functions} functions")
            
            # Get function information
            functions = self.code_tools.get_function_info(code, language)
            results['functions'] = functions
            logger.info(f"Extracted {len(functions)} function details")
            
            # Detect code smells
            code_smells = self.code_tools.detect_code_smells(code, language)
            results['code_smells'] = [
                {
                    'severity': smell.severity,
                    'type': smell.issue_type,
                    'line': smell.line_number,
                    'description': smell.description,
                    'suggestion': smell.suggestion
                }
                for smell in code_smells
            ]
            results['issues'] = results['code_smells']
            logger.info(f"Detected {len(code_smells)} code smells")
            
            # Generate AI-powered summary using Gemini
            summary = self._generate_ai_summary(code, results, language)
            results['summary'] = summary
            
            # Add recommendations
            results['recommendations'] = self._generate_recommendations(results)
            
            logger.info("Code analysis completed successfully")
            
        except Exception as e:
            logger.error(f"Error during code analysis: {e}")
            results['status'] = 'error'
            results['error'] = str(e)
        
        return results
    
    def _generate_ai_summary(self, code: str, analysis: Dict, language: str) -> str:
        """Generate AI-powered analysis summary using Gemini.
        
        Args:
            code: Source code
            analysis: Analysis results so far
            language: Programming language
        
        Returns:
            AI-generated summary string
        """
        try:
            metrics = analysis['metrics']
            functions = analysis['functions']
            code_smells = analysis['code_smells']
            
            prompt = f"""You are a code analysis expert. Analyze this {language} code and provide a concise summary.

Code Metrics:
- Lines of Code: {metrics['lines_of_code']}
- Functions: {metrics['num_functions']}
- Classes: {metrics['num_classes']}
- Total Complexity: {metrics['total_complexity']}
- Average Function Complexity: {metrics['average_function_complexity']}

Functions Found: {len(functions)}
Code Smells Detected: {len(code_smells)}

Provide a 2-3 sentence summary of the code structure and quality. Focus on:
1. Overall code organization
2. Key complexity concerns
3. Main areas for improvement

Code:
```{language}
{code[:1000]}  # First 1000 chars
```

Summary:"""

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            summary = response.text.strip()
            logger.info("Generated AI summary")
            return summary
            
        except Exception as e:
            logger.warning(f"Error generating AI summary: {e}")
            return f"Code contains {metrics['lines_of_code']} lines with {metrics['num_functions']} functions. Complexity score: {metrics['total_complexity']}."
    
    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """Generate recommendations based on analysis.
        
        Args:
            analysis: Analysis results
        
        Returns:
            List of recommendation strings
        """
        recommendations = []
        metrics = analysis['metrics']
        
        # Complexity recommendations
        if metrics['max_function_complexity'] > 10:
            recommendations.append(
                f"High complexity detected (max: {metrics['max_function_complexity']}). "
                "Consider refactoring complex functions into smaller units."
            )
        
        if metrics['average_function_complexity'] > 5:
            recommendations.append(
                f"Average complexity is {metrics['average_function_complexity']}. "
                "Aim to keep functions simple and focused."
            )
        
        # Function recommendations
        if metrics['num_functions'] > 20:
            recommendations.append(
                f"Large number of functions ({metrics['num_functions']}). "
                "Consider organizing into classes or modules."
            )
        
        # Code smell recommendations
        high_priority_smells = [s for s in analysis['code_smells'] if s['severity'] in ['high', 'critical']]
        if high_priority_smells:
            recommendations.append(
                f"Found {len(high_priority_smells)} high-priority code quality issues. "
                "Address these first to improve maintainability."
            )
        
        # Documentation recommendation
        functions_without_docs = [f for f in analysis.get('functions', []) if not f.get('has_docstring')]
        if len(functions_without_docs) > len(analysis.get('functions', [])) * 0.5:
            recommendations.append(
                "Many functions lack documentation. Add docstrings to improve code maintainability."
            )
        
        logger.info(f"Generated {len(recommendations)} recommendations")
        return recommendations
