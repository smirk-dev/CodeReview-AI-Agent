"""Evaluation framework for assessing agent performance.

This module provides evaluation capabilities:
- Agent accuracy assessment with precision, recall, F1 scores
- Response quality metrics
- Performance benchmarking
- Test case management with ground truth
- Detailed performance analytics
"""

import json
import time
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class GroundTruthIssue:
    """Ground truth issue for evaluation."""
    issue_type: str
    severity: str
    line_number: Optional[int] = None
    description: Optional[str] = None


@dataclass
class TestCase:
    """Test case for code review evaluation with ground truth."""
    id: str
    name: str
    code: str
    language: str
    expected_issues: List[GroundTruthIssue]
    expected_severity: str
    description: str
    category: str = "general"  # security, complexity, quality, style


@dataclass
class PerformanceMetrics:
    """Detailed performance metrics."""
    precision: float
    recall: float
    f1_score: float
    true_positives: int
    false_positives: int
    false_negatives: int
    accuracy: float


@dataclass
class EvaluationResult:
    """Result of an evaluation run with detailed metrics."""
    test_case_id: str
    test_case_name: str
    category: str
    execution_time: float
    issues_found: int
    issues_expected: int
    metrics: PerformanceMetrics
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
            # Convert expected_issues to GroundTruthIssue objects
            expected_issues = []
            for issue_data in tc_data.get('expected_issues', []):
                if isinstance(issue_data, str):
                    # Legacy format: convert string to object
                    expected_issues.append(GroundTruthIssue(
                        issue_type=issue_data,
                        severity=tc_data.get('expected_severity', 'medium')
                    ))
                else:
                    # New format: create from dict
                    expected_issues.append(GroundTruthIssue(**issue_data))
            
            tc_data['expected_issues'] = expected_issues
            test_case = TestCase(**tc_data)
            self.add_test_case(test_case)
        
        logger.info(f"Loaded {len(self.test_cases)} test cases from {filepath}")
    
    def evaluate(self, orchestrator, test_case: TestCase) -> EvaluationResult:
        """Evaluate orchestrator on a single test case with detailed metrics.
        
        Args:
            orchestrator: CodeReviewOrchestrator instance
            test_case: Test case to evaluate
        
        Returns:
            EvaluationResult with precision, recall, F1 scores
        """
        logger.info(f"Evaluating test case: {test_case.name}")
        
        start_time = time.time()
        
        try:
            # Run code review
            results = orchestrator.review_code(test_case.code, test_case.language)
            
            execution_time = time.time() - start_time
            
            # Extract found issues
            found_issues = self._extract_found_issues(results)
            
            # Calculate performance metrics
            metrics = self._calculate_metrics(found_issues, test_case.expected_issues)
            
            # Get quality score
            quality_score = results.get('agents', {}).get('quality_reviewer', {}).get('quality_score', 0)
            
            # Determine if passed (F1 >= 0.7 or perfect match)
            passed = metrics.f1_score >= 0.7 or (
                metrics.true_positives > 0 and 
                metrics.false_positives == 0 and 
                metrics.false_negatives == 0
            )
            
            result = EvaluationResult(
                test_case_id=test_case.id,
                test_case_name=test_case.name,
                category=test_case.category,
                execution_time=execution_time,
                issues_found=len(found_issues),
                issues_expected=len(test_case.expected_issues),
                metrics=metrics,
                quality_score=quality_score,
                passed=passed,
                details={
                    'found_issues': [asdict(i) for i in found_issues],
                    'expected_issues': [asdict(i) for i in test_case.expected_issues],
                    'results': results
                }
            )
            
            self.results.append(result)
            logger.info(f"Test case completed: {test_case.name} - {'PASSED' if passed else 'FAILED'} "
                       f"(F1={metrics.f1_score:.2f}, P={metrics.precision:.2f}, R={metrics.recall:.2f})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error evaluating test case {test_case.name}: {e}")
            execution_time = time.time() - start_time
            
            # Create empty metrics for failed case
            metrics = PerformanceMetrics(
                precision=0.0, recall=0.0, f1_score=0.0,
                true_positives=0, false_positives=0,
                false_negatives=len(test_case.expected_issues),
                accuracy=0.0
            )
            
            result = EvaluationResult(
                test_case_id=test_case.id,
                test_case_name=test_case.name,
                category=test_case.category,
                execution_time=execution_time,
                issues_found=0,
                issues_expected=len(test_case.expected_issues),
                metrics=metrics,
                quality_score=0,
                passed=False,
                details={'error': str(e)}
            )
            
            self.results.append(result)
            return result
    
    def _extract_found_issues(self, results: Dict) -> List[GroundTruthIssue]:
        """Extract issues from review results.
        
        Args:
            results: Review results dictionary
        
        Returns:
            List of GroundTruthIssue objects
        """
        found_issues = []
        
        for agent_name, agent_result in results.get('agents', {}).items():
            if 'issues' in agent_result:
                for issue in agent_result['issues']:
                    issue_type = issue.get('type') or issue.get('issue_type', 'unknown')
                    severity = issue.get('severity', 'medium').lower()
                    line = issue.get('line')
                    description = issue.get('description', '')
                    
                    found_issues.append(GroundTruthIssue(
                        issue_type=issue_type,
                        severity=severity,
                        line_number=line,
                        description=description
                    ))
        
        return found_issues
    
    def _calculate_metrics(self, found: List[GroundTruthIssue], 
                          expected: List[GroundTruthIssue]) -> PerformanceMetrics:
        """Calculate precision, recall, F1, and other metrics.
        
        Args:
            found: List of found issues
            expected: List of expected issues (ground truth)
        
        Returns:
            PerformanceMetrics with all calculated metrics
        """
        # Convert to sets of issue types for comparison
        found_types = set(issue.issue_type for issue in found)
        expected_types = set(issue.issue_type for issue in expected)
        
        # Calculate TP, FP, FN
        true_positives = len(found_types & expected_types)
        false_positives = len(found_types - expected_types)
        false_negatives = len(expected_types - found_types)
        
        # Calculate precision, recall, F1
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        # Calculate overall accuracy
        total = true_positives + false_positives + false_negatives
        accuracy = true_positives / total if total > 0 else 0.0
        
        return PerformanceMetrics(
            precision=round(precision, 3),
            recall=round(recall, 3),
            f1_score=round(f1_score, 3),
            true_positives=true_positives,
            false_positives=false_positives,
            false_negatives=false_negatives,
            accuracy=round(accuracy, 3)
        )
    
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
        """Generate comprehensive evaluation summary with detailed metrics.
        
        Returns:
            Summary dictionary with statistics and breakdowns
        """
        if not self.results:
            return {'message': 'No evaluation results available'}
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        
        # Aggregate metrics
        avg_execution_time = sum(r.execution_time for r in self.results) / total
        avg_precision = sum(r.metrics.precision for r in self.results) / total
        avg_recall = sum(r.metrics.recall for r in self.results) / total
        avg_f1 = sum(r.metrics.f1_score for r in self.results) / total
        avg_quality_score = sum(r.quality_score for r in self.results) / total
        
        # Count totals
        total_tp = sum(r.metrics.true_positives for r in self.results)
        total_fp = sum(r.metrics.false_positives for r in self.results)
        total_fn = sum(r.metrics.false_negatives for r in self.results)
        
        # Category breakdown
        categories = defaultdict(lambda: {'count': 0, 'passed': 0, 'f1_scores': []})
        for r in self.results:
            categories[r.category]['count'] += 1
            if r.passed:
                categories[r.category]['passed'] += 1
            categories[r.category]['f1_scores'].append(r.metrics.f1_score)
        
        category_summary = {
            cat: {
                'total': data['count'],
                'passed': data['passed'],
                'pass_rate': round((data['passed'] / data['count']) * 100, 2),
                'avg_f1': round(sum(data['f1_scores']) / len(data['f1_scores']), 3)
            }
            for cat, data in categories.items()
        }
        
        summary = {
            'total_tests': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': round((passed / total) * 100, 2),
            'metrics': {
                'precision': round(avg_precision, 3),
                'recall': round(avg_recall, 3),
                'f1_score': round(avg_f1, 3),
                'true_positives': total_tp,
                'false_positives': total_fp,
                'false_negatives': total_fn
            },
            'performance': {
                'average_execution_time': round(avg_execution_time, 3),
                'average_quality_score': round(avg_quality_score, 2),
            },
            'category_breakdown': category_summary,
            'detailed_results': [
                {
                    'test_case': r.test_case_name,
                    'category': r.category,
                    'passed': r.passed,
                    'metrics': {
                        'precision': r.metrics.precision,
                        'recall': r.metrics.recall,
                        'f1_score': r.metrics.f1_score,
                        'tp': r.metrics.true_positives,
                        'fp': r.metrics.false_positives,
                        'fn': r.metrics.false_negatives
                    },
                    'quality_score': r.quality_score,
                    'execution_time': round(r.execution_time, 3)
                }
                for r in self.results
            ]
        }
        
        return summary
    
    def print_summary(self):
        """Print detailed evaluation summary to console with metrics."""
        summary = self.generate_summary()
        
        print("\n" + "="*80)
        print("📊 Agent Evaluation Summary - Detailed Metrics")
        print("="*80)
        
        if 'message' in summary:
            print(f"\n{summary['message']}")
            return
        
        # Overall statistics
        print(f"\n📈 Overall Results:")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   ✅ Passed: {summary['passed']}")
        print(f"   ❌ Failed: {summary['failed']}")
        print(f"   📊 Pass Rate: {summary['pass_rate']}%")
        
        # Performance metrics
        metrics = summary['metrics']
        print(f"\n🎯 Performance Metrics:")
        print(f"   Precision:  {metrics['precision']:.3f} (how many found issues are correct)")
        print(f"   Recall:     {metrics['recall']:.3f} (how many real issues were found)")
        print(f"   F1 Score:   {metrics['f1_score']:.3f} (harmonic mean of P & R)")
        print(f"   True Positives:  {metrics['true_positives']} (correct detections)")
        print(f"   False Positives: {metrics['false_positives']} (incorrect detections)")
        print(f"   False Negatives: {metrics['false_negatives']} (missed issues)")
        
        # Performance stats
        perf = summary['performance']
        print(f"\n⏱️  Performance:")
        print(f"   Avg Execution Time: {perf['average_execution_time']}s")
        print(f"   Avg Quality Score:  {perf['average_quality_score']}/100")
        
        # Category breakdown
        if summary.get('category_breakdown'):
            print(f"\n📁 Category Breakdown:")
            for cat, data in summary['category_breakdown'].items():
                print(f"   {cat.capitalize():12} | Tests: {data['total']:2} | "
                      f"Pass Rate: {data['pass_rate']:5.1f}% | "
                      f"Avg F1: {data['avg_f1']:.3f}")
        
        # Individual results
        print("\n📋 Individual Test Results:")
        print(f"   {'Test Case':<35} {'Pass':<6} {'P':<6} {'R':<6} {'F1':<6} {'Q':<4} {'Time':<7}")
        print(f"   {'-'*78}")
        
        for result in summary['detailed_results']:
            status = "✅" if result['passed'] else "❌"
            m = result['metrics']
            name = result['test_case'][:33]
            print(f"   {name:<35} {status:<6} "
                  f"{m['precision']:<6.3f} {m['recall']:<6.3f} {m['f1_score']:<6.3f} "
                  f"{result['quality_score']:<4} {result['execution_time']:<7.3f}s")
        
        print("="*80)
        
        # Interpretation guide
        print("\n💡 Metrics Guide:")
        print("   P (Precision) = TP / (TP + FP)  - Accuracy of detections")
        print("   R (Recall)    = TP / (TP + FN)  - Coverage of real issues")
        print("   F1 Score      = 2 * (P * R) / (P + R) - Overall performance")
        print("   Q (Quality)   = Code quality score from agents")
        print("="*80 + "\n")
    
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
    """Create a default set of test cases with ground truth labels.
    
    Returns:
        List of TestCase instances with detailed ground truth
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
            description="Clean, simple function with good documentation",
            category="quality"
        ),
        TestCase(
            id="test_002",
            name="SQL Injection Vulnerability",
            code="""def get_user(user_id):
    query = "SELECT * FROM users WHERE id = %s" % user_id
    return execute(query)""",
            language="python",
            expected_issues=[
                GroundTruthIssue(
                    issue_type="sql_injection",
                    severity="critical",
                    line_number=2,
                    description="String formatting in SQL query enables SQL injection"
                )
            ],
            expected_severity="critical",
            description="SQL injection vulnerability using string formatting",
            category="security"
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
            expected_issues=[
                GroundTruthIssue(
                    issue_type="high_complexity",
                    severity="medium",
                    description="High cyclomatic complexity"
                ),
                GroundTruthIssue(
                    issue_type="deep_nesting",
                    severity="medium",
                    description="Deeply nested conditionals"
                )
            ],
            expected_severity="medium",
            description="Function with high cyclomatic complexity",
            category="complexity"
        ),
        TestCase(
            id="test_004",
            name="Hardcoded Secrets",
            code="""def connect_database():
    password = "SuperSecret123!"
    api_key = "sk-1234567890abcdef"
    return connect(password=password, api_key=api_key)""",
            language="python",
            expected_issues=[
                GroundTruthIssue(
                    issue_type="hardcoded_secret",
                    severity="high",
                    line_number=2,
                    description="Hardcoded password"
                ),
                GroundTruthIssue(
                    issue_type="hardcoded_secret",
                    severity="high",
                    line_number=3,
                    description="Hardcoded API key"
                )
            ],
            expected_severity="high",
            description="Hardcoded passwords and API keys",
            category="security"
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
            expected_issues=[
                GroundTruthIssue(
                    issue_type="missing_docstring",
                    severity="low",
                    description="Function lacks documentation"
                ),
                GroundTruthIssue(
                    issue_type="unclear_variable_names",
                    severity="low",
                    description="Single-letter variable names"
                )
            ],
            expected_severity="low",
            description="Poorly documented function with unclear variable names",
            category="style"
        ),
        TestCase(
            id="test_006",
            name="Command Injection Risk",
            code="""import os
def execute_command(user_input):
    os.system(f"ls {user_input}")""",
            language="python",
            expected_issues=[
                GroundTruthIssue(
                    issue_type="command_injection",
                    severity="critical",
                    line_number=3,
                    description="User input directly in system command"
                )
            ],
            expected_severity="critical",
            description="Command injection vulnerability",
            category="security"
        ),
        TestCase(
            id="test_007",
            name="Unhandled Exceptions",
            code="""def divide(a, b):
    return a / b

def parse_json(text):
    return json.loads(text)""",
            language="python",
            expected_issues=[
                GroundTruthIssue(
                    issue_type="unhandled_exception",
                    severity="medium",
                    line_number=2,
                    description="Division by zero not handled"
                ),
                GroundTruthIssue(
                    issue_type="unhandled_exception",
                    severity="medium",
                    line_number=5,
                    description="JSON parsing errors not handled"
                )
            ],
            expected_severity="medium",
            description="Functions that can raise exceptions without handling",
            category="quality"
        ),
    ]
    
    return test_cases
