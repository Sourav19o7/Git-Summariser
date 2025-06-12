#!/usr/bin/env python3
"""
Git Commit Summarizer for Android Kotlin Projects
A Python script that analyzes git commits from all branches for your changes only and generates AI-powered summaries using OpenAI.
"""

import os
import sys
import subprocess
import json
import requests
from datetime import datetime, timedelta
import pytz
from typing import List, Dict, Optional
import argparse
import time

class GitCommitSummarizer:
    # Configuration variables - easily customizable
    MAX_COMMITS_TO_ANALYZE = 50      # Maximum commits to process
    MAX_BULLET_POINTS = 6            # CHANGED: Reduced from 30 to 6 for high-level summary
    MAX_WORDS_PER_BULLET = 100       # CHANGED: Increased from 70 to 100 to allow more detailed technical descriptions
    AI_MODEL = "gpt-3.5-turbo"       # OpenAI model to use
    MAX_TOKENS = 800                 # Maximum tokens for AI response
    AI_TEMPERATURE = 0.3             # AI response creativity (0.0-1.0)

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the summarizer with OpenAI API key."""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")

        self.openai_url = "https://api.openai.com/v1/chat/completions"
        self.ist_timezone = pytz.timezone('Asia/Kolkata')
        self.log_file = f"git_summary_log_{datetime.now().strftime('%Y%m%d')}.log"

    def log_message(self, message: str, level: str = "INFO"):
        """Log message to both console and file."""
        timestamp = datetime.now(self.ist_timezone).strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] [{level}] {message}"

        print(log_entry)

        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry + '\n')
        except Exception as e:
            print(f"Warning: Could not write to log file: {e}")

    def check_git_repository(self) -> bool:
        """Check if current directory is a git repository."""
        return os.path.exists('.git')

    def get_git_user_info(self) -> Dict[str, str]:
        """Get the current git user information."""
        try:
            name_result = subprocess.run(['git', 'config', 'user.name'], capture_output=True, text=True)
            email_result = subprocess.run(['git', 'config', 'user.email'], capture_output=True, text=True)

            user_name = name_result.stdout.strip() if name_result.returncode == 0 else ""
            user_email = email_result.stdout.strip() if email_result.returncode == 0 else ""

            return {"name": user_name, "email": user_email}
        except Exception as e:
            self.log_message(f"Error getting git user info: {e}", "WARNING")
            return {"name": "", "email": ""}

    def get_ist_time(self, hours_back: int = 0) -> str:
        """Get IST time string, optionally going back specified hours."""
        now = datetime.now(self.ist_timezone)
        if hours_back > 0:
            now = now - timedelta(hours=hours_back)
        return now.strftime('%Y-%m-%d %H:%M:%S')

    def execute_git_command(self, command: List[str]) -> List[str]:
        """Execute a git command and return output lines."""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30,
                cwd='.'
            )

            if result.returncode == 0:
                return [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            else:
                self.log_message(f"Git command failed: {' '.join(command)} - {result.stderr}", "WARNING")
                return []

        except subprocess.TimeoutExpired:
            self.log_message(f"Git command timed out: {' '.join(command)}", "WARNING")
            return []
        except Exception as e:
            self.log_message(f"Error executing git command: {e}", "ERROR")
            return []

    def get_all_branches(self) -> List[str]:
        """Get all branches (local and remote)."""
        # Get local branches
        local_branches = self.execute_git_command(['git', 'branch', '--format=%(refname:short)'])

        # Get remote branches
        remote_branches = self.execute_git_command(['git', 'branch', '-r', '--format=%(refname:short)'])

        # Combine and clean up
        all_branches = set()

        for branch in local_branches:
            if branch and not branch.startswith('*'):
                all_branches.add(branch.strip('* '))

        for branch in remote_branches:
            if branch and not branch.startswith('origin/HEAD'):
                # Remove 'origin/' prefix for consistency
                clean_branch = branch.replace('origin/', '')
                all_branches.add(clean_branch)

        return list(all_branches)

    def get_my_commits_from_all_branches(self, hours_back: int = 24) -> List[Dict]:
        """Get commits from all branches that belong to the current user."""
        user_info = self.get_git_user_info()
        since_time = self.get_ist_time(hours_back)

        self.log_message(f"Searching for commits by: {user_info['name']} <{user_info['email']}>")
        self.log_message(f"Time range: Since {since_time} IST")

        all_commits = []
        branches = self.get_all_branches()

        self.log_message(f"Checking {len(branches)} branches: {', '.join(branches[:5])}{'...' if len(branches) > 5 else ''}")

        for branch in branches:
            try:
                # Build author filter
                author_filters = []
                if user_info['name']:
                    author_filters.extend(['--author', user_info['name']])
                if user_info['email']:
                    author_filters.extend(['--author', user_info['email']])

                # Get commits for this branch
                commit_command = [
                    'git', 'log', branch,
                    f'--since={since_time}',
                    '--pretty=format:%H|%an|%ae|%ad|%s|%D',
                    '--date=iso',
                    '--no-merges'
                ] + author_filters

                commit_lines = self.execute_git_command(commit_command)

                for line in commit_lines:
                    if '|' in line:
                        parts = line.split('|', 5)
                        if len(parts) >= 5:
                            hash_full = parts[0]

                            # Skip if we already have this commit
                            if any(c['hash_full'] == hash_full for c in all_commits):
                                continue

                            # Check if this commit is actually by the current user
                            author_name = parts[1]
                            author_email = parts[2]

                            is_my_commit = (
                                (user_info['name'] and user_info['name'].lower() in author_name.lower()) or
                                (user_info['email'] and user_info['email'].lower() in author_email.lower())
                            )

                            if not is_my_commit:
                                continue

                            hash_short = hash_full[:8]
                            branch_info = parts[5] if len(parts) > 5 else branch

                            # Get files changed in this commit
                            files_command = ['git', 'show', '--name-only', '--pretty=format:', hash_full]
                            files_changed = [f for f in self.execute_git_command(files_command) if f]

                            # Get commit diff summary
                            diff_command = ['git', 'show', '--stat', '--pretty=format:', hash_full]
                            diff_stats = '\n'.join(self.execute_git_command(diff_command))

                            commit_info = {
                                'hash': hash_short,
                                'hash_full': hash_full,
                                'author': author_name,
                                'email': author_email,
                                'date': parts[3],
                                'message': parts[4],
                                'branch': branch,
                                'branch_info': branch_info,
                                'files_changed': files_changed,
                                'kotlin_files': [f for f in files_changed if f.endswith('.kt')],
                                'android_files': [f for f in files_changed if f.endswith(('.kt', '.xml', '.java', '.gradle'))],
                                'diff_stats': diff_stats
                            }
                            all_commits.append(commit_info)

            except Exception as e:
                self.log_message(f"Error processing branch {branch}: {e}", "WARNING")
                continue

        # Sort commits by date (newest first) and limit to MAX_COMMITS_TO_ANALYZE
        all_commits.sort(key=lambda x: x['date'], reverse=True)
        limited_commits = all_commits[:self.MAX_COMMITS_TO_ANALYZE]

        if len(all_commits) > self.MAX_COMMITS_TO_ANALYZE:
            self.log_message(f"Limited analysis to {self.MAX_COMMITS_TO_ANALYZE} most recent commits (found {len(all_commits)} total)")

        self.log_message(f"Found {len(limited_commits)} commits by you across all branches (showing {len(limited_commits)} most recent)")
        return limited_commits

    def analyze_my_commits(self, commits: List[Dict]) -> Dict:
        """Analyze commits to extract statistics and insights."""
        if not commits:
            return {
                'total_commits': 0,
                'total_files': 0,
                'kotlin_files': 0,
                'android_files': 0,
                'branches': [],
                'file_types': {},
                'kotlin_file_list': [],
                'android_file_list': []
            }

        all_files = set()
        all_kotlin_files = set()
        all_android_files = set()
        branches = set()
        file_types = {}

        for commit in commits:
            branches.add(commit['branch'])

            for file in commit['files_changed']:
                all_files.add(file)

                # Count file types
                ext = os.path.splitext(file)[1] or 'no_extension'
                file_types[ext] = file_types.get(ext, 0) + 1

            for kt_file in commit['kotlin_files']:
                all_kotlin_files.add(kt_file)

            for android_file in commit['android_files']:
                all_android_files.add(android_file)

        return {
            'total_commits': len(commits),
            'total_files': len(all_files),
            'kotlin_files': len(all_kotlin_files),
            'android_files': len(all_android_files),
            'branches': list(branches),
            'file_types': file_types,
            'kotlin_file_list': list(all_kotlin_files),
            'android_file_list': list(all_android_files)
        }

    def generate_bullet_summary(self, commits: List[Dict], analysis: Dict) -> str:
        """Generate AI-powered bullet point summary using cheaper GPT model."""
        # CHANGED: Updated to focus on high-level technical summary
        if not commits:
            return "• No commits found in the specified time period by you."

        # Log configuration being used
        self.log_message(f"AI Configuration: Model={self.AI_MODEL}, MaxTokens={self.MAX_TOKENS}, MaxBullets={self.MAX_BULLET_POINTS}, MaxWords={self.MAX_WORDS_PER_BULLET}")

        # Prepare concise commit info for AI (limit to prevent token overflow)
        commits_to_analyze = min(len(commits), 20)  # Analyze max 20 commits for token efficiency
        commit_summaries = []

        for commit in commits[:commits_to_analyze]:
            summary = f"[{commit['branch']}] {commit['message']}"
            if commit['kotlin_files']:
                summary += f" (Kotlin: {', '.join(commit['kotlin_files'][:3])})"
            commit_summaries.append(summary)

        # CHANGED: Updated prompt to focus on high-level technical summary with numbers
        prompt = f"""
