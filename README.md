# 🐍 Git Commit Summarizer - Complete Setup & Usage Guide

A Python script that analyzes **YOUR commits across ALL branches** from the last 24 hours and generates AI-powered bullet-point summaries using OpenAI's GPT models.

## ✨ Features

- 🌿 **All Branches Analysis** - Checks both local and remote branches
- 👤 **Personal Focus** - Only analyzes commits authored by you
- 💰 **Cost Efficient** - Uses GPT-3.5-turbo (90% cheaper than GPT-4)
- 📋 **Bullet Point Summaries** - Up to 30 detailed bullet points (70 words each)
- 📝 **Comprehensive Logging** - Tracks operations, costs, and errors
- ⏰ **Scheduling Support** - Built-in 2:30 AM IST scheduler
- 🔧 **Easily Configurable** - Customize limits and AI settings

## 📋 Prerequisites

- **Python 3.7+** (recommended: Python 3.9+)
- **Git repository** (your Android Studio Kotlin project)
- **OpenAI API Key** ([Get one here](https://platform.openai.com/api-keys))
- **Internet connection** for OpenAI API calls

## 🚀 Quick Setup (5 Minutes)

### Step 1: Download and Create the Script

```bash
# Navigate to your Android Studio project directory
cd /path/to/your/android-project

# Create the Python script file
touch git_commit_summarizer.py

# Open the file in your preferred editor
nano git_commit_summarizer.py
# OR
code git_commit_summarizer.py  # VS Code
# OR
open -e git_commit_summarizer.py  # macOS TextEdit
```

**Copy the entire Python script** from the artifact above into `git_commit_summarizer.py` and save it.

### Step 2: Install Dependencies

```bash
# Install required Python packages
pip3 install requests pytz

# If you get permission errors, use:
pip3 install --user requests pytz

# Or create a virtual environment (recommended):
python3 -m venv git-summarizer-env
source git-summarizer-env/bin/activate  # Linux/Mac
# git-summarizer-env\Scripts\activate   # Windows
pip install requests pytz
```

### Step 3: Get OpenAI API Key

1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create a new API key
3. Copy the key (starts with `sk-`)

### Step 4: Set Environment Variable

**macOS/Linux:**
```bash
# Temporary (current session)
export OPENAI_API_KEY="your_api_key_here"

# Permanent (add to shell profile)
echo 'export OPENAI_API_KEY="your_api_key_here"' >> ~/.zshrc
source ~/.zshrc

# For bash users:
echo 'export OPENAI_API_KEY="your_api_key_here"' >> ~/.bashrc
source ~/.bashrc
```

**Windows:**
```cmd
# Temporary (current session)
set OPENAI_API_KEY=your_api_key_here

# Permanent
setx OPENAI_API_KEY "your_api_key_here"
```

### Step 5: Verify Setup

```bash
# Check if you're in a git repository
ls -la .git

# Check if the script exists
ls -la git_commit_summarizer.py

# Test the script
python3 git_commit_summarizer.py --help
```

## 🎯 Usage Examples

### Basic Usage

```bash
# Analyze your commits from last 24 hours across all branches
python3 git_commit_summarizer.py

# Quick test with last 2 hours
python3 git_commit_summarizer.py --hours 2
```

### Advanced Usage

```bash
# Different time ranges
python3 git_commit_summarizer.py --hours 12    # Last 12 hours
python3 git_commit_summarizer.py --hours 48    # Last 48 hours
python3 git_commit_summarizer.py --hours 168   # Last week

# Output options
python3 git_commit_summarizer.py --quiet       # Minimal console output
python3 git_commit_summarizer.py --no-save     # Don't save to file

# Custom API key (override environment variable)
python3 git_commit_summarizer.py --api-key "sk-your-key-here"

# Schedule for 2:30 AM IST (waits until then)
python3 git_commit_summarizer.py --schedule
```

### Combination Examples

```bash
# Quick 6-hour check without saving
python3 git_commit_summarizer.py --hours 6 --no-save --quiet

# Detailed 48-hour analysis with custom key
python3 git_commit_summarizer.py --hours 48 --api-key "sk-..."
```

## ⏰ Scheduling for 2:30 AM IST

### Option 1: Built-in Scheduler
```bash
# This waits until 2:30 AM IST, then runs automatically
python3 git_commit_summarizer.py --schedule
```

### Option 2: System Cron (Linux/macOS)

```bash
# Edit crontab
crontab -e

# Add this line for daily 2:30 AM runs
30 2 * * * cd /path/to/your/android-project && /usr/bin/python3 git_commit_summarizer.py

# For virtual environment users:
30 2 * * * cd /path/to/project && /path/to/git-summarizer-env/bin/python git_commit_summarizer.py
```

### Option 3: Windows Task Scheduler

1. Open **Task Scheduler**
2. Create **Basic Task** → "Git Daily Summary"
3. **Trigger**: Daily at 2:30 AM
4. **Action**: Start a program
   - **Program**: `python` or `C:\Python39\python.exe`
   - **Arguments**: `git_commit_summarizer.py`
   - **Start in**: Your project directory

## 📱 Android Studio Integration

### Method 1: External Tool
1. **File** → **Settings** → **Tools** → **External Tools**
2. Click **"+"** to add new tool
3. Configure:
   - **Name**: Git Commit Summary
   - **Program**: `python3` (or full path)
   - **Arguments**: `git_commit_summarizer.py`
   - **Working Directory**: `$ProjectFileDir$`

### Method 2: Terminal Integration
```bash
# Open Android Studio terminal (Alt+F12)
cd $PROJECT_DIR
python3 git_commit_summarizer.py
```

### Method 3: Run Configuration
1. **Run** → **Edit Configurations** → **"+"** → **Python**
2. Configure:
   - **Name**: Git Summarizer
   - **Script path**: `/path/to/git_commit_summarizer.py`
   - **Working directory**: Your project directory
   - **Environment variables**: `OPENAI_API_KEY=your_key`

## ⚙️ Configuration Options

The script has configurable variables at the top of the `GitCommitSummarizer` class:

```python
class GitCommitSummarizer:
    # Configuration variables - easily customizable
    MAX_COMMITS_TO_ANALYZE = 50      # Maximum commits to process
    MAX_BULLET_POINTS = 30           # Maximum bullet points in summary
    MAX_WORDS_PER_BULLET = 70        # Maximum words per bullet point
    AI_MODEL = "gpt-3.5-turbo"       # OpenAI model to use
    MAX_TOKENS = 800                 # Maximum tokens for AI response
    AI_TEMPERATURE = 0.3             # AI response creativity (0.0-1.0)
```

### Customization Examples:

**For Detailed Analysis:**
```python
MAX_COMMITS_TO_ANALYZE = 100
MAX_BULLET_POINTS = 50
MAX_WORDS_PER_BULLET = 100
AI_MODEL = "gpt-4"
MAX_TOKENS = 1500
```

**For Quick/Cheap Analysis:**
```python
MAX_COMMITS_TO_ANALYZE = 25
MAX_BULLET_POINTS = 15
MAX_WORDS_PER_BULLET = 40
AI_MODEL = "gpt-3.5-turbo"
MAX_TOKENS = 400
```

**Available AI Models:**
- `gpt-3.5-turbo` - Fast, cheap, good quality
- `gpt-4` - Best quality, more expensive
- `gpt-4o-mini` - Fastest, cheapest

## 📊 Sample Output

### Console Output:
```
🚀 Git Commit Summarizer - Analyzing MY changes across ALL branches
============================================================
🔍 Analyzing MY commits from the last 24 hours across all branches...
Searching for commits by: John Doe <john.doe@company.com>
Checking 8 branches: main, feature/auth, develop, release/v2.1...
Found 45 commits by you across all branches
AI Configuration: Model=gpt-3.5-turbo, MaxTokens=800, MaxBullets=30, MaxWords=70
🤖 Generating AI bullet-point summary...
OpenAI API usage - Prompt: 456, Completion: 234, Total: 690, Est. Cost: $0.0012
Generated 28 bullet points
💾 Report saved to: my_git_summary_20250612_143022.md
✅ Analysis completed!
📄 Log file: git_summary_log_20250612.log
```

### Generated Report:
```markdown
# 📊 My Git Activity Summary

**👤 Author:** John Doe <john.doe@company.com>
**🕐 Generated:** 2025-06-12 14:30:22 IST
**📅 Period:** Last 24 hours
**🌿 Branches:** main, feature/auth, develop, bugfix/login

## 📈 Quick Stats
• **My Commits:** 45 (analyzing up to 50)
• **Files Modified:** 67
• **Kotlin Files:** 23
• **Branches Touched:** 4

## 🎯 What I Actually Did
*(30 max bullets, 70 words each)*

• Implemented comprehensive user authentication system with JWT token management, including login, signup, password reset functionality, and automatic token refresh mechanism for seamless user experience across app sessions
• Fixed critical crash in profile image loading by implementing proper error handling and fallback mechanisms when network requests fail or image URLs are malformed or corrupted
• Added dark mode toggle feature in settings screen with system-wide theme switching, persistent user preference storage using SharedPreferences, and smooth transition animations between light and dark themes
• Refactored entire network layer architecture to use modern coroutines-based approach with proper error handling, retry logic, and centralized response processing for improved app reliability and performance
...

## 🔧 Kotlin Files I Modified
• `app/src/main/java/com/example/LoginActivity.kt`
• `app/src/main/java/com/example/AuthViewModel.kt`
• `app/src/main/java/com/example/UserRepository.kt`
...
```

## 🗂️ Generated Files

1. **`my_git_summary_YYYYMMDD_HHMMSS.md`** - Your detailed summary report
2. **`git_summary_log_YYYYMMDD.log`** - Operation logs with timestamps and costs

## 🛠️ Troubleshooting

### Common Issues:

**1. "No such file or directory"**
```bash
# Make sure you created the file and copied the script content
ls -la git_commit_summarizer.py
```

**2. "ModuleNotFoundError: No module named 'requests'"**
```bash
pip3 install requests pytz
```

**3. "OpenAI API key not found"**
```bash
# Check if environment variable is set
echo $OPENAI_API_KEY  # Linux/Mac
echo %OPENAI_API_KEY%  # Windows

# Set it if missing
export OPENAI_API_KEY="your_key_here"
```

**4. "Not in a git repository"**
```bash
# Make sure you're in your project root
cd /path/to/your/android-project
ls -la .git  # Should exist
```

**5. "No commits found"**
```bash
# Check if you have recent commits
git log --oneline --since="24 hours ago" --author="$(git config user.name)"

# Try different time ranges
python3 git_commit_summarizer.py --hours 48
```

**6. OpenAI API Errors**
```bash
# Test API key manually
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
```

### Performance Tips:

- **Large repos**: Reduce `MAX_COMMITS_TO_ANALYZE` for faster processing
- **Cost control**: Use `gpt-3.5-turbo` and lower `MAX_TOKENS`
- **Network issues**: Increase timeout in the script
- **Memory usage**: Process fewer commits if you have memory constraints

## 💰 Cost Estimation

- **GPT-3.5-turbo**: ~$0.001-0.003 per summary
- **GPT-4**: ~$0.01-0.05 per summary
- **Daily usage**: Typically under $0.10/day
- **Monthly**: $1-5 for regular use

The script logs exact costs for each API call.

## 🔄 Automation Scripts

### Daily Summary Script (Bash)
```bash
#!/bin/bash
# save as daily_git_summary.sh

cd /path/to/your/android-project
python3 git_commit_summarizer.py --hours 24

# Optional: Send via email
# mail -s "Daily Git Summary" your.email@domain.com < my_git_summary_*.md
```

### Weekly Summary Script
```bash
#!/bin/bash
# save as weekly_git_summary.sh

cd /path/to/your/android-project
python3 git_commit_summarizer.py --hours 168  # 24*7 hours
```

Make scripts executable:
```bash
chmod +x daily_git_summary.sh weekly_git_summary.sh
```

## 🎨 Advanced Features

### Multiple Repository Analysis
```python
# Modify the script to analyze multiple repos
repositories = [
    '/path/to/android-project-1',
    '/path/to/android-project-2'
]

for repo in repositories:
    os.chdir(repo)
    summarizer = GitCommitSummarizer()
    summarizer.run_analysis()
```

### Custom Git User Detection
```python
# Override git user detection in the script
def get_git_user_info(self) -> Dict[str, str]:
    return {
        "name": "Your Custom Name",
        "email": "your.custom@email.com"
    }
```

### Integration with Other Tools
```bash
# Slack integration example
python3 git_commit_summarizer.py --quiet > summary.txt
curl -X POST -H 'Content-type: application/json' \
  --data "{\"text\":\"$(cat summary.txt)\"}" \
  YOUR_SLACK_WEBHOOK_URL
```

## 📚 Additional Resources

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Git Log Documentation](https://git-scm.com/docs/git-log)
- [Python Requests Library](https://docs.python-requests.org/)
- [Cron Job Tutorial](https://crontab.guru/)

## 🤝 Contributing

Feel free to modify the script for your needs:
- Add support for other AI providers
- Implement different output formats
- Add more git analysis features
- Improve error handling

## 📄 License

This script is provided as-is for personal use. Modify freely according to your needs.

---

**Happy Coding! 🚀**