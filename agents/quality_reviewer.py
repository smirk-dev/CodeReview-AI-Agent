"""QualityReviewerAgent - Reviews code quality and provides improvements.

This agent specializes in:
- Overall code quality assessment
- Best practices verification
- Improvement suggestions
- Final review synthesis
"""

from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class QualityReviewerAgent:
    """Agent specialized in code quality review and improvement suggestions.
    
    This agent synthesizes findings from previous agents and:
    1. Assesses overall code quality
    2. Verifies best practices
    3. Provides actionable improvements
    4. Generates comprehensive recommendations
    5. Prioritizes issues by impact
    """
    
    def __init__(self, client, code_tools):
        """Initialize the QualityReviewerAgent.
        
        Args:
            client: Google GenAI client for LLM access
            code_tools: CodeAnalysisTools instance
        """
        self.client = client
        self.code_tools = code_tools
        self.model_name = "gemini-2.0-flash-exp"
        logger.info(f"QualityReviewerAgent initialized with model: {self.model_name}")
    
    def review(self, code: str, language: str = "python",
               context: Optional[Dict] = None) -> Dict[str, Any]:
        """Perform comprehensive quality review.
        
        Args:
            code: Source code to review
            language: Programming language
            context: Context from previous agents (analysis + security)
        
        Returns:
            Dictionary containing quality review results
        """
        logger.info(f"Starting quality review for {language} code")
        
        results = {
            'status': 'success',
            'language': language,
            'quality_score': 0,
            'quality_grade': 'Unknown',
            'strengths': [],
            'weaknesses': [],
            'improvements': [],
            'summary': '',
            'issues': [],
            'recommendations': []
        }
        
        try:
            # Calculate quality score based on all available information
            quality_score, grade = self._calculate_quality_score(context)
            results['quality_score'] = quality_score
            results['quality_grade'] = grade
            logger.info(f"Quality score: {quality_score}/100 (Grade: {grade})")
            
            # Identify strengths and weaknesses
            strengths, weaknesses = self._identify_strengths_weaknesses(context)
            results['strengths'] = strengths
            results['weaknesses'] = weaknesses
            
            # Generate improvement suggestions
            improvements = self._generate_improvements(code, context, language)
            results['improvements'] = improvements
            results['issues'] = improvements  # For consistency with other agents
            
            # Generate AI-powered comprehensive review
            summary = self._generate_ai_comprehensive_review(
                code, results, context, language
            )
            results['summary'] = summary
            
            # Generate final recommendations
            recommendations = self._generate_final_recommendations(results, context)
            results['recommendations'] = recommendations
            
            # Add priority matrix
            results['priority_matrix'] = self._create_priority_matrix(context)
            
            logger.info("Quality review completed successfully")
            
        except Exception as e:
            logger.error(f"Error during quality review: {e}")
            results['status'] = 'error'
            results['error'] = str(e)
        
        return results
    
    def _calculate_quality_score(self, context: Optional[Dict]) -> tuple:
        """Calculate overall quality score (0-100).
        
        Args:
            context: Combined context from previous agents
        
        Returns:
            Tuple of (score, grade)
        """
        score = 100
        
        if not context:
            return (score, 'A')
        
        # Deduct points for complexity issues
        if 'analysis' in context and 'metrics' in context['analysis']:
            metrics = context['analysis']['metrics']
            
            # High complexity penalty
            if metrics.get('max_function_complexity', 0) > 15:
                score -= 15
            elif metrics.get('max_function_complexity', 0) > 10:
                score -= 8
            
            # Average complexity penalty
            if metrics.get('average_function_complexity', 0) > 7:
                score -= 10
            elif metrics.get('average_function_complexity', 0) > 5:
                score -= 5
            
            # Code smells penalty
            code_smells = context['analysis'].get('code_smells', [])
            score -= min(len(code_smells) * 2, 20)
        
        # Deduct points for security issues
        if 'security' in context:
            risk_level = context['security'].get('risk_level', 'none')
            security_score = context['security'].get('security_score', 100)
            
            # Use security score in calculation
            score = int((score + security_score) / 2)
        
        # Ensure score is in valid range
        score = max(0, min(100, score))
        
        # Assign grade
        if score >= 90:
            grade = 'A'
        elif score >= 80:
            grade = 'B'
        elif score >= 70:
            grade = 'C'
        elif score >= 60:
            grade = 'D'
        else:
            grade = 'F'
        
        return (score, grade)
    
    def _identify_strengths_weaknesses(self, context: Optional[Dict]) -> tuple:
        """Identify code strengths and weaknesses.
        
        Args:
            context: Context from previous agents
        
        Returns:
            Tuple of (strengths list, weaknesses list)
        """
        strengths = []
        weaknesses = []
        
        if not context:
            return (strengths, weaknesses)
        
        # Analyze from code analysis context
        if 'analysis' in context:
            analysis = context['analysis']
            metrics = analysis.get('metrics', {})
            
            # Check complexity
            if metrics.get('average_function_complexity', 0) < 5:
                strengths.append("Low cyclomatic complexity - code is maintainable")
            elif metrics.get('average_function_complexity', 0) > 7:
                weaknesses.append("High cyclomatic complexity - difficult to maintain")
            
            # Check code organization
            if metrics.get('num_classes', 0) > 0:
                strengths.append("Uses object-oriented structure")
            
            # Check documentation
            functions = analysis.get('functions', [])
            if functions:
                documented = sum(1 for f in functions if f.get('has_docstring'))
                doc_ratio = documented / len(functions)
                if doc_ratio > 0.7:
                    strengths.append(f"Well documented ({int(doc_ratio*100)}% functions have docstrings)")
                elif doc_ratio < 0.3:
                    weaknesses.append(f"Poor documentation ({int(doc_ratio*100)}% functions have docstrings)")
            
            # Check code smells
            code_smells = analysis.get('code_smells', [])
            if len(code_smells) == 0:
                strengths.append("No code smells detected")
            elif len(code_smells) > 5:
                weaknesses.append(f"Multiple code quality issues ({len(code_smells)} issues)")
        
        # Analyze from security context
        if 'security' in context:
            security = context['security']
            risk_level = security.get('risk_level', 'none')
            
            if risk_level == 'none':
                strengths.append("No security vulnerabilities detected")
            elif risk_level in ['critical', 'high']:
                weaknesses.append(f"Security risk level: {risk_level}")
        
        return (strengths, weaknesses)
    
    def _generate_improvements(self, code: str, context: Optional[Dict], 
                              language: str) -> List[Dict[str, Any]]:
        """Generate specific improvement suggestions.
        
        Args:
            code: Source code
            context: Context from previous agents
            language: Programming language
        
        Returns:
            List of improvement dictionaries
        """
        improvements = []
        
        if not context:
            return improvements
        
        # Improvements from code analysis
        if 'analysis' in context:
            analysis = context['analysis']
            
            # Add improvements for each code smell
            for smell in analysis.get('code_smells', []):
                improvements.append({
                    'category': 'Code Quality',
                    'severity': smell.get('severity', 'medium'),
                    'line': smell.get('line'),
                    'issue': smell.get('description'),
                    'improvement': smell.get('suggestion'),
                    'priority': self._calculate_priority(smell.get('severity'))
                })
        
        # Improvements from security
        if 'security' in context:
            security = context['security']
            
            # Add improvements for each vulnerability
            for vuln in security.get('vulnerabilities', []):
                improvements.append({
                    'category': 'Security',
                    'severity': vuln.get('severity', 'medium'),
                    'line': vuln.get('line'),
                    'issue': vuln.get('description'),
                    'improvement': vuln.get('recommendation'),
                    'priority': self._calculate_priority(vuln.get('severity'))
                })
        
        # Sort by priority
        improvements.sort(key=lambda x: x['priority'], reverse=True)
        
        logger.info(f"Generated {len(improvements)} improvement suggestions")
        return improvements
    
    def _calculate_priority(self, severity: str) -> int:
        """Calculate priority score from severity.
        
        Args:
            severity: Severity level string
        
        Returns:
            Priority score (higher = more important)
        """
        priority_map = {
            'critical': 4,
            'high': 3,
            'medium': 2,
            'low': 1
        }
        return priority_map.get(severity, 0)
    
    def _generate_ai_comprehensive_review(self, code: str, results: Dict,
                                         context: Optional[Dict], language: str) -> str:
        """Generate AI-powered comprehensive review using Gemini.
        
        Args:
            code: Source code
            results: Quality review results so far
            context: Context from previous agents
            language: Programming language
        
        Returns:
            AI-generated comprehensive review
        """
        try:
            quality_score = results['quality_score']
            grade = results['quality_grade']
            strengths = results['strengths']
            weaknesses = results['weaknesses']
            
            # Build context summary
            context_summary = ""
            if context:
                if 'analysis' in context:
                    metrics = context['analysis'].get('metrics', {})
                    context_summary += f"\nCode Analysis:\n- Lines: {metrics.get('lines_of_code')}\n- Functions: {metrics.get('num_functions')}\n- Complexity: {metrics.get('total_complexity')}"
                
                if 'security' in context:
                    risk = context['security'].get('risk_level')
                    context_summary += f"\n\nSecurity:\n- Risk Level: {risk}\n- Vulnerabilities: {len(context['security'].get('vulnerabilities', []))}"
            
            prompt = f"""You are a senior code reviewer. Provide a comprehensive final review of this {language} code.

Quality Assessment:
- Overall Score: {quality_score}/100 (Grade: {grade})
- Strengths: {len(strengths)}
- Weaknesses: {len(weaknesses)}
{context_summary}

Key Strengths:
{chr(10).join([f"✓ {s}" for s in strengths[:3]])}

Key Weaknesses:
{chr(10).join([f"✗ {w}" for w in weaknesses[:3]])}

Provide a 3-4 sentence final review. Focus on:
1. Overall assessment of code quality
2. Most impactful improvements needed
3. Readiness for production

Code snippet:
```{language}
{code[:700]}
```

Final Review:"""

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            summary = response.text.strip()
            logger.info("Generated AI comprehensive review")
            return summary
            
        except Exception as e:
            logger.warning(f"Error generating AI comprehensive review: {e}")
            return f"Code quality grade: {grade} ({quality_score}/100). {len(strengths)} strengths, {len(weaknesses)} areas for improvement."
    
    def _generate_final_recommendations(self, results: Dict, 
                                       context: Optional[Dict]) -> List[str]:
        """Generate final prioritized recommendations.
        
        Args:
            results: Quality review results
            context: Context from all agents
        
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Top priority based on grade
        grade = results['quality_grade']
        if grade in ['D', 'F']:
            recommendations.append(
                "⚠️ PRIORITY: Code requires significant refactoring before production deployment."
            )
        elif grade == 'C':
            recommendations.append(
                "Code needs improvement. Address high-priority issues before deployment."
            )
        
        # Recommendations from high-priority improvements
        high_priority_improvements = [
            imp for imp in results.get('improvements', [])
            if imp['priority'] >= 3
        ]
        
        if high_priority_improvements:
            security_high = [i for i in high_priority_improvements if i['category'] == 'Security']
            quality_high = [i for i in high_priority_improvements if i['category'] == 'Code Quality']
            
            if security_high:
                recommendations.append(
                    f"🔒 Address {len(security_high)} critical security issues immediately."
                )
            
            if quality_high:
                recommendations.append(
                    f"🔧 Refactor {len(quality_high)} high-priority code quality issues."
                )
        
        # Specific recommendations from weaknesses
        weaknesses = results.get('weaknesses', [])
        if any('complexity' in w.lower() for w in weaknesses):
            recommendations.append(
                "📊 Reduce code complexity by extracting methods and simplifying logic."
            )
        
        if any('documentation' in w.lower() for w in weaknesses):
            recommendations.append(
                "📝 Improve code documentation with comprehensive docstrings."
            )
        
        # Positive reinforcement
        if grade in ['A', 'B'] and len(high_priority_improvements) == 0:
            recommendations.append(
                "✅ Code is in good shape! Minor improvements would make it excellent."
            )
        
        logger.info(f"Generated {len(recommendations)} final recommendations")
        return recommendations
    
    def _create_priority_matrix(self, context: Optional[Dict]) -> Dict[str, List]:
        """Create a priority matrix of all issues.
        
        Args:
            context: Context from all agents
        
        Returns:
            Dictionary with issues categorized by priority
        """
        matrix = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': []
        }
        
        if not context:
            return matrix
        
        # Collect all issues
        if 'analysis' in context:
            for smell in context['analysis'].get('code_smells', []):
                severity = smell.get('severity', 'medium')
                matrix[severity].append({
                    'type': 'code_quality',
                    'description': smell.get('description'),
                    'line': smell.get('line')
                })
        
        if 'security' in context:
            for vuln in context['security'].get('vulnerabilities', []):
                severity = vuln.get('severity', 'medium')
                matrix[severity].append({
                    'type': 'security',
                    'description': vuln.get('description'),
                    'line': vuln.get('line')
                })
        
        return matrix