Analyze these git commits from an Android Kotlin project and provide a HIGH-LEVEL TECHNICAL SUMMARY of the overall work accomplished:

COMMITS ANALYZED: {commits_to_analyze} of {len(commits)} total commits

COMMIT DETAILS:
{chr(10).join(commit_summaries)}

PROJECT STATISTICS:
- Total commits: {analysis['total_commits']}
- Branches worked on: {', '.join(analysis['branches'][:5])}
- Total files modified: {analysis['total_files']}
- Kotlin files modified: {analysis['kotlin_files']}
- Android-specific files: {analysis['android_files']}
- File types distribution: {dict(list(analysis['file_types'].items())[:5])}

Provide EXACTLY {self.MAX_BULLET_POINTS} bullet points that summarize the OVERALL TECHNICAL WORK at a HIGH LEVEL:

Requirements:
• Exactly {self.MAX_BULLET_POINTS} bullet points maximum
• Focus on MAJOR features, components, or architectural changes - not individual bug fixes
• Include specific numbers (files modified, features added, components built, etc.)
• Be technical but concise - mention frameworks, patterns, architectures used
• Group related changes together (e.g., "Implemented user authentication system across 8 files")
• Prioritize impact: major features > refactoring > bug fixes > minor changes
• Use format: "• [Technical accomplishment] with [numbers/scope] affecting [components/areas]"

