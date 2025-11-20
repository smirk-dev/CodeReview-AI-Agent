"""
GitHub Integration Module
Enables PR commenting, automated reviews, and GitHub Actions integration
"""

import os
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from github import Github, GithubException
from datetime import datetime

logger = logging.getLogger(__name__)

class GitHubIntegration:
    """Handles GitHub API integration for PR reviews"""
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub integration
        
        Args:
            token: GitHub personal access token (or read from GITHUB_TOKEN env)
        """
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.github = None
        
        if self.token:
            try:
                self.github = Github(self.token)
                logger.info("GitHub integration initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize GitHub client: {e}")
        else:
            logger.warning("No GitHub token provided. GitHub features will be disabled.")
    
    def is_available(self) -> bool:
        """Check if GitHub integration is available"""
        return self.github is not None
    
    def get_pr(self, repo_full_name: str, pr_number: int):
        """
        Get a pull request
        
        Args:
            repo_full_name: Repository in format 'owner/repo'
            pr_number: PR number
        """
        if not self.is_available():
            logger.error("GitHub integration not available")
            return None
        
        try:
            repo = self.github.get_repo(repo_full_name)
            pr = repo.get_pull(pr_number)
            return pr
        except GithubException as e:
            logger.error(f"Failed to get PR: {e}")
            return None
    
    def post_review_comment(
        self,
        repo_full_name: str,
        pr_number: int,
        results: Dict[str, Any],
        as_review: bool = True
    ) -> bool:
        """
        Post code review results as a PR comment or review
        
        Args:
            repo_full_name: Repository in format 'owner/repo'
            pr_number: PR number
            results: Review results dict
            as_review: If True, post as review; if False, post as comment
        """
        if not self.is_available():
            logger.error("GitHub integration not available")
            return False
        
        try:
            pr = self.get_pr(repo_full_name, pr_number)
            if not pr:
                return False
            
            # Generate review markdown
            from utils.report_generator import report_generator
            markdown = report_generator.generate_markdown_report(results)
            
            if as_review:
                # Determine review event based on issues
                issues_count = results.get('summary', {}).get('issues_found', 0)
                quality_score = 0
                
                if 'agents' in results and 'quality_reviewer' in results['agents']:
                    quality_score = results['agents']['quality_reviewer'].get('quality_score', 0)
                
                # Approve if score is high and few issues
                if quality_score >= 90 and issues_count <= 2:
                    event = "APPROVE"
                elif issues_count > 5 or quality_score < 60:
                    event = "REQUEST_CHANGES"
                else:
                    event = "COMMENT"
                
                pr.create_review(body=markdown, event=event)
                logger.info(f"Posted review to PR #{pr_number} with event {event}")
            else:
                pr.create_issue_comment(markdown)
                logger.info(f"Posted comment to PR #{pr_number}")
            
            return True
        
        except GithubException as e:
            logger.error(f"Failed to post comment: {e}")
            return False
    
    def post_inline_comments(
        self,
        repo_full_name: str,
        pr_number: int,
        results: Dict[str, Any]
    ) -> int:
        """
        Post inline comments on specific lines with issues
        
        Args:
            repo_full_name: Repository in format 'owner/repo'
            pr_number: PR number
            results: Review results dict
        
        Returns:
            Number of comments posted
        """
        if not self.is_available():
            logger.error("GitHub integration not available")
            return 0
        
        try:
            pr = self.get_pr(repo_full_name, pr_number)
            if not pr:
                return 0
            
            # Get the latest commit
            commits = list(pr.get_commits())
            if not commits:
                logger.warning("No commits found in PR")
                return 0
            
            latest_commit = commits[-1]
            
            # Collect all issues
            comments_posted = 0
            if 'agents' in results:
                for agent_name, agent_data in results['agents'].items():
                    if 'issues' in agent_data:
                        for issue in agent_data['issues']:
                            line = issue.get('line', 1)
                            
                            comment_body = (
                                f"**{issue.get('severity', 'info').upper()}**: "
                                f"{issue.get('type', 'Issue')}\n\n"
                                f"{issue.get('description', '')}\n\n"
                            )
                            
                            if 'suggestion' in issue:
                                comment_body += f"💡 **Suggestion:** {issue['suggestion']}"
                            
                            try:
                                # Try to post inline comment
                                pr.create_review_comment(
                                    body=comment_body,
                                    commit=latest_commit,
                                    path="code.py",  # Default path, should be customized
                                    line=line
                                )
                                comments_posted += 1
                            except GithubException as e:
                                logger.warning(f"Failed to post inline comment: {e}")
            
            logger.info(f"Posted {comments_posted} inline comments to PR #{pr_number}")
            return comments_posted
        
        except GithubException as e:
            logger.error(f"Failed to post inline comments: {e}")
            return 0
    
    def get_pr_files(self, repo_full_name: str, pr_number: int) -> List[str]:
        """
        Get list of files changed in a PR
        
        Args:
            repo_full_name: Repository in format 'owner/repo'
            pr_number: PR number
        
        Returns:
            List of file paths
        """
        if not self.is_available():
            return []
        
        try:
            pr = self.get_pr(repo_full_name, pr_number)
            if not pr:
                return []
            
            files = [f.filename for f in pr.get_files()]
            logger.info(f"Found {len(files)} changed files in PR #{pr_number}")
            return files
        
        except GithubException as e:
            logger.error(f"Failed to get PR files: {e}")
            return []
    
    def get_pr_diff(self, repo_full_name: str, pr_number: int) -> str:
        """
        Get the diff for a PR
        
        Args:
            repo_full_name: Repository in format 'owner/repo'
            pr_number: PR number
        
        Returns:
            Diff text
        """
        if not self.is_available():
            return ""
        
        try:
            pr = self.get_pr(repo_full_name, pr_number)
            if not pr:
                return ""
            
            # Get diff as text
            files = pr.get_files()
            diff_text = ""
            
            for file in files:
                diff_text += f"\n\n--- {file.filename} ---\n"
                diff_text += file.patch if file.patch else ""
            
            return diff_text
        
        except GithubException as e:
            logger.error(f"Failed to get PR diff: {e}")
            return ""
    
    def set_commit_status(
        self,
        repo_full_name: str,
        sha: str,
        state: str,
        description: str,
        context: str = "CodeReview-AI-Agent"
    ) -> bool:
        """
        Set commit status (for CI/CD integration)
        
        Args:
            repo_full_name: Repository in format 'owner/repo'
            sha: Commit SHA
            state: 'pending', 'success', 'failure', 'error'
            description: Status description
            context: Status context name
        """
        if not self.is_available():
            return False
        
        try:
            repo = self.github.get_repo(repo_full_name)
            commit = repo.get_commit(sha)
            commit.create_status(
                state=state,
                description=description,
                context=context
            )
            logger.info(f"Set commit status to '{state}' for {sha[:7]}")
            return True
        
        except GithubException as e:
            logger.error(f"Failed to set commit status: {e}")
            return False

class GitHubActionsHelper:
    """Helper for GitHub Actions integration"""
    
    @staticmethod
    def is_running_in_actions() -> bool:
        """Check if code is running in GitHub Actions"""
        return os.getenv('GITHUB_ACTIONS') == 'true'
    
    @staticmethod
    def get_pr_number() -> Optional[int]:
        """Get PR number from GitHub Actions environment"""
        # From pull_request event
        pr_ref = os.getenv('GITHUB_REF')
        if pr_ref and pr_ref.startswith('refs/pull/'):
            try:
                return int(pr_ref.split('/')[2])
            except (IndexError, ValueError):
                pass
        
        # From environment variable set in workflow
        pr_num = os.getenv('PR_NUMBER')
        if pr_num:
            try:
                return int(pr_num)
            except ValueError:
                pass
        
        return None
    
    @staticmethod
    def get_repository() -> Optional[str]:
        """Get repository name from GitHub Actions environment"""
        return os.getenv('GITHUB_REPOSITORY')
    
    @staticmethod
    def get_sha() -> Optional[str]:
        """Get commit SHA from GitHub Actions environment"""
        return os.getenv('GITHUB_SHA')
    
    @staticmethod
    def set_output(name: str, value: str):
        """Set output variable for GitHub Actions"""
        if GitHubActionsHelper.is_running_in_actions():
            output_file = os.getenv('GITHUB_OUTPUT')
            if output_file:
                with open(output_file, 'a') as f:
                    f.write(f"{name}={value}\n")
    
    @staticmethod
    def set_env(name: str, value: str):
        """Set environment variable for GitHub Actions"""
        if GitHubActionsHelper.is_running_in_actions():
            env_file = os.getenv('GITHUB_ENV')
            if env_file:
                with open(env_file, 'a') as f:
                    f.write(f"{name}={value}\n")
    
    @staticmethod
    def log_error(message: str):
        """Log error in GitHub Actions format"""
        print(f"::error::{message}")
    
    @staticmethod
    def log_warning(message: str):
        """Log warning in GitHub Actions format"""
        print(f"::warning::{message}")
    
    @staticmethod
    def log_info(message: str):
        """Log info in GitHub Actions format"""
        print(f"::notice::{message}")

# Global instance
github_integration = GitHubIntegration()
