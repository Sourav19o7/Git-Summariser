#!/usr/bin/env python3
"""
Git Commit Summarizer for Android Kotlin Projects
A Python script that analyzes git commits from the last 24 hours and generates AI-powered summaries using OpenAI.
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
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        
        self.openai_url = "https://api.openai.com/v1/chat/completions"
        self.ist_timezone = pytz.timezone('Asia/Kolkata')
        
    def check_git_repository(self) -> bool:
        return os.path.exists('.git')
    
    def get_ist_time(self, hours_back: int = 0) -> str:
        now = datetime.now(self.ist_timezone)
        if hours_back > 0:
            now = now - timedelta(hours=hours_back)
        return now.strftime('%Y-%m-%d %H:%M:%S')
    
    def execute_git_command(self, command: List[str]) -> List[str]:
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
                print(f"⚠️  Git command failed: {' '.join(command)}")
                print(f"Error: {result.stderr}")
                return []
                
        except subprocess.TimeoutExpired:
            print(f"⚠️  Git command timed out: {' '.join(command)}")
            return []
        except Exception as e:
            print(f"⚠️  Error executing git command: {e}")
            return []
    
    def get_commits_since(self, hours_back: int = 24) -> List[Dict]:
        since_time = self.get_ist_time(hours_back)
        
        # Get commit hashes and basic info
        commit_command = [
            'git', 'log',
            f'--since={since_time}',
            '--pretty=format:%H|%an|%ae|%ad|%s',
            '--date=iso',
            '--no-merges'
        ]
        
        commit_lines = self.execute_git_command(commit_command)
        commits = []
        
        for line in commit_lines:
            if '|' in line:
                parts = line.split('|', 4)
                if len(parts) >= 5:
                    hash_full = parts[0]
                    hash_short = hash_full[:8]
                    
                    # Get files changed in this commit
                    files_command = ['git', 'show', '--name-only', '--pretty=format:', hash_full]
                    files_changed = [f for f in self.execute_git_command(files_command) if f]
                    
                    # Get commit diff stats
                    stats_command = ['git', 'show', '--stat', '--pretty=format:', hash_full]
                    diff_stats = '\n'.join(self.execute_git_command(stats_command))
                    
                    commit_info = {
                        'hash': hash_short,
                        'hash_full': hash_full,
                        'author': parts[1],
                        'email': parts[2],
                        'date': parts[3],
                        'message': parts[4],
                        'files_changed': files_changed,
                        'kotlin_files': [f for f in files_changed if f.endswith('.kt')],
                        'diff_stats': diff_stats
                    }
                    commits.append(commit_info)
        
        return commits
    
    def get_repository_info(self) -> Dict:
        # Get current branch
        branch_command = ['git', 'branch', '--show-current']
        current_branch = self.execute_git_command(branch_command)
        branch = current_branch[0] if current_branch else 'unknown'
        
        # Get remote URL
        remote_command = ['git', 'config', '--get', 'remote.origin.url']
        remote_url = self.execute_git_command(remote_command)
        remote = remote_url[0] if remote_url else 'unknown'
        
        return {
            'branch': branch,
            'remote': remote,
            'timestamp': self.get_ist_time()
        }
    
    def analyze_commits(self, commits: List[Dict]) -> Dict:
        if not commits:
            return {
                'total_commits': 0,
                'total_files': 0,
                'kotlin_files': 0,
                'authors': [],
                'file_types': {},
                'kotlin_file_list': []
            }
        
        all_files = set()
        all_kotlin_files = set()
        authors = set()
        file_types = {}
        
        for commit in commits:
            authors.add(commit['author'])
            
            for file in commit['files_changed']:
                all_files.add(file)
                
                # Count file types
                ext = os.path.splitext(file)[1] or 'no_extension'
                file_types[ext] = file_types.get(ext, 0) + 1
            
            for kt_file in commit['kotlin_files']:
                all_kotlin_files.add(kt_file)
        
        return {
            'total_commits': len(commits),
            'total_files': len(all_files),
            'kotlin_files': len(all_kotlin_files),
            'authors': list(authors),
            'file_types': file_types,
            'kotlin_file_list': list(all_kotlin_files)
        }
    
    def generate_ai_summary(self, commits: List[Dict], analysis: Dict, repo_info: Dict) -> str:
        if not commits:
            return "No commits found in the specified time period."
        
        # Prepare commit details for AI analysis
        commit_details = []
        for commit in commits:
            detail = f"Commit {commit['hash']} by {commit['author']}:\n"
            detail += f"Message: {commit['message']}\n"
            detail += f"Files: {', '.join(commit['files_changed'][:10])}"  # Limit to first 10 files
            if len(commit['files_changed']) > 10:
                detail += f" ... and {len(commit['files_changed']) - 10} more"
            detail += f"\nKotlin files: {', '.join(commit['kotlin_files'])}\n"
            commit_details.append(detail)
        
        # Create prompt for OpenAI
        prompt = f"""