Examples of good high-level bullets:
• "Implemented complete user authentication system across 12 Kotlin files with JWT token management and biometric login"
• "Refactored data layer architecture affecting 15 repository classes, introducing Repository pattern with Room database integration"
• "Built real-time messaging feature with WebSocket integration across 8 UI components and 5 data models"

Format as bullet points starting with •
Focus on WHAT was built/changed, not just WHERE
        """.strip()

        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            payload = {
                'model': self.AI_MODEL,
                'messages': [
                    {
                        'role': 'system',
                        'content': f'You are a senior software architect reviewing code changes. Provide exactly {self.MAX_BULLET_POINTS} high-level technical bullet points summarizing major accomplishments, not individual commits. Focus on overall features and architectural changes with specific numbers.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'temperature': self.AI_TEMPERATURE,
                'max_tokens': self.MAX_TOKENS
            }

            response = requests.post(self.openai_url, headers=headers, json=payload, timeout=60)

            if response.status_code == 200:
                result = response.json()
                summary = result['choices'][0]['message']['content']

                # Log token usage for cost tracking
                if 'usage' in result:
                    usage = result['usage']
                    estimated_cost = (usage.get('prompt_tokens', 0) * 0.0015 + usage.get('completion_tokens', 0) * 0.002) / 1000
                    self.log_message(f"OpenAI API usage - Prompt: {usage.get('prompt_tokens', 0)}, Completion: {usage.get('completion_tokens', 0)}, Total: {usage.get('total_tokens', 0)}, Est. Cost: ${estimated_cost:.4f}")

                # Count actual bullet points generated
                bullet_count = len([line for line in summary.split('\n') if line.strip().startswith('•')])
                self.log_message(f"Generated {bullet_count} bullet points")

                return summary
            else:
                error_msg = f"OpenAI API Error {response.status_code}: {response.text}"
                self.log_message(error_msg, "ERROR")
                return f"• AI summary failed: {error_msg}"

        except requests.exceptions.RequestException as e:
            error_msg = f"Network error calling OpenAI API: {e}"
            self.log_message(error_msg, "ERROR")
            return f"• AI summary failed due to network error: {e}"
        except Exception as e:
            error_msg = f"Error calling OpenAI API: {e}"
            self.log_message(error_msg, "ERROR")
            return f"• AI summary failed: {e}"

    def generate_report(self, commits: List[Dict], analysis: Dict, ai_summary: str, hours_back: int) -> str:
        """Generate a concise report focused on bullet points."""
        user_info = self.get_git_user_info()
        timestamp = self.get_ist_time()

        # Count actual commits processed vs total found
        total_found = len(commits) if len(commits) <= self.MAX_COMMITS_TO_ANALYZE else f"{len(commits)}+ (limited to {self.MAX_COMMITS_TO_ANALYZE})"

        # CHANGED: Updated report description to reflect high-level focus
        report = f"""# 📊 My Git Activity Summary - High-Level Technical Overview

