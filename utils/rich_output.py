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
from rich.layout import Layout
from rich.align import Align
from rich.text import Text
from rich import box
from rich.columns import Columns
from rich.live import Live
import time
from typing import Dict, List, Any
import json

console = Console(record=True)

class RichOutput:
    """Rich terminal output manager"""
    
    def __init__(self):
        self.console = console
    
    def print_header(self, title: str, subtitle: str = ""):
        """Print stylized header with gradient effect"""
        # Create title with gradient-like effect using colors
        title_text = Text()
        colors = ["bright_cyan", "cyan", "blue"]
        words = title.split()
        
        for i, word in enumerate(words):
            color = colors[i % len(colors)]
            title_text.append(word, style=f"bold {color}")
            if i < len(words) - 1:
                title_text.append(" ")
        
        if subtitle:
            title_text.append("\n")
            title_text.append(subtitle, style="dim italic")
        
        panel = Panel(
            Align.center(title_text),
            border_style="bright_cyan",
            box=box.DOUBLE,
            padding=(1, 4),
            title="[bold bright_white]⚡[/bold bright_white]",
            title_align="left"
        )
        self.console.print(panel)
        self.console.print()
    
    def print_success(self, message: str):
        """Print success message with icon"""
        self.console.print(f"[green]✓[/green] [bold green]{message}[/bold green]")
    
    def print_error(self, message: str):
        """Print error message with icon"""
        self.console.print(f"[red]✗[/red] [bold red]{message}[/bold red]")
    
    def print_warning(self, message: str):
        """Print warning message with icon"""
        self.console.print(f"[yellow]⚠[/yellow] [bold yellow]{message}[/bold yellow]")
    
    def print_info(self, message: str):
        """Print info message with icon"""
        self.console.print(f"[blue]ℹ[/blue] [cyan]{message}[/cyan]")
    
    def print_agent_start(self, agent_name: str, step: str):
        """Print agent start message with styled panel"""
        text = Text()
        text.append(step, style="bold magenta")
        text.append(" ", style="white")
        text.append("🤖 ", style="white")
        text.append(agent_name, style="bold bright_cyan")
        text.append("...", style="dim")
        
        self.console.print()
        self.console.print(Panel(
            Align.center(text),
            border_style="magenta",
            box=box.ROUNDED,
            padding=(0, 2)
        ))
    
    def print_code(self, code: str, language: str = "python"):
        """Print syntax highlighted code"""
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        self.console.print(Panel(syntax, title="Code", border_style="green"))
    
    def create_metrics_table(self, metrics: Dict[str, Any]) -> Table:
        """Create a table for code metrics with enhanced styling"""
        table = Table(
            title="📊 Code Metrics",
            show_header=True,
            header_style="bold bright_cyan",
            border_style="cyan",
            box=box.ROUNDED,
            title_style="bold bright_white"
        )
        table.add_column("Metric", style="bright_cyan", no_wrap=True)
        table.add_column("Value", style="bright_yellow", justify="right")
        
        for key, value in metrics.items():
            # Add icons for specific metrics
            metric_name = key.replace("_", " ").title()
            if "complexity" in key.lower():
                metric_name = "⚙️  " + metric_name
            elif "function" in key.lower():
                metric_name = "🔧 " + metric_name
            elif "class" in key.lower():
                metric_name = "📦 " + metric_name
            elif "line" in key.lower():
                metric_name = "📝 " + metric_name
            
            table.add_row(metric_name, str(value))
        
        return table
    
    def create_issues_table(self, issues: List[Dict[str, Any]]) -> Table:
        """Create a table for issues with enhanced styling"""
        table = Table(
            title="🔍 Issues Found",
            show_header=True,
            header_style="bold bright_red",
            border_style="red",
            box=box.HEAVY_HEAD,
            title_style="bold bright_white"
        )
        table.add_column("Severity", style="red", justify="center", width=12)
        table.add_column("Type", style="yellow", width=20)
        table.add_column("Line", style="cyan", justify="center", width=8)
        table.add_column("Description", style="white", width=40)
        
        for issue in issues:
            severity = issue.get("severity", "unknown").upper()
            severity_styles = {
                "CRITICAL": "[white on red bold]🔴 CRITICAL[/]",
                "HIGH": "[red bold]🟠 HIGH[/]",
                "MEDIUM": "[yellow bold]🟡 MEDIUM[/]",
                "LOW": "[blue bold]🔵 LOW[/]"
            }
            
            styled_severity = severity_styles.get(severity, f"[white]{severity}[/]")
            
            table.add_row(
                styled_severity,
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
        """Print review summary with enhanced styling"""
        table = Table(
            title="📋 Review Summary",
            show_header=True,
            header_style="bold bright_green",
            border_style="green",
            box=box.DOUBLE_EDGE,
            title_style="bold bright_white"
        )
        table.add_column("Metric", style="bright_cyan", width=20)
        table.add_column("Value", style="bright_yellow", justify="right", width=10)
        
        # Add icons to metrics
        metrics_display = {
            "total_agents": ("🤖 Total Agents", summary.get("total_agents", 0)),
            "successful_agents": ("✅ Successful", summary.get("successful_agents", 0)),
            "issues_found": ("🔍 Issues Found", summary.get("issues_found", 0)),
            "recommendations_count": ("💡 Recommendations", summary.get("recommendations_count", 0))
        }
        
        for label, value in metrics_display.values():
            # Color code the value based on metric
            if "Issues" in label:
                value_style = "red bold" if value > 5 else "yellow" if value > 0 else "green"
                value_str = f"[{value_style}]{value}[/{value_style}]"
            else:
                value_str = str(value)
            
            table.add_row(label, value_str)
        
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
        """Print quality score with enhanced styling and color coding"""
        # Determine color based on score
        if score >= 90:
            color = "bright_green"
            emoji = "🌟"
            message = "Excellent!"
        elif score >= 80:
            color = "green"
            emoji = "✨"
            message = "Great!"
        elif score >= 70:
            color = "yellow"
            emoji = "👍"
            message = "Good"
        elif score >= 60:
            color = "orange3"
            emoji = "⚠️"
            message = "Fair"
        else:
            color = "red"
            emoji = "🔴"
            message = "Needs Work"
        
        # Create score display
        score_text = Text()
        score_text.append(f"{emoji} ", style="white")
        score_text.append(f"{score}", style=f"bold {color}")
        score_text.append("/100", style=f"{color}")
        score_text.append("\n", style="white")
        score_text.append(f"Grade: ", style="white")
        score_text.append(grade, style=f"bold {color}")
        score_text.append(f" • {message}", style=f"italic {color}")
        
        panel = Panel(
            Align.center(score_text),
            title="[bold bright_white]⭐ Code Quality Score[/bold bright_white]",
            border_style=color,
            box=box.DOUBLE,
            padding=(1, 2)
        )
        self.console.print(panel)
    
    def print_results(self, results: Dict[str, Any]):
        """Print comprehensive results with enhanced dashboard layout"""
        self.console.print("\n")
        
        # Header with session info
        session_id = results.get('session_id', 'N/A')
        timestamp = results.get('timestamp', 'N/A')
        
        header = Text()
        header.append("Review Results", style="bold bright_white")
        header.append("\n")
        header.append(f"Session: {session_id[:8]}...", style="dim cyan")
        header.append(" • ", style="dim")
        header.append(timestamp[:19] if timestamp != 'N/A' else 'N/A', style="dim cyan")
        
        self.console.print(Panel(
            Align.center(header),
            border_style="bright_cyan",
            box=box.DOUBLE,
            padding=(1, 2)
        ))
        self.console.print()
        
        # Print metrics if available
        if "agents" in results and "code_analyzer" in results["agents"]:
            metrics = results["agents"]["code_analyzer"].get("metrics", {})
            if metrics:
                self.console.print(self.create_metrics_table(metrics))
                self.console.print()
        
        # Print quality score
        if "agents" in results and "quality_reviewer" in results["agents"]:
            quality = results["agents"]["quality_reviewer"]
            score = quality.get("quality_score", 0)
            grade = quality.get("quality_grade", "N/A")
            self.print_quality_score(score, grade)
            self.console.print()
        
        # Print issues
        all_issues = []
        if "agents" in results:
            for agent_name, agent_data in results["agents"].items():
                if "issues" in agent_data:
                    all_issues.extend(agent_data["issues"])
        
        if all_issues:
            self.console.print(self.create_issues_table(all_issues))
            self.console.print()
        else:
            self.console.print(Panel(
                "[bold green]🎉 No issues found! Code looks great![/bold green]",
                border_style="green",
                box=box.ROUNDED
            ))
            self.console.print()
        
        # Print recommendations
        all_recommendations = []
        if "agents" in results:
            for agent_name, agent_data in results["agents"].items():
                if "recommendations" in agent_data:
                    all_recommendations.extend(agent_data["recommendations"])
        
        if all_recommendations:
            self.console.print(self.create_recommendations_tree(all_recommendations))
            self.console.print()
        
        # Print summary
        if "summary" in results:
            self.print_summary(results["summary"])
    
    def print_completion_banner(self, stats: Dict[str, Any] = None):  # type: ignore
        """Print a beautiful completion banner"""
        self.console.print()
        
        text = Text()
        text.append("✨ ", style="bright_yellow")
        text.append("Code Review Complete", style="bold bright_green")
        text.append(" ✨", style="bright_yellow")
        
        if stats:
            text.append("\n\n")
            text.append(f"⚡ Analyzed in {stats.get('duration', '0')}s", style="cyan")
            text.append(" • ")
            text.append(f"🎯 Quality: {stats.get('quality', 'N/A')}/100", style="bright_cyan")
        
        panel = Panel(
            Align.center(text),
            border_style="bright_green",
            box=box.DOUBLE,
            padding=(1, 4)
        )
        self.console.print(panel)
        self.console.print()
    
    def print_banner(self, text: str, style: str = "bright_cyan"):
        """Print a centered banner"""
        banner_text = Text(text, style=f"bold {style}")
        self.console.print()
        self.console.print(Panel(
            Align.center(banner_text),
            border_style=style,
            box=box.HEAVY,
            padding=(0, 2)
        ))
        self.console.print()
    
    def create_status_panel(self, title: str, items: List[tuple], status: str = "success"):
        """Create a status panel with items"""
        border_colors = {
            "success": "green",
            "warning": "yellow",
            "error": "red",
            "info": "cyan"
        }
        
        icons = {
            "success": "✓",
            "warning": "⚠",
            "error": "✗",
            "info": "ℹ"
        }
        
        color = border_colors.get(status, "cyan")
        icon = icons.get(status, "•")
        
        text = Text()
        for label, value in items:
            text.append(f"{icon} ", style=color)
            text.append(f"{label}: ", style="white")
            text.append(f"{value}\n", style=f"bold {color}")
        
        return Panel(
            text,
            title=f"[bold white]{title}[/bold white]",
            border_style=color,
            box=box.ROUNDED,
            padding=(1, 2)
        )

# Global instance
rich_output = RichOutput()
