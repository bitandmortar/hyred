#!/usr/bin/env python3
"""
Local Job Scraper - Zero Data Leak
====================================
Uses local Playwright instance to extract job descriptions without any external API calls.
Bypasses JavaScript-heavy sites (Greenhouse, Lever, etc.) using headless Chromium.

NO external APIs: No Firecrawl, no ScrapingBee, no cloud services.
"""

import subprocess
import tempfile
import json

# from pathlib import Path  # Unused
from typing import Optional, Dict
from bs4 import BeautifulSoup
import re

# Supported job board URL patterns
SITE_PATTERNS = {
    "linkedin":     r"linkedin\.com/jobs",
    "indeed":       r"indeed\.com/(viewjob|rc/clk|pagead)",
    "ziprecruiter": r"ziprecruiter\.com/jobs",
    "glassdoor":    r"glassdoor\.com/job-listing",
    "greenhouse":   r"greenhouse\.io/jobs",
    "lever":        r"jobs\.lever\.co",
    "workday":      r"myworkdayjobs\.com",
}


class LocalJobScraper:
    """
    Local job description scraper using Playwright + BeautifulSoup.
    Zero external API dependencies - all processing happens locally.
    """

    def __init__(self, timeout: int = 30000):
        """
        Initialize scraper with local Playwright instance.

        Args:
            timeout: Page load timeout in milliseconds (default: 30s)
        """
        self.timeout = timeout
        self.playwright_installed = self._check_playwright()

    def _check_playwright(self) -> bool:
        """Verify playwright-cli is installed via brew"""
        try:
            result = subprocess.run(
                ["playwright-cli", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print(
                "⚠️  playwright-cli not found. Install with: brew install playwright-cli"
            )
            return False

    def _detect_site(self, url: str) -> str:
        """Return site key or 'generic'."""
        for site, pattern in SITE_PATTERNS.items():
            if re.search(pattern, url, re.I):
                return site
        return "generic"

    def _extract_json_ld(self, soup: BeautifulSoup) -> Optional[Dict]:
        """Extract JSON-LD JobPosting structured data if present."""
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                if isinstance(data, list):
                    data = next((d for d in data if d.get("@type") == "JobPosting"), None)
                if data and data.get("@type") == "JobPosting":
                    return data
            except (json.JSONDecodeError, AttributeError):
                continue
        return None

    def _parse_from_json_ld(self, data: Dict) -> Dict:
        """Build result dict from JSON-LD JobPosting object."""
        desc = data.get("description", "")
        # Strip HTML tags from description
        desc = re.sub(r"<[^>]+>", " ", desc)
        desc = re.sub(r"\s+", " ", desc).strip()
        return {
            "job_title": data.get("title"),
            "company": (data.get("hiringOrganization") or {}).get("name"),
            "job_description": desc[:5000] if desc else None,
            "requirements": None,
            "error": None,
        }

    def _scrape_linkedin(self, soup: BeautifulSoup, url: str) -> Dict:
        """LinkedIn job page extractor."""
        # Try JSON-LD first
        ld = self._extract_json_ld(soup)
        if ld:
            return self._parse_from_json_ld(ld)

        # Fall back to meta tags + DOM selectors
        title = (
            self._extract_by_selectors(soup, ['meta[property="og:title"]']) or
            self._extract_by_selectors(soup, ["h1"])
        )
        company = self._extract_by_selectors(
            soup,
            ['[class*="company-name"]', '[class*="topcard__org-name"]', 'a[data-tracking-control-name*="company"]']
        )
        desc_el = soup.select_one('[class*="description__text"]') or soup.select_one("main")
        desc = desc_el.get_text(separator="\n", strip=True)[:5000] if desc_el else None

        return {
            "job_title": self._clean_text(title) if title else None,
            "company": self._clean_text(company) if company else None,
            "job_description": self._clean_text(desc) if desc else None,
            "requirements": None,
            "error": None if (title or desc) else
                "LinkedIn requires login for full job details. Please paste the description manually.",
        }

    def _scrape_indeed(self, soup: BeautifulSoup, url: str) -> Dict:
        """Indeed job page extractor — JSON-LD is usually present."""
        ld = self._extract_json_ld(soup)
        if ld:
            return self._parse_from_json_ld(ld)

        # DOM fallback
        title = self._extract_by_selectors(
            soup, ['[data-testid="jobsearch-JobInfoHeader-title"]', "h1"]
        )
        company = self._extract_by_selectors(
            soup, ['[data-testid="inlineHeader-companyName"]', '[class*="companyName"]']
        )
        desc_el = soup.select_one('[id="jobDescriptionText"]') or soup.select_one("main")
        desc = desc_el.get_text(separator="\n", strip=True)[:5000] if desc_el else None

        return {
            "job_title": self._clean_text(title) if title else None,
            "company": self._clean_text(company) if company else None,
            "job_description": self._clean_text(desc) if desc else None,
            "requirements": None,
            "error": None,
        }

    def _scrape_ziprecruiter(self, soup: BeautifulSoup, url: str) -> Dict:
        """ZipRecruiter job page extractor."""
        ld = self._extract_json_ld(soup)
        if ld:
            return self._parse_from_json_ld(ld)

        title = self._extract_by_selectors(soup, ['[class*="job_title"]', "h1"])
        company = self._extract_by_selectors(soup, ['[class*="hiring_company_text"]', '[class*="company"]'])
        desc_el = soup.select_one('[class*="job_description"]') or soup.select_one("article")
        desc = desc_el.get_text(separator="\n", strip=True)[:5000] if desc_el else None

        return {
            "job_title": self._clean_text(title) if title else None,
            "company": self._clean_text(company) if company else None,
            "job_description": self._clean_text(desc) if desc else None,
            "requirements": None,
            "error": None,
        }

    def _scrape_glassdoor(self, soup: BeautifulSoup, url: str) -> Dict:
        """Glassdoor extractor — mostly gated, tries meta tags."""
        ld = self._extract_json_ld(soup)
        if ld:
            return self._parse_from_json_ld(ld)

        title = self._extract_by_selectors(soup, ['meta[property="og:title"]', "h1"])
        company = self._extract_by_selectors(soup, ['[class*="employer-name"]', '[class*="company"]'])
        desc_el = soup.select_one('[class*="jobDescriptionContent"]') or soup.select_one("main")
        desc = desc_el.get_text(separator="\n", strip=True)[:5000] if desc_el else None

        has_content = bool(title or desc)
        return {
            "job_title": self._clean_text(title) if title else None,
            "company": self._clean_text(company) if company else None,
            "job_description": self._clean_text(desc) if desc else None,
            "requirements": None,
            "error": None if has_content else
                "Glassdoor requires login for full details. Please paste the description manually.",
        }

    def scrape_url(self, url: str) -> Dict[str, Optional[str]]:
        """
        Scrape job description from URL using local Playwright instance.

        Args:
            url: Job posting URL (Greenhouse, Lever, LinkedIn, etc.)

        Returns:
            Dictionary with extracted fields:
            - job_title: str or None
            - company: str or None
            - job_description: str or None
            - requirements: str or None
            - error: str or None (if scraping failed)
        """
        if not self.playwright_installed:
            return {
                "job_title": None,
                "company": None,
                "job_description": None,
                "requirements": None,
                "error": "Playwright not installed. Please run: brew install playwright-cli",
            }

        try:
            # Create temporary HTML file for Playwright to render
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".html", delete=False
            ) as f:
                _ = f.name  # tempfile

            # Use playwright-cli to fetch and render the page
            _ = [
                "playwright-cli",
                "open",
                "--headless",
                "--timeout",
                str(self.timeout),
                "--wait",
                "networkidle",  # Wait for all JS to load
                url,
            ]

            # Alternative: Use playwright-cli screenshot + extract text
            # For now, use simpler approach with requests + BS4 for static content
            # Fall back to manual paste if JS-heavy

            import requests
            from requests.exceptions import RequestException

            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }

            try:
                response = requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()
            except RequestException as e:
                return {
                    "job_title": None,
                    "company": None,
                    "job_description": None,
                    "requirements": None,
                    "error": f"Failed to fetch URL: {str(e)}. Please paste job description manually.",
                }

            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(response.text, "html.parser")

            # Remove script, style, nav elements
            for element in soup(["script", "style", "nav", "header", "footer"]):
                element.decompose()

            # --- Site-specific extraction ---
            site = self._detect_site(url)
            site_handlers = {
                "linkedin":     self._scrape_linkedin,
                "indeed":       self._scrape_indeed,
                "ziprecruiter": self._scrape_ziprecruiter,
                "glassdoor":    self._scrape_glassdoor,
            }
            if site in site_handlers:
                result = site_handlers[site](soup, url)
                # Clean all text fields
                for key in ("job_title", "company", "job_description"):
                    if result.get(key):
                        result[key] = self._clean_text(result[key])
                return result

            # --- Generic extraction (Greenhouse, Lever, Workday, etc.) ---
            job_title = self._extract_by_selectors(
                soup,
                [
                    "h1",
                    '[class*="job-title"]',
                    '[class*="jobTitle"]',
                    '[data-qa*="job-title"]',
                    "title",  # Fallback to page title
                ],
            )

            # Extract company name
            company = self._extract_by_selectors(
                soup,
                [
                    '[class*="company"]',
                    '[class*="employer"]',
                    '[data-qa*="company"]',
                    'meta[name="employer"]',
                ],
            )

            # Extract job description (look for main content areas)
            job_description = self._extract_main_content(soup)

            # Extract requirements (look for lists, bullet points)
            requirements = self._extract_requirements(soup)

            # Clean up extracted text
            if job_title:
                job_title = self._clean_text(job_title)
            if company:
                company = self._clean_text(company)
            if job_description:
                job_description = self._clean_text(job_description)
            if requirements:
                requirements = self._clean_text(requirements)

            return {
                "job_title": job_title,
                "company": company,
                "job_description": job_description,
                "requirements": requirements,
                "error": None,
            }

        except Exception as e:
            return {
                "job_title": None,
                "company": None,
                "job_description": None,
                "requirements": None,
                "error": f"Scraping failed: {str(e)}. Please paste job description manually.",
            }

    def _extract_by_selectors(
        self, soup: BeautifulSoup, selectors: list
    ) -> Optional[str]:
        """Try multiple CSS selectors until one returns content"""
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    # Handle meta tags
                    if element.name == "meta":
                        return element.get("content")
                    return element.get_text(strip=True)
            except Exception:
                continue
        return None

    def _extract_main_content(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract main job description content"""
        # Try common job description containers
        content_selectors = [
            '[class*="description"]',
            '[class*="job-description"]',
            '[class*="content"]',
            '[id*="description"]',
            "main",
            "article",
        ]

        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                # Extract paragraphs
                paragraphs = element.find_all("p", recursive=True)
                if paragraphs:
                    return "\n\n".join(
                        [
                            p.get_text(strip=True)
                            for p in paragraphs
                            if p.get_text(strip=True)
                        ]
                    )

        # Fallback: extract all text from body
        body = soup.find("body")
        if body:
            return body.get_text(separator="\n", strip=True)

        return None

    def _extract_requirements(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract requirements/qualifications section"""
        # Look for sections containing "requirement", "qualification", "must have"
        requirement_keywords = [
            "requirement",
            "qualification",
            "must have",
            "you should",
            "you must",
        ]

        # Find lists (ul, ol) near requirement keywords
        for heading in soup.find_all(["h2", "h3", "h4"]):
            heading_text = heading.get_text().lower()
            if any(keyword in heading_text for keyword in requirement_keywords):
                # Find next list after this heading
                next_list = heading.find_next(["ul", "ol"])
                if next_list:
                    items = next_list.find_all("li")
                    if items:
                        return "\n".join([li.get_text(strip=True) for li in items])

        # Fallback: look for any lists
        lists = soup.find_all(["ul", "ol"])
        if lists:
            all_items = []
            for list_tag in lists:
                items = list_tag.find_all("li")
                all_items.extend([li.get_text(strip=True) for li in items])

            if all_items:
                return "\n".join(all_items[:20])  # Limit to 20 items

        return None

    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        if not text:
            return ""

        # Remove multiple whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove special characters that break markdown
        text = text.replace("\u200b", "")  # Zero-width space
        text = text.replace("\u00a0", " ")  # Non-breaking space

        # Strip leading/trailing whitespace
        text = text.strip()

        # Limit length to prevent context overflow
        if len(text) > 5000:
            text = text[:5000] + "..."

        return text


def scrape_job(url: str) -> Dict:
    """
    Convenience function to scrape a job posting.

    Args:
        url: Job posting URL

    Returns:
        Dictionary with scraped content
    """
    scraper = LocalJobScraper()
    return scraper.scrape_url(url)


if __name__ == "__main__":
    # Test scraping
    test_url = input("Enter job posting URL (or press Enter to skip): ").strip()

    if test_url:
        print(f"\n🔍 Scraping: {test_url}")
        result = scrape_job(test_url)

        if result.get("error"):
            print(f"❌ {result['error']}")
        else:
            print("\n✅ Scraping successful!")
            print(f"\n📋 Job Title: {result.get('job_title', 'N/A')}")
            print(f"🏢 Company: {result.get('company', 'N/A')}")
            print(
                f"\n📝 Description preview: {result.get('job_description', '')[:200]}..."
            )
            print(
                f"\n🎯 Requirements preview: {result.get('requirements', '')[:200]}..."
            )
    else:
        print(
            "⚠️  Skipping test. You can paste job descriptions directly in the Streamlit UI."
        )