**👤 Author:** {user_info['name']} <{user_info['email']}>
**🕐 Generated:** {timestamp} IST
**📅 Period:** Last {hours_back} hours
**🌿 Branches:** {', '.join(analysis['branches'][:5])}{'...' if len(analysis['branches']) > 5 else ''}

## 📈 Quick Stats
• **My Commits:** {analysis['total_commits']} (analyzing up to {self.MAX_COMMITS_TO_ANALYZE})
• **Files Modified:** {analysis['total_files']}
• **Kotlin Files:** {analysis['kotlin_files']}
• **Branches Touched:** {len(analysis['branches'])}

## 🎯 Major Technical Accomplishments
*High-level summary of overall work (max {self.MAX_BULLET_POINTS} bullets)*

{ai_summary}

"""

        if analysis['kotlin_file_list']:
            report += "## 🔧 Kotlin Files I Modified\n"
            for kt_file in sorted(analysis['kotlin_file_list'][:15]):  # Show top 15
                report += f"• `{kt_file}`\n"
            if len(analysis['kotlin_file_list']) > 15:
                report += f"• ... and {len(analysis['kotlin_file_list']) - 15} more Kotlin files\n"
            report += "\n"

        if commits:
            report += "## 📝 My Recent Commits\n"
            commits_to_show = min(len(commits), 10)  # Show max 10 commits
            for i, commit in enumerate(commits[:commits_to_show], 1):
                report += f"{i}. **{commit['hash']}** [{commit['branch']}] {commit['message']}\n"
            if len(commits) > commits_to_show:
                report += f"   ... and {len(commits) - commits_to_show} more commits\n"
            report += "\n"

        report += f"---\n*Generated by Git Commit Summarizer at {timestamp} IST*\n"
        report += f"*Configuration: Max {self.MAX_COMMITS_TO_ANALYZE} commits, {self.MAX_BULLET_POINTS} high-level bullets, {self.MAX_WORDS_PER_BULLET} words each*\n"
        report += f"*Log file: {self.log_file}*"

        return report

    def save_report(self, report: str, filename: Optional[str] = None) -> str:
        """Save the report to a file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"my_git_summary_{timestamp}.md"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            self.log_message(f"Report saved to: {filename}")
            return filename
        except Exception as e:
            self.log_message(f"Error saving report: {e}", "ERROR")
            return ""

    def run_analysis(self, hours_back: int = 24, save_to_file: bool = True, verbose: bool = True) -> str:
        """Run the complete analysis and return the report."""
        if verbose:
            self.log_message("🚀 Git Commit Summarizer - High-Level Technical Analysis of MY changes")
            self.log_message("=" * 60)

        # Check git repository
        if not self.check_git_repository():
            error_msg = "❌ Error: Not in a git repository. Please run from your project root."
            self.log_message(error_msg, "ERROR")
            return error_msg

        self.log_message(f"🔍 Analyzing MY commits from the last {hours_back} hours across all branches...")

        # Get my commits from all branches
        commits = self.get_my_commits_from_all_branches(hours_back)

        if not commits:
            no_commits_msg = f"No commits by you found in the last {hours_back} hours across any branch."
            self.log_message(no_commits_msg, "INFO")
            return no_commits_msg

        # Analyze commits
        analysis = self.analyze_my_commits(commits)
        self.log_message(f"📊 Analysis: {analysis['total_commits']} commits, {analysis['kotlin_files']} Kotlin files, {len(analysis['branches'])} branches")

        # Generate AI bullet summary
        self.log_message("🤖 Generating high-level technical summary...")
        ai_summary = self.generate_bullet_summary(commits, analysis)

        # Generate report
        report = self.generate_report(commits, analysis, ai_summary, hours_back)

        # Save report
        if save_to_file:
            filename = self.save_report(report)
            if filename:
                self.log_message(f"💾 Report saved to: {filename}")

        self.log_message("✅ Analysis completed!")
        self.log_message(f"📄 Log file: {self.log_file}")

        return report

