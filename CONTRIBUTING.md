# Contributing to hyred

Thank you for your interest in contributing to hyred! 🎉

## What is hyred?

**hyred** = git + hyred = Get Hired

A private, local CV & Cover Letter Generator that runs 100% on your machine. No external APIs. Complete privacy.

## How to Contribute

### Reporting Bugs

Before creating a bug report:
- Check existing issues to avoid duplicates
- Test with the latest version from `main` branch

When creating a bug report, include:
- Clear title and description
- Steps to reproduce the issue
- Expected vs actual behavior
- Screenshots if applicable
- System information (OS, Python version)

**Example:**
```markdown
**Title:** Application fails to start on macOS Sonoma

**Description:**
When running `streamlit run main_ui.py`, the app crashes immediately.

**Steps to Reproduce:**
1. Clone repository
2. Install dependencies
3. Run `streamlit run main_ui.py`

**Expected:** App starts on localhost:8501
**Actual:** Crash with error message

**System:**
- macOS 14.0
- Python 3.11
- M2 Mac
```

### Suggesting Features

Before suggesting a feature:
- Check existing issues for similar requests
- Ensure it aligns with hyred's privacy-first philosophy

When suggesting a feature:
- Clear, descriptive title
- Detailed description of the feature
- Use case and motivation
- Examples of how it would work

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly
5. Commit with clear messages
6. Push to your fork
7. Open a Pull Request

**PR Guidelines:**
- Keep PRs focused and manageable
- Include tests for new features
- Update documentation as needed
- Follow existing code style
- Ensure all tests pass

### Code Style

- **Python:** Follow PEP 8
- **Naming:** Descriptive variable and function names
- **Comments:** Explain why, not what
- **Type Hints:** Use where appropriate

**Example:**
```python
def generate_resume(job_description: str, cv_content: str) -> str:
    """
    Generate tailored resume from job description and CV.
    
    Args:
        job_description: The job posting text
        cv_content: Candidate's CV content
    
    Returns:
        Tailored resume as markdown string
    """
    # Implementation here
    pass
```

## Development Setup

### Prerequisites

- Python 3.11+
- pip or uv
- Ollama (for local LLM)
- Playwright (for web scraping)

### Installation

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/hyred.git
cd hyred

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install

# Start Ollama
ollama serve
ollama pull llama3.2

# Run the app
streamlit run main_ui.py --server.port=8501
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=hyred

# Run specific test file
pytest tests/test_resume_generator.py
```

## Project Structure

```
hyred/
├── main_ui.py              # Main Streamlit app
├── pages/                  # Feature pages
│   ├── 01_Import_Documents.py
│   ├── 02_Resume_Tools.py
│   ├── 03_Auto_Generate.py
│   ├── 04_Application_Tracker.py
│   ├── 05_Interview_Prep.py
│   ├── 06_Skills_Gap.py
│   ├── 07_CV_Versioning.py
│   └── 08_Job_Archive.py
├── assets/                 # Static assets (fonts, CSS)
├── docs/                   # Documentation
├── tests/                  # Test suite
├── requirements.txt        # Python dependencies
├── pyproject.toml         # Project configuration
└── README.md              # Project overview
```

## Areas for Contribution

### High Priority

- **Test Coverage:** Add unit and integration tests
- **Documentation:** Improve guides and examples
- **Performance:** Optimize RAG search and embedding generation
- **UI/UX:** Enhance user interface and experience

### Nice to Have

- **Additional Export Formats:** PDF, DOCX export
- **More Templates:** Resume and cover letter templates
- **Integrations:** LinkedIn, job board integrations
- **Analytics:** Usage statistics and insights

## Questions?

- **General Questions:** Open a GitHub Discussion
- **Bug Reports:** Create an Issue
- **Feature Requests:** Create an Issue with "enhancement" label

## Code of Conduct

Please note that this project is released with a [Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to hyred! 🚀
