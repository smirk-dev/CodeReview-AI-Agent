"""CodeReview-AI-Agent: Multi-agent AI system for automated code review

This is the main entry point for the CodeReview-AI-Agent system.
It demonstrates a multi-agent architecture using Google's ADK with:
- Sequential agent workflow
- Custom tools for code analysis
- Session management and memory
- Integration with Gemini models

Kaggle Agents Intensive Capstone Project 2025
Track: Enterprise Agents
"""

import os
import sys
from typing import Dict, List, Optional
import json
from datetime import datetime

# Import Google GenAI components
try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Error: Please install google-genai: pip install google-genai")
    sys.exit(1)

# Simple session service implementation (ADK-like interface)
class InMemorySessionService:
    """Simple in-memory session service."""
    def __init__(self):
        self.sessions = {}

# Import custom agents and tools
from agents.code_analyzer import CodeAnalyzerAgent
from agents.security_checker import SecurityCheckerAgent  
from agents.quality_reviewer import QualityReviewerAgent
from tools.code_tools import CodeAnalysisTools
from utils.session_manager import SessionManager
from utils.memory_bank import MemoryBank
from utils.observability import get_observability
from utils.rich_output import rich_output
from utils.report_generator import report_generator
from utils.retry_handler import with_retry, GracefulDegradation
from utils.multi_language import multi_language_analyzer
from utils.github_integration import github_integration, GitHubActionsHelper


