"""Evaluation framework for assessing agent performance.

This module provides evaluation capabilities:
- Agent accuracy assessment
- Response quality metrics
- Performance benchmarking
- Test case management
"""

import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class TestCase:
    """Test case for code review evaluation."""
    id: str
    name: str
    code: str
    language: str
    expected_issues: List[str]
    expected_severity: str
    description: str


@dataclass
class EvaluationResult:
    """Result of an evaluation run."""
    test_case_id: str
    test_case_name: str
    execution_time: float
    issues_found: int
    issues_expected: int
    accuracy_score: float
    quality_score: int
    passed: bool
    details: Dict[str, Any]


class AgentEvaluator:
    """Evaluates agent performance on test cases."""
    
    def __init__(self):
        """Initialize the evaluator."""
        self.test_cases: List[TestCase] = []
        self.results: List[EvaluationResult] = []
        logger.info("AgentEvaluator initialized")
    
    def add_test_case(self, test_case: TestCase):
        """Add a test case for evaluation.
        
        Args:
            test_case: TestCase instance
        """
        self.test_cases.append(test_case)
        logger.info(f"Added test case: {test_case.name}")
    
    def load_test_cases_from_file(self, filepath: str):
        """Load test cases from a JSON file.
        
        Args:
            filepath: Path to JSON file with test cases
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        for tc_data in data.get('test_cases', []):
            test_case = TestCase(**tc_data)
            self.add_test_case(test_case)
        
        logger.info(f"Loaded {len(self.test_cases)} test cases from {filepath}")
    
    def evaluate(self, orchestrator, test_case: TestCase) -> EvaluationResult:
        """Evaluate orchestrator on a single test case.
        
        Args:
            orchestrator: CodeReviewOrchestrator instance
            test_case: Test case to evaluate
        
        Returns:
            EvaluationResult
        """
        logger.info(f"Evaluating test case: {test_case.name}")
        
        start_time = time.time()
        
        try:
            # Run code review
            results = orchestrator.review_code(test_case.code, test_case.language)
            
            execution_time = time.time() - start_time
            
            # Count issues found
            issues_found = results.get('summary', {}).get('issues_found', 0)
            quality_score = results.get('agents', {}).get('quality_reviewer', {}).get('quality_score', 0)
            
            # Calculate accuracy (how well it matches expected issues)
            expected_count = len(test_case.expected_issues)
            accuracy_score = self._calculate_accuracy(results, test_case)
            
            # Determine if passed
            passed = accuracy_score >= 0.7 and quality_score > 0
            
            result = EvaluationResult(
                test_case_id=test_case.id,
                test_case_name=test_case.name,
                execution_time=execution_time,
                issues_found=issues_found,
                issues_expected=expected_count,
                accuracy_score=accuracy_score,
                quality_score=quality_score,
                passed=passed,
                details={
                    'results': results,
                    'expected_issues': test_case.expected_issues,
                    'expected_severity': test_case.expected_severity
                }
            )
            
            self.results.append(result)
            logger.info(f"Test case completed: {test_case.name} - {'PASSED' if passed else 'FAILED'}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error evaluating test case {test_case.name}: {e}")
            execution_time = time.time() - start_time
            
            result = EvaluationResult(
                test_case_id=test_case.id,
                test_case_name=test_case.name,
                execution_time=execution_time,
                issues_found=0,
                issues_expected=len(test_case.expected_issues),
                accuracy_score=0.0,
                quality_score=0,
                passed=False,
                details={'error': str(e)}
            )
            
            self.results.append(result)
            return result
    
    def _calculate_accuracy(self, results: Dict, test_case: TestCase) -> float:
        """Calculate accuracy score.
        
        Args:
            results: Review results
            test_case: Test case with expected results
        
        Returns:
            Accuracy score (0.0 to 1.0)
        """
        # Simple accuracy: ratio of found vs expected
        issues_found = results.get('summary', {}).get('issues_found', 0)
        expected_count = len(test_case.expected_issues)
        
        if expected_count == 0:
            return 1.0 if issues_found == 0 else 0.5
        
        # Calculate based on how close we are
        ratio = min(issues_found, expected_count) / expected_count
        
        # Check if we found the right types of issues
        found_types = set()
        for agent_result in results.get('agents', {}).values():
            if 'issues' in agent_result:
                for issue in agent_result['issues']:
                    if 'type' in issue:
                        found_types.add(issue['type'])
                    elif 'issue_type' in issue:
                        found_types.add(issue['issue_type'])
        
        expected_types = set(test_case.expected_issues)
        type_match = len(found_types & expected_types) / len(expected_types) if expected_types else 0
        
        # Combine ratios
        accuracy = (ratio * 0.6) + (type_match * 0.4)
        
        return round(accuracy, 2)
    
    def evaluate_all(self, orchestrator) -> Dict[str, Any]:
        """Evaluate orchestrator on all test cases.
        
        Args:
            orchestrator: CodeReviewOrchestrator instance
        
        Returns:
            Summary dictionary
        """
        logger.info(f"Starting evaluation of {len(self.test_cases)} test cases")
        
        self.results.clear()
        
        for test_case in self.test_cases:
            self.evaluate(orchestrator, test_case)
        
        summary = self.generate_summary()
        logger.info("Evaluation completed")
        
        return summary
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate evaluation summary.
        
        Returns:
            Summary dictionary with statistics
        """
        if not self.results:
            return {'message': 'No evaluation results available'}
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        
        avg_execution_time = sum(r.execution_time for r in self.results) / total
        avg_accuracy = sum(r.accuracy_score for r in self.results) / total
        avg_quality_score = sum(r.quality_score for r in self.results) / total
        
        summary = {
            'total_tests': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': round((passed / total) * 100, 2),
            'average_execution_time': round(avg_execution_time, 3),
            'average_accuracy': round(avg_accuracy, 2),
            'average_quality_score': round(avg_quality_score, 2),
            'results': [
                {
                    'test_case': r.test_case_name,
                    'passed': r.passed,
                    'accuracy': r.accuracy_score,
                    'quality_score': r.quality_score,
                    'execution_time': round(r.execution_time, 3)
                }
                for r in self.results
            ]
        }
        
        return summary
    
    def print_summary(self):
        """Print evaluation summary to console."""
        summary = self.generate_summary()
        
        print("\n" + "="*70)
        print("📊 Agent Evaluation Summary")
        print("="*70)
        
        if 'message' in summary:
            print(f"\n{summary['message']}")
            return
        
        print(f"\nTotal Tests: {summary['total_tests']}")
        print(f"✅ Passed: {summary['passed']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"📈 Pass Rate: {summary['pass_rate']}%")
        
        print(f"\n⏱️  Average Execution Time: {summary['average_execution_time']}s")
        print(f"🎯 Average Accuracy: {summary['average_accuracy']}")
        print(f"⭐ Average Quality Score: {summary['average_quality_score']}/100")
        
        print("\n📋 Individual Results:")
        for result in summary['results']:
            status = "✅" if result['passed'] else "❌"
            print(f"   {status} {result['test_case']}: "
                  f"Accuracy={result['accuracy']}, "
                  f"Quality={result['quality_score']}, "
                  f"Time={result['execution_time']}s")
        
        print("="*70)
    
    def export_results(self, filepath: str):
        """Export evaluation results to JSON.
        
        Args:
            filepath: Path to save results
        """
        summary = self.generate_summary()
        summary['exported_at'] = datetime.now().isoformat()
        summary['detailed_results'] = [asdict(r) for r in self.results]
        
        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Exported evaluation results to {filepath}")


def create_default_test_cases() -> List[TestCase]:
    """Create a default set of test cases.
    
    Returns:
        List of TestCase instances
    """
    test_cases = [
        TestCase(
            id="test_001",
            name="Simple Function - Good Quality",
            code="""def add(a: int, b: int) -> int:
    \"\"\"Add two numbers.\"\"\"
    return a + b""",
            language="python",
            expected_issues=[],
            expected_severity="none",
            description="Clean, simple function with good documentation"
        ),
        TestCase(
            id="test_002",
            name="SQL Injection Vulnerability",
            code="""def get_user(user_id):
    query = "SELECT * FROM users WHERE id = %s" % user_id
    return execute(query)""",
            language="python",
            expected_issues=["sql_injection"],
            expected_severity="critical",
            description="SQL injection vulnerability using string formatting"
        ),
        TestCase(
            id="test_003",
            name="High Complexity Function",
            code="""def complex_function(data):
    result = 0
    for item in data:
        if item > 0:
            if item < 10:
                result += item
            elif item < 20:
                result += item * 2
            else:
                result += item * 3
        elif item < 0:
            if item > -10:
                result -= item
            else:
                result -= item * 2
    return result""",
            language="python",
            expected_issues=["high_complexity", "deep_nesting"],
            expected_severity="medium",
            description="Function with high cyclomatic complexity"
        ),
        TestCase(
            id="test_004",
            name="Hardcoded Secrets",
            code="""def connect_database():
    password = "SuperSecret123!"
    api_key = "sk-1234567890abcdef"
    return connect(password=password, api_key=api_key)""",
            language="python",
            expected_issues=["hardcoded_secret"],
            expected_severity="high",
            description="Hardcoded passwords and API keys"
        ),
        TestCase(
            id="test_005",
            name="Poor Documentation",
            code="""def process_data(data, config, flags):
    x = data[0]
    y = config.get('y')
    if flags & 0x01:
        return x + y
    return x - y""",
            language="python",
            expected_issues=["todo_comment", "long_function"],
            expected_severity="low",
            description="Poorly documented function with unclear variable names"
        ),
    ]
    
    return test_cases