def schedule_for_2_30_am():
    """Schedule the script to run at 2:30 AM IST."""
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)

    # Calculate next 2:30 AM
    target_time = now.replace(hour=2, minute=30, second=0, microsecond=0)
    if now >= target_time:
        target_time += timedelta(days=1)

    wait_seconds = (target_time - now).total_seconds()
    wait_hours = wait_seconds / 3600

    print(f"⏰ Scheduled to run at 2:30 AM IST")
    print(f"🕐 Next run: {target_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"⏳ Waiting {wait_hours:.1f} hours...")

    time.sleep(wait_seconds)

    # Run the analysis
    summarizer = GitCommitSummarizer()
    report = summarizer.run_analysis()
    print("\n" + "=" * 60)
    print(report)

def main():
    """Main function with command line argument parsing."""
    parser = argparse.ArgumentParser(description='Git Commit Summarizer - High-level technical summary of MY changes')
    parser.add_argument('--hours', type=int, default=24, help='Hours back to analyze (default: 24)')
    parser.add_argument('--no-save', action='store_true', help='Don\'t save report to file')
    parser.add_argument('--quiet', action='store_true', help='Quiet mode - minimal output')
    parser.add_argument('--schedule', action='store_true', help='Schedule to run at 2:30 AM IST')
    parser.add_argument('--api-key', type=str, help='OpenAI API key (overrides environment variable)')

    args = parser.parse_args()

    # Handle scheduling
    if args.schedule:
        schedule_for_2_30_am()
        return

    try:
        # Create summarizer
        summarizer = GitCommitSummarizer(api_key=args.api_key)

        # Run analysis
        report = summarizer.run_analysis(
            hours_back=args.hours,
            save_to_file=not args.no_save,
            verbose=not args.quiet
        )

        # Print report if not in quiet mode
        if not args.quiet:
            print("\n" + "=" * 60)
            print("📄 HIGH-LEVEL TECHNICAL SUMMARY:")
            print("=" * 60)
            print(report)

    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("💡 Set your OpenAI API key: export OPENAI_API_KEY='your_key_here'")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  Analysis interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()