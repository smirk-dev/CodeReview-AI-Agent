# Quick Start Guide

## Setup (5 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set API Key
Get your API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

**Windows (PowerShell):**
```powershell
$env:GOOGLE_AI_API_KEY="your-api-key-here"
```

**Linux/Mac:**
```bash
export GOOGLE_AI_API_KEY='your-api-key-here'
```

### 3. Run Demo
```bash
python main.py
```

## Test the System

### Run Unit Tests
```bash
python test_system.py
```

### Run Examples
```bash
python examples/sample_usage.py
```

## Basic Usage

```python
from main import CodeReviewOrchestrator

# Initialize
orchestrator = CodeReviewOrchestrator()

# Review code
code = '''
def calculate_total(items):
    total = 0
    for item in items:
        total += item['price'] * item['quantity']
    return total
'''

results = orchestrator.review_code(code, language="python")

# Check results
print(f"Quality Score: {results['agents']['quality_reviewer']['quality_score']}/100")
print(f"Issues Found: {results['summary']['issues_found']}")
```

## What Gets Analyzed

✅ **Code Structure**: Complexity, functions, classes  
✅ **Security**: Vulnerabilities, hardcoded secrets, injection risks  
✅ **Quality**: Code smells, best practices, documentation  

## Output Files

After running reviews, you'll find:
- `review_results_*.json` - Detailed review results
- `logs/code_review.log` - System logs
- `evaluation_results.json` - Evaluation metrics (if tests run)

## Next Steps

1. Review the demo output in `main.py`
2. Try examples in `examples/sample_usage.py`
3. Run full tests with `python test_system.py`
4. Customize agents in `agents/` directory

## ADK Concepts Demonstrated

1. ✅ **Multi-Agent System** - Sequential agents (3 specialized agents)
2. ✅ **Custom Tools** - CodeAnalysisTools for AST parsing, complexity analysis
3. ✅ **Sessions & Memory** - InMemorySessionService + MemoryBank
4. ✅ **Context Engineering** - Progressive context sharing between agents
5. ✅ **Observability** - Logging, tracing, metrics collection
6. ✅ **Evaluation** - Agent performance testing framework

## Troubleshooting

**API Key Error:**
```
ValueError: API key required
```
→ Set GOOGLE_AI_API_KEY environment variable

**Import Error:**
```
ModuleNotFoundError: No module named 'google.genai'
```
→ Run `pip install -r requirements.txt`

**No Results:**
→ Check logs in `logs/code_review.log`

## Support

- GitHub Issues: [Report bugs](https://github.com/smirk-dev/CodeReview-AI-Agent/issues)
- Documentation: See README.md for detailed info
