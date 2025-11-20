"""Demo script for the enhanced evaluation system.

This demonstrates:
1. Loading ground truth test cases
2. Running evaluations with precision, recall, F1 metrics
3. Generating comprehensive reports
4. Analyzing performance by category
"""

import os
import sys
from main import CodeReviewOrchestrator
from utils.evaluation import AgentEvaluator, create_default_test_cases
from utils.rich_output import console

def main():
    """Run evaluation demo."""
    
    console.print("\n╔═══════════════════════════════════════════════════════════╗", style="bold cyan")
    console.print("║                                                           ║", style="bold cyan")
    console.print("║     🧪 Agent Evaluation System Demo                      ║", style="bold cyan")
    console.print("║     Precision, Recall, F1 Score Analysis                 ║", style="bold cyan")
    console.print("║                                                           ║", style="bold cyan")
    console.print("╚═══════════════════════════════════════════════════════════╝", style="bold cyan")
    
    # Check for API key
    if not os.getenv("GOOGLE_AI_API_KEY"):
        console.print("\n❌ Error: GOOGLE_AI_API_KEY not set", style="bold red")
        console.print("Set it with: export GOOGLE_AI_API_KEY='your-key'", style="yellow")
        return
    
    try:
        # Initialize orchestrator
        console.print("\n[1/4] 🤖 Initializing CodeReview-AI-Agent...", style="bold blue")
        orchestrator = CodeReviewOrchestrator()
        console.print("✓ Orchestrator initialized", style="green")
        
        # Initialize evaluator
        console.print("\n[2/4] 📊 Setting up evaluation framework...", style="bold blue")
        evaluator = AgentEvaluator()
        
        # Option 1: Load from file (if exists)
        test_cases_file = "ground_truth_test_cases.json"
        if os.path.exists(test_cases_file):
            console.print(f"   Loading test cases from {test_cases_file}...", style="cyan")
            evaluator.load_test_cases_from_file(test_cases_file)
        else:
            # Option 2: Use default test cases
            console.print("   Loading default test cases...", style="cyan")
            test_cases = create_default_test_cases()
            for tc in test_cases:
                evaluator.add_test_case(tc)
        
        console.print(f"✓ Loaded {len(evaluator.test_cases)} test cases", style="green")
        
        # Show test case categories
        categories = {}
        for tc in evaluator.test_cases:
            categories[tc.category] = categories.get(tc.category, 0) + 1
        
        console.print("\n   Test Categories:", style="cyan")
        for cat, count in categories.items():
            console.print(f"      • {cat.capitalize()}: {count} tests", style="white")
        
        # Run evaluation
        console.print("\n[3/4] 🧪 Running evaluation suite...", style="bold blue")
        console.print("   This will take a moment as each test is processed by all agents.\n", style="yellow")
        
        summary = evaluator.evaluate_all(orchestrator)
        
        # Display results
        console.print("\n[4/4] 📈 Generating evaluation report...", style="bold blue")
        evaluator.print_summary()
        
        # Export results
        output_file = "evaluation_results.json"
        evaluator.export_results(output_file)
        console.print(f"\n✓ Detailed results exported to: {output_file}", style="bold green")
        
        # Show interpretation
        console.print("\n" + "="*80, style="cyan")
        console.print("💡 Understanding Your Metrics", style="bold yellow")
        console.print("="*80, style="cyan")
        
        metrics = summary['metrics']
        
        console.print(f"\n📊 Overall F1 Score: {metrics['f1_score']:.3f}", style="bold")
        if metrics['f1_score'] >= 0.8:
            console.print("   🌟 Excellent! Agents are performing very well.", style="green")
        elif metrics['f1_score'] >= 0.6:
            console.print("   👍 Good performance, some room for improvement.", style="yellow")
        else:
            console.print("   ⚠️  Needs improvement. Consider tuning prompts or tools.", style="red")
        
        console.print(f"\n🎯 Precision: {metrics['precision']:.3f}", style="bold")
        if metrics['precision'] < 0.7:
            console.print("   💡 Tip: High false positives. Agents may be too aggressive.", style="yellow")
        
        console.print(f"\n🔍 Recall: {metrics['recall']:.3f}", style="bold")
        if metrics['recall'] < 0.7:
            console.print("   💡 Tip: High false negatives. Agents may be missing issues.", style="yellow")
        
        # Show best/worst performing categories
        if summary.get('category_breakdown'):
            console.print("\n📁 Category Performance:", style="bold")
            sorted_cats = sorted(
                summary['category_breakdown'].items(),
                key=lambda x: x[1]['avg_f1'],
                reverse=True
            )
            
            for cat, data in sorted_cats:
                emoji = "🌟" if data['avg_f1'] >= 0.7 else "⚠️"
                console.print(
                    f"   {emoji} {cat.capitalize():12} - F1: {data['avg_f1']:.3f} "
                    f"({data['passed']}/{data['total']} passed)",
                    style="white"
                )
        
        console.print("\n" + "="*80, style="cyan")
        console.print("✅ Evaluation complete!", style="bold green")
        console.print("="*80 + "\n", style="cyan")
        
    except KeyboardInterrupt:
        console.print("\n\n⚠️  Evaluation interrupted by user", style="yellow")
    except Exception as e:
        console.print(f"\n❌ Error during evaluation: {e}", style="bold red")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
