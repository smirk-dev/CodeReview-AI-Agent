"""Comprehensive test script for CodeReview-AI-Agent system.

This script tests the complete end-to-end functionality including:
- All three agents
- Custom tools
- Session management
- Memory bank
- Observability
- Evaluation framework
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from main import CodeReviewOrchestrator
from utils.observability import get_observability
from utils.evaluation import AgentEvaluator, create_default_test_cases


def test_basic_functionality():
    """Test basic code review functionality."""
    print("\n" + "="*70)
    print("Test 1: Basic Code Review")
    print("="*70)
    
    # Initialize observability
    obs = get_observability(log_level="INFO")
    
    # Simple test code
    test_code = '''def hello(name):
    """Say hello."""
    return f"Hello, {name}!"
'''
    
    try:
        orchestrator = CodeReviewOrchestrator()
        
        with obs.trace_operation("basic_review_test"):
            results = orchestrator.review_code(test_code, language="python")
        
        # Validate results
        assert 'agents' in results, "Results should contain agents key"
        assert 'code_analyzer' in results['agents'], "Code analyzer should run"
        assert 'security_checker' in results['agents'], "Security checker should run"
        assert 'quality_reviewer' in results['agents'], "Quality reviewer should run"
        
        print("✅ Basic functionality test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test FAILED: {e}")
        return False


def test_security_detection():
    """Test security vulnerability detection."""
    print("\n" + "="*70)
    print("Test 2: Security Vulnerability Detection")
    print("="*70)
    
    # Code with security issues
    test_code = '''def unsafe_query(user_id):
    password = "hardcoded123"
    query = "SELECT * FROM users WHERE id = %s" % user_id
    return execute(query)
'''
    
    try:
        orchestrator = CodeReviewOrchestrator()
        results = orchestrator.review_code(test_code, language="python")
        
        # Check security findings
        security_results = results['agents']['security_checker']
        vulnerabilities = security_results.get('vulnerabilities', [])
        
        assert len(vulnerabilities) > 0, "Should detect security vulnerabilities"
        
        # Check for specific vulnerabilities
        vuln_types = [v['type'] for v in vulnerabilities]
        assert 'sql_injection' in vuln_types or 'hardcoded_secret' in vuln_types, \
            "Should detect SQL injection or hardcoded secrets"
        
        print(f"   Detected {len(vulnerabilities)} vulnerabilities: {vuln_types}")
        print("✅ Security detection test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Security detection test FAILED: {e}")
        return False


def test_complexity_analysis():
    """Test complexity analysis."""
    print("\n" + "="*70)
    print("Test 3: Complexity Analysis")
    print("="*70)
    
    # Complex function
    test_code = '''def complex_calc(x, y, z):
    if x > 0:
        if y > 0:
            if z > 0:
                return x + y + z
            else:
                return x + y - z
        else:
            return x - y
    else:
        return 0
'''
    
    try:
        orchestrator = CodeReviewOrchestrator()
        results = orchestrator.review_code(test_code, language="python")
        
        # Check analysis results
        analysis_results = results['agents']['code_analyzer']
        metrics = analysis_results.get('metrics', {})
        
        assert 'total_complexity' in metrics, "Should calculate complexity"
        assert metrics['total_complexity'] > 0, "Complexity should be greater than 0"
        
        print(f"   Total complexity: {metrics['total_complexity']}")
        print(f"   Max function complexity: {metrics['max_function_complexity']}")
        print("✅ Complexity analysis test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Complexity analysis test FAILED: {e}")
        return False


def test_session_management():
    """Test session management and memory."""
    print("\n" + "="*70)
    print("Test 4: Session Management")
    print("="*70)
    
    test_code = 'def test(): pass'
    
    try:
        orchestrator = CodeReviewOrchestrator()
        
        # First review
        results1 = orchestrator.review_code(test_code, language="python")
        session_id = results1['session_id']
        
        # Retrieve session history
        history = orchestrator.get_session_history(session_id)
        
        assert history is not None, "Should retrieve session history"
        assert len(history['history']) > 0, "Session should have history"
        
        print(f"   Session ID: {session_id}")
        print(f"   History items: {len(history['history'])}")
        print("✅ Session management test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Session management test FAILED: {e}")
        return False


def test_memory_bank():
    """Test memory bank functionality."""
    print("\n" + "="*70)
    print("Test 5: Memory Bank")
    print("="*70)
    
    try:
        orchestrator = CodeReviewOrchestrator()
        memory = orchestrator.memory_bank
        
        # Store data
        memory.store("test_key", {"data": "test_value"})
        
        # Retrieve data
        retrieved = memory.get("test_key")
        
        assert retrieved is not None, "Should retrieve stored data"
        assert retrieved['data'] == "test_value", "Data should match"
        
        # Check exists
        assert memory.exists("test_key"), "Key should exist"
        
        # Get summary
        summary = memory.get_context_summary()
        assert summary['total_items'] > 0, "Should have items in memory"
        
        print(f"   Memory items: {summary['total_items']}")
        print("✅ Memory bank test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Memory bank test FAILED: {e}")
        return False


def test_observability():
    """Test observability features."""
    print("\n" + "="*70)
    print("Test 6: Observability")
    print("="*70)
    
    try:
        obs = get_observability()
        
        # Test tracing
        with obs.trace_operation("test_operation", test_param="value"):
            import time
            time.sleep(0.1)
        
        # Test metrics
        obs.record_metric("test_metric", 42.5)
        
        # Get traces and metrics
        traces = obs.get_traces()
        metrics = obs.get_all_metrics()
        
        assert len(traces) > 0, "Should have recorded traces"
        assert "test_metric" in metrics, "Should have recorded metrics"
        
        print(f"   Total traces: {len(traces)}")
        print(f"   Total metrics: {len(metrics)}")
        print("✅ Observability test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Observability test FAILED: {e}")
        return False


def test_evaluation_framework():
    """Test evaluation framework."""
    print("\n" + "="*70)
    print("Test 7: Evaluation Framework")
    print("="*70)
    
    try:
        orchestrator = CodeReviewOrchestrator()
        evaluator = AgentEvaluator()
        
        # Create test cases
        test_cases = create_default_test_cases()
        
        # Add a subset for quick testing
        for tc in test_cases[:2]:
            evaluator.add_test_case(tc)
        
        # Run evaluation
        summary = evaluator.evaluate_all(orchestrator)
        
        assert 'total_tests' in summary, "Should have evaluation summary"
        assert summary['total_tests'] == 2, "Should run 2 tests"
        
        print(f"   Tests run: {summary['total_tests']}")
        print(f"   Pass rate: {summary['pass_rate']}%")
        print("✅ Evaluation framework test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Evaluation framework test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_full_evaluation():
    """Run full evaluation with all test cases."""
    print("\n" + "="*70)
    print("Full Agent Evaluation")
    print("="*70)
    
    try:
        orchestrator = CodeReviewOrchestrator()
        evaluator = AgentEvaluator()
        
        # Load all default test cases
        test_cases = create_default_test_cases()
        for tc in test_cases:
            evaluator.add_test_case(tc)
        
        print(f"\nRunning evaluation on {len(test_cases)} test cases...")
        
        # Run evaluation
        summary = evaluator.evaluate_all(orchestrator)
        
        # Print results
        evaluator.print_summary()
        
        # Export results
        evaluator.export_results("evaluation_results.json")
        print("\n💾 Detailed results saved to: evaluation_results.json")
        
        return True
        
    except Exception as e:
        print(f"❌ Full evaluation FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("CodeReview-AI-Agent System Tests")
    print("="*70)
    
    # Check for API key
    if not os.getenv('GOOGLE_AI_API_KEY'):
        print("\n❌ ERROR: GOOGLE_AI_API_KEY environment variable not set")
        print("   Please set your API key:")
        print("   export GOOGLE_AI_API_KEY='your-key-here'")
        sys.exit(1)
    
    results = []
    
    # Run tests
    results.append(("Basic Functionality", test_basic_functionality()))
    results.append(("Security Detection", test_security_detection()))
    results.append(("Complexity Analysis", test_complexity_analysis()))
    results.append(("Session Management", test_session_management()))
    results.append(("Memory Bank", test_memory_bank()))
    results.append(("Observability", test_observability()))
    results.append(("Evaluation Framework", test_evaluation_framework()))
    
    # Print summary
    print("\n" + "="*70)
    print("📊 Test Summary")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({int(passed/total*100)}%)")
    
    # Run full evaluation if all tests passed
    if passed == total:
        print("\n🎉 All unit tests passed! Running full evaluation...")
        run_full_evaluation()
        
        # Print observability summary
        obs = get_observability()
        obs.print_summary()
        
        # Export observability data
        obs.export_traces("test_traces.json")
        obs.export_metrics("test_metrics.json")
        print("\n💾 Observability data exported to test_traces.json and test_metrics.json")
    
    print("\n" + "="*70)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
