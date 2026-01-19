"""
Job Description Extractor Service.
Extracts job description text from job posting URLs.
"""
import requests
from bs4 import BeautifulSoup
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class JobExtractor:
    """Extracts job descriptions from job posting URLs."""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.timeout = 10
    
    def extract(self, job_url: str) -> Tuple[str, str, str]:
        """
        Extract job description, title, and company from job URL.
        
        Args:
            job_url: URL of the job posting
            
        Returns:
            Tuple of (job_description, job_title, company_name)
            
        Raises:
            ValueError: If extraction fails
        """
        try:
            # Fetch the page
            response = requests.get(job_url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            # Extract job title
            job_title = self._extract_job_title(soup)
            
            # Extract company name
            company_name = self._extract_company_name(soup)
            
            # Extract job description
            job_description = self._extract_job_description(soup)
            
            if not job_description:
                raise ValueError("Could not extract job description from the page")
            
            return job_description, job_title, company_name
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch job URL: {e}")
            raise ValueError(f"Failed to fetch job posting: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to extract job description: {e}")
            raise ValueError(f"Failed to extract job description: {str(e)}")
    
    def _extract_job_title(self, soup: BeautifulSoup) -> str:
        """Extract job title from page."""
        # Try common selectors
        selectors = [
            'h1',
            '[class*="job-title"]',
            '[class*="jobTitle"]',
            '[data-testid="job-title"]',
            'title'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                return element.get_text(strip=True)
        
        # Fallback to first h1
        h1 = soup.find('h1')
        if h1:
            return h1.get_text(strip=True)
        
        return "Job Title Not Found"
    
    def _extract_company_name(self, soup: BeautifulSoup) -> str:
        """Extract company name from page."""
        # Try common selectors
        selectors = [
            '[class*="company-name"]',
            '[class*="companyName"]',
            '[class*="employer"]',
            '[data-testid="company-name"]',
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                return element.get_text(strip=True)
        
        return "Company Not Found"
    
    def _extract_job_description(self, soup: BeautifulSoup) -> str:
        """Extract job description text from page."""
        # Try to find job description in common containers
        description_selectors = [
            '[class*="job-description"]',
            '[class*="jobDescription"]',
            '[class*="job_description"]',
            '[id*="job-description"]',
            '[id*="jobDescription"]',
            '[class*="description"]',
            '[class*="job-details"]',
            '[class*="jobDetails"]',
            '[class*="job-content"]',
            '[class*="content"]',
            'article',
            'main',
            '[role="main"]',
            '.job-desc',
            '#job-desc',
            '.description',
            '#description'
        ]
        
        for selector in description_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(separator='\n', strip=True)
                if len(text) > 100:  # Minimum length check
                    return self._clean_text(text)
        
        # Try finding multiple div/section tags with substantial content
        all_divs = soup.find_all(['div', 'section'])
        for div in all_divs:
            text = div.get_text(separator='\n', strip=True)
            # Look for substantial text blocks (likely job descriptions)
            if len(text) > 500 and len(text) < 20000:
                return self._clean_text(text)
        
        # Fallback: extract all visible text from body
        body = soup.find('body')
        if body:
            text = body.get_text(separator='\n', strip=True)
            if len(text) > 100:
                return self._clean_text(text)
        
        return ""
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text."""
        # Remove multiple newlines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        # Remove duplicate consecutive lines
        cleaned_lines = []
        prev_line = None
        for line in lines:
            if line != prev_line:
                cleaned_lines.append(line)
                prev_line = line
        
        return '\n'.join(cleaned_lines)


# Global instance
job_extractor = JobExtractor()
