# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| main    | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of hyred seriously. If you believe you've found a security vulnerability, please report it to us.

### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via:
1. GitHub Security Advisories (preferred)
2. Email to: security@bitandmortar.com (if available)

### What to Include

Please include the following information in your report:

- **Description:** Clear description of the vulnerability
- **Impact:** Potential impact if exploited
- **Reproduction:** Steps to reproduce the issue
- **Environment:** OS, Python version, dependencies
- **Suggestions:** Any suggested fixes (optional)

### Response Timeline

- **Acknowledgment:** Within 48 hours
- **Initial Assessment:** Within 1 week
- **Fix Timeline:** Depends on severity
  - Critical: 24-48 hours
  - High: 1 week
  - Medium: 2-4 weeks
  - Low: Next release cycle

### Security Best Practices

Since hyred runs locally and processes sensitive personal data (CVs, cover letters, job applications), please be aware of:

#### Data Privacy
- All data stays local by design
- No external API calls for core functionality
- Optional NotebookLM integration requires explicit authentication

#### Dependencies
- Keep dependencies updated
- Review security advisories for:
  - Streamlit
  - LanceDB
  - sentence-transformers
  - Ollama

#### Local Security
- Run on trusted networks
- Keep Ollama models updated
- Review uploaded documents before sharing

### Security Features

hyred includes several security-by-design features:

1. **Local-First:** All processing happens on your machine
2. **No Cloud APIs:** Core functionality requires no external services
3. **Explicit Opt-In:** Optional features (NotebookLM) require explicit setup
4. **Data Isolation:** Each user's data stays in their local directory
5. **No Tracking:** No analytics or telemetry

### Past Security Advisories

| Date       | Severity | Description                    | Status  |
| ---------- | -------- | ------------------------------ | ------- |
| 2026-03-21 | Low      | Initial security review        | Fixed   |

### Recognition

We appreciate responsible disclosure and will acknowledge security researchers who help improve hyred's security (with permission).

---

Thank you for helping keep hyred secure! 🔒