class CodeReviewOrchestrator:
    """Main orchestrator for the multi-agent code review system.
    
    This class manages the sequential flow of agents:
    1. CodeAnalyzerAgent - Performs initial code analysis
    2. SecurityCheckerAgent - Checks for security vulnerabilities
    3. QualityReviewerAgent - Reviews code quality and suggests improvements
    
    It also manages shared state, memory, and session persistence.
    """
    
    def __init__(self, api_key: str = None):
        """Initialize the orchestrator with all agents and tools.
        
        Args:
            api_key: Google AI API key (falls back to GOOGLE_AI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('GOOGLE_AI_API_KEY')
        if not self.api_key:
            raise ValueError("API key required. Set GOOGLE_AI_API_KEY or pass api_key")
        
        # Initialize observability
        self.observability = get_observability()
        self.logger = self.observability.get_logger(__name__)
        
        # Initialize client
        self.client = genai.Client(api_key=self.api_key)
        
        # Initialize session management and memory
        self.session_service = InMemorySessionService()
        self.session_manager = SessionManager(self.session_service)
        self.memory_bank = MemoryBank()
        
        # Initialize tools
        self.code_tools = CodeAnalysisTools()
        
        # Initialize specialized agents
        self.code_analyzer = CodeAnalyzerAgent(self.client, self.code_tools)
        self.security_checker = SecurityCheckerAgent(self.client, self.code_tools)
        self.quality_reviewer = QualityReviewerAgent(self.client, self.code_tools)
        
        self.logger.info("CodeReview-AI-Agent system initialized")
        rich_output.print_header(
            "CodeReview-AI-Agent System",
            "Multi-Agent Code Review with AI"
        )
        rich_output.print_success("CodeReview-AI-Agent system initialized")
        rich_output.print_success("Using Gemini models for multi-agent workflow")
    
    def review_code(self, code: str, language: str = "python", 
                   session_id: Optional[str] = None) -> Dict:
        """Execute the full code review pipeline.
        
        This method orchestrates the sequential flow of three specialized agents:
        1. CodeAnalyzerAgent: Analyzes code structure, complexity, patterns
        2. SecurityCheckerAgent: Identifies security vulnerabilities and risks
        3. QualityReviewerAgent: Provides quality assessment and improvements
        
        Args:
            code: Source code to review
            language: Programming language (default: python)
            session_id: Optional session ID for continuing previous reviews
        
        Returns:
            Dict containing comprehensive review results from all agents
        """
        rich_output.print_header(
            "Multi-Agent Code Review Pipeline",
            f"Language: {language}"
        )
        
        self.logger.info(f"Starting code review pipeline for {language}")
        
        # Auto-detect language if needed
        if language == "auto":
            language = multi_language_analyzer.detect_language(code)
            rich_output.print_info(f"Detected language: {language}")
        
        # Create or resume session
        session = self.session_manager.get_or_create_session(session_id)
        rich_output.print_info(f"Session ID: {session['id']}")
        
        # Store code in memory for all agents to access
        self.memory_bank.store("current_code", {
            "code": code,
            "language": language,
            "timestamp": datetime.now().isoformat()
        })
        
        results = {
            "session_id": session['id'],
            "language": language,
            "timestamp": datetime.now().isoformat(),
            "agents": {}
        }
        
        # Agent 1: Code Analysis
        rich_output.print_agent_start("CodeAnalyzerAgent", "[1/3]")
        try:
            with self.observability.trace_operation("code_analysis", language=language):
                analysis_result = self.code_analyzer.analyze(code, language)
            results["agents"]["code_analyzer"] = analysis_result
            self.memory_bank.store("analysis_result", analysis_result)
            rich_output.print_success("Code analysis complete")
            self.logger.info("Code analysis completed successfully")
        except Exception as e:
            rich_output.print_error(f"Code analysis failed: {str(e)}")
            self.logger.error(f"Code analysis failed: {e}", exc_info=True)
            results["agents"]["code_analyzer"] = {"error": str(e)}
        
        # Agent 2: Security Check
        rich_output.print_agent_start("SecurityCheckerAgent", "[2/3]")
        try:
            with self.observability.trace_operation("security_check", language=language):
                # Pass previous agent results for context
                security_result = self.security_checker.check(
                    code, 
                    language,
                    context=self.memory_bank.get("analysis_result")
                )
            results["agents"]["security_checker"] = security_result
            self.memory_bank.store("security_result", security_result)
            rich_output.print_success("Security check complete")
            self.logger.info("Security check completed successfully")
        except Exception as e:
            rich_output.print_error(f"Security check failed: {str(e)}")
            self.logger.error(f"Security check failed: {e}", exc_info=True)
            results["agents"]["security_checker"] = {"error": str(e)}
        
        # Agent 3: Quality Review
        rich_output.print_agent_start("QualityReviewerAgent", "[3/3]")
        try:
            with self.observability.trace_operation("quality_review", language=language):
                # Provide full context from previous agents
                quality_result = self.quality_reviewer.review(
                    code,
                    language,
                    context={
                        "analysis": self.memory_bank.get("analysis_result"),
                        "security": self.memory_bank.get("security_result")
                    }
                )
            results["agents"]["quality_reviewer"] = quality_result
            rich_output.print_success("Quality review complete")
            self.logger.info("Quality review completed successfully")
        except Exception as e:
            rich_output.print_error(f"Quality review failed: {str(e)}")
            self.logger.error(f"Quality review failed: {e}", exc_info=True)
            results["agents"]["quality_reviewer"] = {"error": str(e)}
        
        # Generate final summary
        results["summary"] = self._generate_summary(results)
        
        # Update session with results
        self.session_manager.update_session(session['id'], results)
        
        # Display rich results
        rich_output.print_results(results)
        
        # Generate reports
        session_short = results['session_id'][:8]
        
        # Save JSON
        json_file = f"review_results_{session_short}.json"
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Generate HTML report
        html_file = f"review_report_{session_short}.html"
        report_generator.generate_html_report(results, html_file)
        rich_output.print_success(f"HTML report: {html_file}")
        
        # Generate Markdown for GitHub
        md_file = f"review_report_{session_short}.md"
        report_generator.generate_markdown_report(results, md_file)
        rich_output.print_success(f"Markdown report: {md_file}")
        
        # Generate SARIF for IDEs
        sarif_file = f"review_report_{session_short}.sarif"
        report_generator.generate_sarif_report(results, sarif_file)
        rich_output.print_success(f"SARIF report: {sarif_file}")
        
        return results
    
    def _generate_summary(self, results: Dict) -> Dict:
        """Generate a comprehensive summary from all agent results."""
        summary = {
            "total_agents": len(results["agents"]),
            "successful_agents": sum(1 for r in results["agents"].values() 
                                   if "error" not in r),
            "issues_found": 0,
            "severity_levels": {},
            "recommendations_count": 0
        }
        
        # Aggregate findings from all agents
        for agent_name, agent_result in results["agents"].items():
            if "error" in agent_result:
                continue
            if "issues" in agent_result:
                summary["issues_found"] += len(agent_result["issues"])
            if "recommendations" in agent_result:
                summary["recommendations_count"] += len(agent_result["recommendations"])
        
        return summary
    
    def get_session_history(self, session_id: str) -> Optional[Dict]:
        """Retrieve historical review data for a session."""
        return self.session_manager.get_session(session_id)


def main():
    """Main function demonstrating the CodeReview-AI-Agent system."""
    
    # Example code to review
    sample_code = '''def calculate_user_score(user_data):
    # Calculate user score from raw data
    score = 0
    for item in user_data:
        score += item['points'] * item['multiplier']
    return score

def process_payment(amount, card_number, cvv):
    # Process payment
    print(f"Processing ${amount} for card {card_number}")
    return {"status": "success", "card": card_number}
'''
    
    try:
        # Initialize orchestrator
        orchestrator = CodeReviewOrchestrator()
        
        # Run code review
        results = orchestrator.review_code(sample_code, language="python")
        
        print(f"\n💾 Multiple report formats generated!")
        print(f"   - JSON: review_results_{results['session_id'][:8]}.json")
        print(f"   - HTML: review_report_{results['session_id'][:8]}.html")
        print(f"   - Markdown: review_report_{results['session_id'][:8]}.md")
        print(f"   - SARIF: review_report_{results['session_id'][:8]}.sarif")
        
    except Exception as e:
        rich_output.print_error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