Analyze the following git commits from an Android Kotlin project and provide a comprehensive summary:

PROJECT CONTEXT:
- Repository Branch: {repo_info['branch']}
- Analysis Period: Last 24 hours (until {repo_info['timestamp']} IST)
- Total Commits: {analysis['total_commits']}
- Authors: {', '.join(analysis['authors'])}
- Files Modified: {analysis['total_files']}
- Kotlin Files: {analysis['kotlin_files']}

COMMIT DETAILS:
{chr(10).join(commit_details[:10])}  # Limit to first 10 commits to avoid token limits

FILE TYPE BREAKDOWN:
{json.dumps(analysis['file_types'], indent=2)}

Please provide a structured summary including:

1. **EXECUTIVE SUMMARY**: Brief overview of what was accomplished
2. **KEY FEATURES/CHANGES**: Main functionality added or modified
3. **TECHNICAL ANALYSIS**: Important code changes, architecture updates
4. **ANDROID-SPECIFIC INSIGHTS**: Impact on the Android app (UI, performance, etc.)
5. **DEVELOPMENT PATTERNS**: Notable patterns in commit messages and changes
6. **RECOMMENDATIONS**: Any suggestions based on the changes

Keep the summary concise but informative, focusing on the most impactful changes for stakeholders.
        """.strip()
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'gpt-4',
                'messages': [
                    {
                        'role': 'system', 
                        'content': 'You are an expert software architect and code reviewer specializing in Android development and Kotlin. Provide clear, actionable insights about code changes.'
                    },
                    {
                        'role': 'user', 
                        'content': prompt
                    }
                ],
                'temperature': 0.5,
                'max_tokens': 1500
            }
            
            response = requests.post(self.openai_url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                error_msg = f"OpenAI API Error {response.status_code}: {response.text}"
                print(f"⚠️  {error_msg}")
                return f"Failed to generate AI summary. {error_msg}"
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error calling OpenAI API: {e}"
            print(f"⚠️  {error_msg}")
            return f"Failed to generate AI summary due to network error: {e}"
        except Exception as e:
            error_msg = f"Error calling OpenAI API: {e}"
            print(f"⚠️  {error_msg}")
            return f"Failed to generate AI summary: {e}"
    
    def generate_markdown_report(self, commits: List[Dict], analysis: Dict, repo_info: Dict, ai_summary: str, hours_back: int) -> str:
        report = f"""# 📊 Git Activity Summary Report

**🕐 Generated At:** {repo_info['timestamp']} IST  
**📅 Analysis Period:** Last {hours_back} hours  
**🌿 Branch:** {repo_info['branch']}  
**📂 Repository:** {repo_info['remote']}

---

## 📈 Quick Statistics

| Metric | Value |
|--------|-------|
| **Total Commits** | {analysis['total_commits']} |
| **Files Modified** | {analysis['total_files']} |
| **Kotlin Files** | {analysis['kotlin_files']} |
| **Active Authors** | {len(analysis['authors'])} |

### 👥 Contributors
{', '.join(f'`{author}`' for author in analysis['authors'])}

