"""Example usage of CodeReview-AI-Agent system.

This script demonstrates various features:
- Basic code review
- Batch processing
- Session resumption
- Custom configuration
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import CodeReviewOrchestrator


def example_basic_review():
    """Example: Basic code review."""
    print("\n" + "="*70)
    print("Example 1: Basic Code Review")
    print("="*70)
    
    code = '''def calculate_total(items):
    """Calculate total price from items."""
    total = 0
    for item in items:
        total += item['price'] * item['quantity']
    return total
'''
    
    orchestrator = CodeReviewOrchestrator()
    results = orchestrator.review_code(code, language="python")
    
    print(f"\n✅ Review Complete!")
    print(f"   Quality Score: {results['agents']['quality_reviewer']['quality_score']}/100")
    print(f"   Issues Found: {results['summary']['issues_found']}")


def example_security_focused():
    """Example: Security-focused review."""
    print("\n" + "="*70)
    print("Example 2: Security-Focused Review")
    print("="*70)
    
    code = '''def authenticate_user(username, password):
    # Authenticate user
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    result = execute_query(query)
    return result
'''
    
    orchestrator = CodeReviewOrchestrator()
    results = orchestrator.review_code(code, language="python")
    
    security_results = results['agents']['security_checker']
    print(f"\n🔒 Security Analysis:")
    print(f"   Risk Level: {security_results['risk_level']}")
    print(f"   Vulnerabilities: {len(security_results['vulnerabilities'])}")
    
    for vuln in security_results['vulnerabilities']:
        print(f"\n   ⚠️  {vuln['severity'].upper()}: {vuln['type']}")
        print(f"      Line {vuln['line']}: {vuln['description']}")
        print(f"      Fix: {vuln['recommendation']}")


def example_batch_processing():
    """Example: Batch processing multiple files."""
    print("\n" + "="*70)
    print("Example 3: Batch Processing")
    print("="*70)
    
    code_samples = [
        ("sample1.py", "def add(a, b):\n    return a + b"),
        ("sample2.py", "def multiply(x, y):\n    result = x * y\n    return result"),
        ("sample3.py", "password = 'hardcoded123'\nprint(password)"),
    ]
    
    orchestrator = CodeReviewOrchestrator()
    
    for filename, code in code_samples:
        print(f"\n📄 Reviewing {filename}...")
        results = orchestrator.review_code(code, language="python")
        quality_score = results['agents']['quality_reviewer']['quality_score']
        issues = results['summary']['issues_found']
        print(f"   Quality: {quality_score}/100, Issues: {issues}")


def example_session_resumption():
    """Example: Session resumption."""
    print("\n" + "="*70)
    print("Example 4: Session Resumption")
    print("="*70)
    
    code = "def test():\n    pass"
    
    orchestrator = CodeReviewOrchestrator()
    
    # First review
    print("\n📝 First review...")
    results1 = orchestrator.review_code(code, language="python")
    session_id = results1['session_id']
    print(f"   Session ID: {session_id}")
    
    # Resume session
    print(f"\n🔄 Resuming session {session_id}...")
    history = orchestrator.get_session_history(session_id)
    print(f"   Review count: {history['review_count']}")
    print(f"   History entries: {len(history['history'])}")


def main():
    """Run all examples."""
    # Check for API key
    if not os.getenv('GOOGLE_AI_API_KEY'):
        print("\n❌ ERROR: GOOGLE_AI_API_KEY environment variable not set")
        print("   Please set your API key:")
        print("   export GOOGLE_AI_API_KEY='your-key-here'")
        sys.exit(1)
    
    print("\n" + "="*70)
    print("🚀 CodeReview-AI-Agent Usage Examples")
    print("="*70)
    
    try:
        example_basic_review()
        example_security_focused()
        example_batch_processing()
        example_session_resumption()
        
        print("\n" + "="*70)
        print("✅ All examples completed successfully!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
