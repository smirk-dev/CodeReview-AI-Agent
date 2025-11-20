"""
Report Generation Module
Generates HTML, Markdown, and SARIF format reports
"""

import json
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path
from jinja2 import Template

class ReportGenerator:
    """Generates review reports in multiple formats"""
    
    def __init__(self):
        self.html_template = self._get_html_template()
        self.markdown_template = self._get_markdown_template()
    
    def _get_html_template(self) -> Template:
        """Get HTML template for reports"""
        html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Code Review Report - {{ session_id }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            line-height: 1.6;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { opacity: 0.9; font-size: 1.1em; }
        .content { padding: 40px; }
        .section {
            margin-bottom: 40px;
            padding: 30px;
            background: #f8f9fa;
            border-radius: 12px;
            border-left: 4px solid #667eea;
        }
        .section h2 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.8em;
        }
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
        }
        .metric-card .value {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin: 10px 0;
        }
        .metric-card .label {
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .quality-score {
            text-align: center;
            padding: 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 12px;
            margin: 30px 0;
        }
        .quality-score .score {
            font-size: 5em;
            font-weight: bold;
            margin: 20px 0;
        }
        .quality-score .grade {
            font-size: 2em;
            opacity: 0.9;
        }
        .issue {
            background: white;
            padding: 20px;
            margin: 15px 0;
            border-radius: 8px;
            border-left: 4px solid;
        }
        .issue.critical { border-left-color: #dc3545; }
        .issue.high { border-left-color: #fd7e14; }
        .issue.medium { border-left-color: #ffc107; }
        .issue.low { border-left-color: #17a2b8; }
        .issue .severity {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .issue.critical .severity { background: #dc3545; color: white; }
        .issue.high .severity { background: #fd7e14; color: white; }
        .issue.medium .severity { background: #ffc107; color: black; }
        .issue.low .severity { background: #17a2b8; color: white; }
        .recommendation {
            background: #fff3cd;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid #ffc107;
        }
        .recommendation:before {
            content: "💡 ";
            font-size: 1.2em;
        }
        .footer {
            text-align: center;
            padding: 30px;
            color: #666;
            border-top: 1px solid #eee;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            border-radius: 8px;
            overflow: hidden;
        }
        th, td {
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        th {
            background: #667eea;
            color: white;
            font-weight: 600;
        }
        tr:hover { background: #f8f9fa; }
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }
        .badge.success { background: #d4edda; color: #155724; }
        .badge.warning { background: #fff3cd; color: #856404; }
        .badge.error { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Code Review Report</h1>
            <p>Multi-Agent AI Code Analysis</p>
            <p style="font-size: 0.9em; margin-top: 10px;">Session: {{ session_id }}</p>
            <p style="font-size: 0.9em;">{{ timestamp }}</p>
        </div>
        
        <div class="content">
            {% if quality_score %}
            <div class="quality-score">
                <div>Overall Quality</div>
                <div class="score">{{ quality_score }}/100</div>
                <div class="grade">Grade: {{ quality_grade }}</div>
            </div>
            {% endif %}
            
            <div class="section">
                <h2>📊 Summary</h2>
                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="label">Total Agents</div>
                        <div class="value">{{ summary.total_agents }}</div>
                    </div>
                    <div class="metric-card">
                        <div class="label">Successful</div>
                        <div class="value">{{ summary.successful_agents }}</div>
                    </div>
                    <div class="metric-card">
                        <div class="label">Issues Found</div>
                        <div class="value">{{ summary.issues_found }}</div>
                    </div>
                    <div class="metric-card">
                        <div class="label">Recommendations</div>
                        <div class="value">{{ summary.recommendations_count }}</div>
                    </div>
                </div>
            </div>
            
            {% if metrics %}
            <div class="section">
                <h2>📈 Code Metrics</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Metric</th>
                            <th>Value</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for key, value in metrics.items() %}
                        <tr>
                            <td>{{ key|replace("_", " ")|title }}</td>
                            <td><strong>{{ value }}</strong></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% endif %}
            
            {% if issues %}
            <div class="section">
                <h2>🔍 Issues Found</h2>
                {% for issue in issues %}
                <div class="issue {{ issue.severity|lower }}">
                    <span class="severity">{{ issue.severity|upper }}</span>
                    <h3>{{ issue.type }}</h3>
                    <p><strong>Line {{ issue.line }}:</strong> {{ issue.description }}</p>
                    {% if issue.suggestion %}
                    <p style="margin-top: 10px; color: #666;">💡 {{ issue.suggestion }}</p>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
            {% endif %}
            
            {% if recommendations %}
            <div class="section">
                <h2>💡 Recommendations</h2>
                {% for rec in recommendations %}
                <div class="recommendation">{{ rec }}</div>
                {% endfor %}
            </div>
            {% endif %}
            
            {% if strengths %}
            <div class="section">
                <h2>✨ Strengths</h2>
                <ul style="list-style: none; padding: 0;">
                    {% for strength in strengths %}
                    <li style="padding: 10px; margin: 5px 0; background: white; border-radius: 8px;">
                        ✓ {{ strength }}
                    </li>
                    {% endfor %}
                </ul>
            </div>
            {% endif %}
        </div>
        
        <div class="footer">
            <p><strong>CodeReview-AI-Agent</strong> - Multi-Agent Code Review System</p>
            <p style="margin-top: 10px; font-size: 0.9em;">Powered by Google Gemini & ADK</p>
        </div>
    </div>
</body>
</html>
"""
        return Template(html)
    
    def _get_markdown_template(self) -> Template:
        """Get Markdown template for GitHub"""
        markdown = """# 🤖 Code Review Report

**Session:** `{{ session_id }}`  
**Timestamp:** {{ timestamp }}  
**Language:** {{ language }}

---

## 📊 Summary

| Metric | Value |
|--------|-------|
| Total Agents | {{ summary.total_agents }} |
| Successful | {{ summary.successful_agents }} |
| Issues Found | {{ summary.issues_found }} |
| Recommendations | {{ summary.recommendations_count }} |

{% if quality_score %}
## 🎯 Quality Score

**{{ quality_score }}/100** (Grade: **{{ quality_grade }}**)

{% endif %}

{% if metrics %}
## 📈 Code Metrics

| Metric | Value |
|--------|-------|
{% for key, value in metrics.items() %}
| {{ key|replace("_", " ")|title }} | {{ value }} |
{% endfor %}

{% endif %}

{% if issues %}
## 🔍 Issues Found

{% for issue in issues %}
### {{ issue.severity|upper }}: {{ issue.type }}

**Line {{ issue.line }}:** {{ issue.description }}

{% if issue.suggestion %}
💡 **Suggestion:** {{ issue.suggestion }}
{% endif %}

---
{% endfor %}
{% endif %}

{% if recommendations %}
## 💡 Recommendations

{% for rec in recommendations %}
- {{ rec }}
{% endfor %}
{% endif %}

{% if strengths %}
## ✨ Strengths

{% for strength in strengths %}
- ✓ {{ strength }}
{% endfor %}
{% endif %}

---

*Generated by **CodeReview-AI-Agent** - Multi-Agent Code Review System*  
*Powered by Google Gemini & ADK*
"""
        return Template(markdown)
    
    def generate_html_report(self, results: Dict[str, Any], output_path: str = None) -> str:
        """Generate HTML report from review results"""
        # Extract data
        context = {
            'session_id': results.get('session_id', 'N/A'),
            'timestamp': results.get('timestamp', datetime.now().isoformat()),
            'language': results.get('language', 'unknown'),
            'summary': results.get('summary', {}),
            'quality_score': None,
            'quality_grade': None,
            'metrics': {},
            'issues': [],
            'recommendations': [],
            'strengths': []
        }
        
        # Extract quality score
        if 'agents' in results and 'quality_reviewer' in results['agents']:
            quality = results['agents']['quality_reviewer']
            context['quality_score'] = quality.get('quality_score')
            context['quality_grade'] = quality.get('quality_grade')
            context['strengths'] = quality.get('strengths', [])
        
        # Extract metrics
        if 'agents' in results and 'code_analyzer' in results['agents']:
            context['metrics'] = results['agents']['code_analyzer'].get('metrics', {})
        
        # Collect all issues and recommendations
        if 'agents' in results:
            for agent_name, agent_data in results['agents'].items():
                if 'issues' in agent_data:
                    context['issues'].extend(agent_data['issues'])
                if 'recommendations' in agent_data:
                    context['recommendations'].extend(agent_data['recommendations'])
        
        # Generate HTML
        html_content = self.html_template.render(**context)
        
        # Save to file if path provided
        if output_path:
            Path(output_path).write_text(html_content, encoding='utf-8')
        
        return html_content
    
    def generate_markdown_report(self, results: Dict[str, Any], output_path: str = None) -> str:
        """Generate Markdown report for GitHub"""
        # Extract data (same as HTML)
        context = {
            'session_id': results.get('session_id', 'N/A'),
            'timestamp': results.get('timestamp', datetime.now().isoformat()),
            'language': results.get('language', 'unknown'),
            'summary': results.get('summary', {}),
            'quality_score': None,
            'quality_grade': None,
            'metrics': {},
            'issues': [],
            'recommendations': [],
            'strengths': []
        }
        
        if 'agents' in results and 'quality_reviewer' in results['agents']:
            quality = results['agents']['quality_reviewer']
            context['quality_score'] = quality.get('quality_score')
            context['quality_grade'] = quality.get('quality_grade')
            context['strengths'] = quality.get('strengths', [])
        
        if 'agents' in results and 'code_analyzer' in results['agents']:
            context['metrics'] = results['agents']['code_analyzer'].get('metrics', {})
        
        if 'agents' in results:
            for agent_name, agent_data in results['agents'].items():
                if 'issues' in agent_data:
                    context['issues'].extend(agent_data['issues'])
                if 'recommendations' in agent_data:
                    context['recommendations'].extend(agent_data['recommendations'])
        
        # Generate Markdown
        markdown_content = self.markdown_template.render(**context)
        
        if output_path:
            Path(output_path).write_text(markdown_content, encoding='utf-8')
        
        return markdown_content
    
    def generate_sarif_report(self, results: Dict[str, Any], output_path: str = None) -> Dict[str, Any]:
        """Generate SARIF format report for IDE integration"""
        sarif = {
            "version": "2.1.0",
            "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "CodeReview-AI-Agent",
                            "version": "1.0.0",
                            "informationUri": "https://github.com/smirk-dev/CodeReview-AI-Agent",
                            "rules": []
                        }
                    },
                    "results": []
                }
            ]
        }
        
        # Convert issues to SARIF format
        rule_id = 0
        if 'agents' in results:
            for agent_name, agent_data in results['agents'].items():
                if 'issues' in agent_data:
                    for issue in agent_data['issues']:
                        rule_id += 1
                        rule_id_str = f"CR{rule_id:04d}"
                        
                        # Add rule
                        sarif["runs"][0]["tool"]["driver"]["rules"].append({
                            "id": rule_id_str,
                            "name": issue.get('type', 'Unknown'),
                            "shortDescription": {
                                "text": issue.get('description', '')
                            },
                            "fullDescription": {
                                "text": issue.get('suggestion', issue.get('description', ''))
                            },
                            "defaultConfiguration": {
                                "level": self._severity_to_sarif_level(issue.get('severity', 'low'))
                            }
                        })
                        
                        # Add result
                        sarif["runs"][0]["results"].append({
                            "ruleId": rule_id_str,
                            "level": self._severity_to_sarif_level(issue.get('severity', 'low')),
                            "message": {
                                "text": issue.get('description', '')
                            },
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {
                                            "uri": "code.py"
                                        },
                                        "region": {
                                            "startLine": issue.get('line', 1)
                                        }
                                    }
                                }
                            ]
                        })
        
        if output_path:
            Path(output_path).write_text(json.dumps(sarif, indent=2), encoding='utf-8')
        
        return sarif
    
    def _severity_to_sarif_level(self, severity: str) -> str:
        """Convert severity to SARIF level"""
        mapping = {
            'critical': 'error',
            'high': 'error',
            'medium': 'warning',
            'low': 'note'
        }
        return mapping.get(severity.lower(), 'note')

# Global instance
report_generator = ReportGenerator()
