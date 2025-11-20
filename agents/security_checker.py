"""SecurityCheckerAgent - Scans for security vulnerabilities.

This agent specializes in:
- Security vulnerability detection
- Sensitive data exposure checks
- Input validation analysis
- Security best practices verification
"""

from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class SecurityCheckerAgent:
    """Agent specialized in security vulnerability detection.
    
    This agent uses custom tools and AI to:
    1. Scan for common security vulnerabilities
    2. Detect hardcoded secrets
    3. Identify injection vulnerabilities
    4. Check for insecure function usage
    5. Validate input handling
    """
    
    def __init__(self, client, code_tools):
        """Initialize the SecurityCheckerAgent.
        
        Args:
            client: Google GenAI client for LLM access
            code_tools: CodeAnalysisTools instance
        """
        self.client = client
        self.code_tools = code_tools
        self.model_name = "gemini-2.0-flash-exp"
        logger.info(f"SecurityCheckerAgent initialized with model: {self.model_name}")
    
    def check(self, code: str, language: str = "python", 
              context: Optional[Dict] = None) -> Dict[str, Any]:
        """Perform comprehensive security check.
        
        Args:
            code: Source code to check
            language: Programming language
            context: Optional context from previous agents
        
        Returns:
            Dictionary containing security check results
        """
        logger.info(f"Starting security check for {language} code")
        
        results = {
            'status': 'success',
            'language': language,
            'vulnerabilities': [],
            'risk_level': 'unknown',
            'summary': '',
            'issues': []
        }
        
        try:
            # Scan for security vulnerabilities
            security_issues = self.code_tools.scan_security(code, language)
            results['vulnerabilities'] = [
                {
                    'severity': issue.severity,
                    'type': issue.issue_type,
                    'line': issue.line_number,
                    'description': issue.description,
                    'recommendation': issue.recommendation
                }
                for issue in security_issues
            ]
            results['issues'] = results['vulnerabilities']
            logger.info(f"Detected {len(security_issues)} security issues")
            
            # Calculate overall risk level
            risk_level = self._calculate_risk_level(security_issues)
            results['risk_level'] = risk_level
            logger.info(f"Overall risk level: {risk_level}")
            
            # Generate AI-powered security analysis
            summary = self._generate_ai_security_analysis(code, results, context, language)
            results['summary'] = summary
            
            # Generate security recommendations
            results['recommendations'] = self._generate_security_recommendations(results)
            
            # Add security score
            results['security_score'] = self._calculate_security_score(security_issues)
            
            logger.info("Security check completed successfully")
            
        except Exception as e:
            logger.error(f"Error during security check: {e}")
            results['status'] = 'error'
            results['error'] = str(e)
        
        return results
    
    def _calculate_risk_level(self, security_issues: List) -> str:
        """Calculate overall risk level based on vulnerabilities.
        
        Args:
            security_issues: List of SecurityIssue objects
        
        Returns:
            Risk level string: 'critical', 'high', 'medium', 'low', 'none'
        """
        if not security_issues:
            return 'none'
        
        severity_counts = {
            'critical': sum(1 for issue in security_issues if issue.severity == 'critical'),
            'high': sum(1 for issue in security_issues if issue.severity == 'high'),
            'medium': sum(1 for issue in security_issues if issue.severity == 'medium'),
            'low': sum(1 for issue in security_issues if issue.severity == 'low')
        }
        
        if severity_counts['critical'] > 0:
            return 'critical'
        elif severity_counts['high'] > 0:
            return 'high'
        elif severity_counts['medium'] > 0:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_security_score(self, security_issues: List) -> int:
        """Calculate security score (0-100, higher is better).
        
        Args:
            security_issues: List of SecurityIssue objects
        
        Returns:
            Security score integer
        """
        base_score = 100
        
        # Deduct points based on severity
        for issue in security_issues:
            if issue.severity == 'critical':
                base_score -= 25
            elif issue.severity == 'high':
                base_score -= 15
            elif issue.severity == 'medium':
                base_score -= 8
            elif issue.severity == 'low':
                base_score -= 3
        
        return max(0, base_score)
    
    def _generate_ai_security_analysis(self, code: str, analysis: Dict, 
                                      context: Optional[Dict], language: str) -> str:
        """Generate AI-powered security analysis using Gemini.
        
        Args:
            code: Source code
            analysis: Security analysis results
            context: Context from previous agents
            language: Programming language
        
        Returns:
            AI-generated security summary
        """
        try:
            vulnerabilities = analysis['vulnerabilities']
            risk_level = analysis['risk_level']
            
            context_info = ""
            if context and 'metrics' in context:
                context_info = f"\nCode Metrics from previous analysis:\n- Functions: {context['metrics'].get('num_functions', 'N/A')}\n- Complexity: {context['metrics'].get('total_complexity', 'N/A')}"
            
            prompt = f"""You are a security expert. Analyze this {language} code for security vulnerabilities.

Security Scan Results:
- Vulnerabilities Found: {len(vulnerabilities)}
- Risk Level: {risk_level}
{context_info}

Detected Issues:
{chr(10).join([f"- {v['type']}: {v['description']}" for v in vulnerabilities[:5]])}

Provide a 2-3 sentence security assessment. Focus on:
1. Most critical vulnerabilities
2. Potential security impact
3. Urgency of fixes needed

Code snippet:
```{language}
{code[:800]}
```

Security Assessment:"""

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            summary = response.text.strip()
            logger.info("Generated AI security analysis")
            return summary
            
        except Exception as e:
            logger.warning(f"Error generating AI security analysis: {e}")
            return f"Security scan found {len(vulnerabilities)} vulnerabilities with {risk_level} risk level."
    
    def _generate_security_recommendations(self, analysis: Dict) -> List[str]:
        """Generate security recommendations.
        
        Args:
            analysis: Security analysis results
        
        Returns:
            List of recommendation strings
        """
        recommendations = []
        vulnerabilities = analysis['vulnerabilities']
        risk_level = analysis['risk_level']
        
        # Critical risk recommendations
        if risk_level == 'critical':
            recommendations.append(
                "URGENT: Critical security vulnerabilities detected. "
                "Address immediately before deploying to production."
            )
        
        # Group by vulnerability type
        vuln_types = {}
        for vuln in vulnerabilities:
            vuln_type = vuln['type']
            if vuln_type not in vuln_types:
                vuln_types[vuln_type] = []
            vuln_types[vuln_type].append(vuln)
        
        # Specific recommendations by type
        if 'sql_injection' in vuln_types:
            recommendations.append(
                f"SQL Injection vulnerabilities found ({len(vuln_types['sql_injection'])} instances). "
                "Use parameterized queries or an ORM to prevent injection attacks."
            )
        
        if 'hardcoded_secret' in vuln_types:
            recommendations.append(
                f"Hardcoded secrets detected ({len(vuln_types['hardcoded_secret'])} instances). "
                "Move secrets to environment variables or a secure vault."
            )
        
        if 'command_injection' in vuln_types:
            recommendations.append(
                f"Command injection risks found ({len(vuln_types['command_injection'])} instances). "
                "Avoid shell=True and validate all user inputs."
            )
        
        if 'insecure_function' in vuln_types:
            recommendations.append(
                f"Insecure functions detected ({len(vuln_types['insecure_function'])} instances). "
                "Replace eval/exec with safer alternatives."
            )
        
        # General recommendations
        if len(vulnerabilities) > 5:
            recommendations.append(
                "Multiple security issues detected. Conduct a thorough security review "
                "and consider implementing automated security scanning in CI/CD."
            )
        
        if not recommendations:
            recommendations.append(
                "No major security vulnerabilities detected. Continue following security best practices."
            )
        
        logger.info(f"Generated {len(recommendations)} security recommendations")
        return recommendations
