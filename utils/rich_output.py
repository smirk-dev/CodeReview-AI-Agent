"""
Rich Terminal Output Module
Provides beautiful terminal output using rich library
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.syntax import Syntax
from rich.tree import Tree
from rich.markdown import Markdown
from typing import Dict, List, Any
import json

console = Console()

class RichOutput:
    """Rich terminal output manager"""
    
    def __init__(self):
        self.console = console
    
    def print_header(self, title: str, subtitle: str = ""):
        """Print stylized header"""
        header_text = f"[bold cyan]{title}[/bold cyan]"
        if subtitle:
            header_text += f"\n[dim]{subtitle}[/dim]"
        
        panel = Panel(
            header_text,
            border_style="cyan",
            padding=(1, 2)
        )
        self.console.print(panel)
    
    def print_success(self, message: str):
        """Print success message"""
        self.console.print(f"[green]✓[/green] {message}")
    
    def print_error(self, message: str):
        """Print error message"""
        self.console.print(f"[red]✗[/red] {message}")
    
    def print_warning(self, message: str):
        """Print warning message"""
        self.console.print(f"[yellow]⚠[/yellow] {message}")
    
    def print_info(self, message: str):
        """Print info message"""
        self.console.print(f"[blue]ℹ[/blue] {message}")
    
    def print_agent_start(self, agent_name: str, step: str):
        """Print agent start message"""
        self.console.print(f"\n[bold magenta]{step}[/bold magenta] [cyan]{agent_name}[/cyan]...")
    
    def print_code(self, code: str, language: str = "python"):
        """Print syntax highlighted code"""
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        self.console.print(Panel(syntax, title="Code", border_style="green"))
    
    def create_metrics_table(self, metrics: Dict[str, Any]) -> Table:
        """Create a table for code metrics"""
        table = Table(title="Code Metrics", show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="yellow")
        
        for key, value in metrics.items():
            table.add_row(key.replace("_", " ").title(), str(value))
        
        return table
    
    def create_issues_table(self, issues: List[Dict[str, Any]]) -> Table:
        """Create a table for issues"""
        table = Table(title="Issues Found", show_header=True, header_style="bold red")
        table.add_column("Severity", style="red")
        table.add_column("Type", style="yellow")
        table.add_column("Line", style="cyan")
        table.add_column("Description", style="white")
        
        for issue in issues:
            severity = issue.get("severity", "unknown")
            severity_color = {
                "critical": "[red bold]",
                "high": "[red]",
                "medium": "[yellow]",
                "low": "[blue]"
            }.get(severity.lower(), "[white]")
            
            table.add_row(
                f"{severity_color}{severity.upper()}[/]",
                issue.get("type", "N/A"),
                str(issue.get("line", "N/A")),
                issue.get("description", "N/A")
            )
        
        return table
    
    def create_recommendations_tree(self, recommendations: List[str]) -> Tree:
        """Create a tree for recommendations"""
        tree = Tree("[bold cyan]💡 Recommendations[/bold cyan]")
        
        for i, rec in enumerate(recommendations, 1):
            tree.add(f"[yellow]{i}.[/yellow] {rec}")
        
        return tree
    
    def print_summary(self, summary: Dict[str, Any]):
        """Print review summary"""
        table = Table(title="Review Summary", show_header=True, header_style="bold green")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="yellow", justify="right")
        
        table.add_row("Total Agents", str(summary.get("total_agents", 0)))
        table.add_row("Successful", str(summary.get("successful_agents", 0)))
        table.add_row("Issues Found", str(summary.get("issues_found", 0)))
        table.add_row("Recommendations", str(summary.get("recommendations_count", 0)))
        
        self.console.print(table)
    
    def create_progress(self, description: str):
        """Create a progress bar"""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console
        )
    
    def print_quality_score(self, score: int, grade: str):
        """Print quality score with styling"""
        color = "green" if score >= 80 else "yellow" if score >= 60 else "red"
        self.console.print(
            Panel(
                f"[{color} bold]Quality Score: {score}/100[/{color} bold]\n"
                f"[{color}]Grade: {grade}[/{color}]",
                title="Code Quality",
                border_style=color
            )
        )
    
    def print_results(self, results: Dict[str, Any]):
        """Print comprehensive results"""
        self.console.print("\n")
        self.print_header("Review Results", f"Session: {results.get('session_id', 'N/A')}")
        
        # Print metrics if available
        if "agents" in results and "code_analyzer" in results["agents"]:
            metrics = results["agents"]["code_analyzer"].get("metrics", {})
            if metrics:
                self.console.print(self.create_metrics_table(metrics))
        
        # Print quality score
        if "agents" in results and "quality_reviewer" in results["agents"]:
            quality = results["agents"]["quality_reviewer"]
            score = quality.get("quality_score", 0)
            grade = quality.get("quality_grade", "N/A")
            self.console.print("\n")
            self.print_quality_score(score, grade)
        
        # Print issues
        all_issues = []
        if "agents" in results:
            for agent_name, agent_data in results["agents"].items():
                if "issues" in agent_data:
                    all_issues.extend(agent_data["issues"])
        
        if all_issues:
            self.console.print("\n")
            self.console.print(self.create_issues_table(all_issues))
        
        # Print recommendations
        all_recommendations = []
        if "agents" in results:
            for agent_name, agent_data in results["agents"].items():
                if "recommendations" in agent_data:
                    all_recommendations.extend(agent_data["recommendations"])
        
        if all_recommendations:
            self.console.print("\n")
            self.console.print(self.create_recommendations_tree(all_recommendations))
        
        # Print summary
        if "summary" in results:
            self.console.print("\n")
            self.print_summary(results["summary"])

# Global instance
rich_output = RichOutput()