### 📁 File Types Modified
"""
        
        for ext, count in sorted(analysis['file_types'].items(), key=lambda x: x[1], reverse=True):
            report += f"- **{ext or 'No extension'}**: {count} files\n"
        
        if commits:
            report += f"\n---\n\n## 📝 Recent Commits\n\n"
            
            for i, commit in enumerate(commits[:10], 1):  # Show first 10 commits
                report += f"### {i}. `{commit['hash']}` - {commit['author']}\n\n"
                report += f"**📅 Date:** {commit['date']}  \n"
                report += f"**💬 Message:** {commit['message']}  \n"
                
                if commit['kotlin_files']:
                    report += f"**🎯 Kotlin Files:** {', '.join(f'`{f}`' for f in commit['kotlin_files'])}  \n"
                
                if commit['files_changed']:
                    if len(commit['files_changed']) <= 5:
                        report += f"**📂 Files:** {', '.join(f'`{f}`' for f in commit['files_changed'])}  \n"
                    else:
                        report += f"**📂 Files:** {', '.join(f'`{f}`' for f in commit['files_changed'][:5])} ... and {len(commit['files_changed']) - 5} more  \n"
                
                report += "\n"
            
            if len(commits) > 10:
                report += f"*... and {len(commits) - 10} more commits*\n\n"
        
        if analysis['kotlin_file_list']:
            report += "---\n\n## 🎯 Kotlin Files Modified\n\n"
            for kt_file in sorted(analysis['kotlin_file_list']):
                report += f"- `{kt_file}`\n"
            report += "\n"
        
        report += "---\n\n## 🤖 AI-Generated Analysis\n\n"
        report += ai_summary
        
        report += f"\n\n---\n\n*Report generated by Git Commit Summarizer at {repo_info['timestamp']} IST*"
        
        return report
    
    def save_report(self, report: str, filename: Optional[str] = None) -> str:
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"git_summary_{timestamp}.md"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            return filename
        except Exception as e:
            print(f"⚠️  Error saving report: {e}")
            return ""
    
    def run_analysis(self, hours_back: int = 24, save_to_file: bool = True, verbose: bool = True) -> str:
        if verbose:
            print(f"🚀 Git Commit Summarizer for Android Kotlin Projects")
            print("=" * 60)
        
        # Check git repository
        if not self.check_git_repository():
            error_msg = "❌ Error: Not in a git repository. Please run from your project root."
            print(error_msg)
            return error_msg
        
        if verbose:
            print(f"🔍 Analyzing commits from the last {hours_back} hours...")
        
        # Get repository info
        repo_info = self.get_repository_info()
        if verbose:
            print(f"📂 Repository: {repo_info['branch']} branch")
        
        # Get commits
        commits = self.get_commits_since(hours_back)
        if verbose:
            print(f"📊 Found {len(commits)} commits")
        
        if not commits:
            no_commits_msg = f"No commits found in the last {hours_back} hours."
            print(f"ℹ️  {no_commits_msg}")
            return no_commits_msg
        
        # Analyze commits
        analysis = self.analyze_commits(commits)
        if verbose:
            print(f"🎯 {analysis['kotlin_files']} Kotlin files modified")
            print(f"👥 {len(analysis['authors'])} contributor(s): {', '.join(analysis['authors'])}")
        
        # Generate AI summary
        if verbose:
            print("🤖 Generating AI summary...")
        ai_summary = self.generate_ai_summary(commits, analysis, repo_info)
        
        # Generate report
        report = self.generate_markdown_report(commits, analysis, repo_info, ai_summary, hours_back)
        
        # Save report
        if save_to_file:
            filename = self.save_report(report)
            if filename and verbose:
                print(f"💾 Report saved to: {filename}")
        
        if verbose:
            print("=" * 60)
            print("✅ Analysis completed!")
        
        return report

def schedule_for_2_30_am():
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
    parser = argparse.ArgumentParser(description='Git Commit Summarizer for Android Kotlin Projects')
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
            print("📄 GENERATED REPORT:")
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