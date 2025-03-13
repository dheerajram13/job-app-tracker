import httpx
import requests
from bs4 import BeautifulSoup
from typing import Dict, List
import logging
import json
import re
import spacy
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class JobParser:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
        
        # Common selectors across job boards
        self.selectors = {
            'title': [
                'h1.job-title',
                'h1.posting-headline',
                'h1.app-title',
                '.job-title',
                '.posting-headline',
                'h1:first-of-type',  # Fallback to first h1
            ],
            'company': [
                '.company-name',
                '.employer',
                '.organization',
                '[data-company]',
                '[itemtype="http://schema.org/Organization"]'
            ],
            'location': [
                '.location',
                '.job-location',
                '[data-location]',
                '.posting-location'
            ],
            'description': [
                '.job-description',
                '.description',
                '.posting-description',
                '#job-description',
                '[data-job-description]'
            ]
        }
        
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading spaCy model: {str(e)}")
            raise

    def _find_element_by_selectors(self, soup: BeautifulSoup, selectors: List[str]) -> str:
        """Find element using multiple possible selectors"""
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    return element.get_text().strip()
            except Exception:
                continue
        return ""

    def _extract_from_structured_data(self, soup: BeautifulSoup) -> str:
        """Extract company name from structured data"""
        try:
            # Try to find JSON-LD data
            script_tags = soup.find_all('script', type='application/ld+json')
            for script in script_tags:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        # Look for hiringOrganization or organization
                        org = data.get('hiringOrganization') or data.get('organization')
                        if org and isinstance(org, dict):
                            name = org.get('name')
                            if name and isinstance(name, str):
                                cleaned_name = self._clean_company_name(name)
                                if self._validate_company_name(cleaned_name):
                                    return cleaned_name
                except:
                    continue
                    
            # Try to find meta tags
            meta_selectors = [
                'meta[property="og:site_name"]',
                'meta[name="author"]',
                'meta[name="publisher"]'
            ]
            
            for selector in meta_selectors:
                meta = soup.select_one(selector)
                if meta and meta.get('content'):
                    cleaned_name = self._clean_company_name(meta['content'])
                    if self._validate_company_name(cleaned_name):
                        return cleaned_name
                        
        except Exception as e:
            logger.error(f"Error extracting structured data: {str(e)}")
        
        return ""

    def _extract_from_url(self, url: str) -> str:
        """Extract company name from URL"""
        try:
            domain = urlparse(url).netloc
            parts = domain.split('.')
            
            # Skip common job board domains
            job_boards = {
                'greenhouse', 'lever', 'workday', 'careers', 'jobs',
                'boards', 'glassdoor', 'indeed', 'linkedin', 'monster',
                'careerbuilder', 'dice', 'ziprecruiter', 'smartrecruiters'
            }
            
            # Try to find the company name part
            for part in parts:
                if part.lower() not in job_boards and len(part) > 2:
                    name = part.replace('-', ' ').title()
                    if self._validate_company_name(name):
                        return name
                        
        except Exception as e:
            logger.error(f"Error extracting from URL: {str(e)}")
        
        return ""

    def _clean_company_name(self, name: str) -> str:
        """Clean up extracted company names"""
        # Remove common suffixes
        suffixes = [
            r'\s*(?:Inc|LLC|Ltd|Limited|Corp|Corporation|Co|Company)',
            r'\'s?\s*(?:team|careers?|jobs?)',
            r'\s*[-–—]\s*(?:Careers|Jobs)',
        ]
        
        cleaned = name.strip()
        for suffix in suffixes:
            cleaned = re.sub(suffix, '', cleaned, flags=re.IGNORECASE)
        
        # Remove special characters and extra whitespace
        cleaned = re.sub(r'[^\w\s&-]', ' ', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned.strip()

    def _validate_company_name(self, name: str) -> bool:
        """Validate extracted company names"""
        if not name:
            return False
            
        # Must be between 2 and 50 chars
        if len(name) < 2 or len(name) > 50:
            return False
        
        # Must start with a letter
        if not name[0].isalpha():
            return False
        
        # Check against common false positives
        false_positives = {
            'career', 'job', 'position', 'role', 'opportunity',
            'hiring', 'apply', 'work', 'employment', 'recruit',
            'about', 'contact', 'mission', 'vision', 'overview'
        }
        
        if name.lower() in false_positives:
            return False
        
        return True

    def _score_company_candidates(self, candidates: List[str], text: str) -> List[str]:
        """Score and rank company name candidates"""
        scored = []
        
        for candidate in candidates:
            score = 0
            
            # Frequency score
            freq = len(re.findall(re.escape(candidate), text, re.IGNORECASE))
            score += freq * 2
            
            # Position score (higher score if appears earlier)
            pos = text.lower().find(candidate.lower())
            if pos != -1:
                score += max(0, 1000 - pos) / 100
                
            # Length score (prefer medium length names)
            length = len(candidate)
            if 10 <= length <= 30:
                score += 2
                
            # Case score (prefer proper case)
            if candidate.istitle():
                score += 3
                
            scored.append((candidate, score))
        
        # Sort by score and return company names only
        return [name for name, score in sorted(scored, key=lambda x: x[1], reverse=True)]

    def _extract_company_name(self, text: str, url: str, title: str, soup: BeautifulSoup) -> str:
        """Extract company name using advanced NLP and pattern matching techniques"""
        try:
            # 1. First try to extract from structured data
            company_from_structured = self._extract_from_structured_data(soup)
            if company_from_structured:
                return company_from_structured

            # 2. Try common text patterns with more robust regex
            company_patterns = [
                # "Company Name is hiring" pattern
                r'(?:^|\s)([A-Z][A-Za-z0-9\s&,.]{2,50}?)(?:\s+is\s+(?:hiring|looking|seeking))',
                
                # "Join Company Name" pattern
                r'[Jj]oin\s+(?:the\s+)?([A-Z][A-Za-z0-9\s&,.]{2,50}?)(?:\s+team|\s+today|\s+now|[!.])',
                
                # "About Company Name" pattern
                r'[Aa]bout\s+([A-Z][A-Za-z0-9\s&,.]{2,50}?)(?:\n|\.|$)',
                
                # "Work at Company Name" pattern
                r'[Ww]ork(?:ing)?\s+(?:at|with|for)\s+([A-Z][A-Za-z0-9\s&,.]{2,50}?)(?:\.|,|\n)',
                
                # "Company Name Careers" pattern
                r'^([A-Z][A-Za-z0-9\s&,.]{2,50}?)\s+[Cc]areers?(?:\s|$)',
            ]

            for pattern in company_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    company = matches[0].strip()
                    # Clean up the extracted company name
                    company = self._clean_company_name(company)
                    if self._validate_company_name(company):
                        return company

            # 3. Use NLP for organization detection
            doc = self.nlp(text[:2000])  # Process first 2000 chars for performance
            org_candidates = []
            
            for ent in doc.ents:
                if ent.label_ == 'ORG':
                    org_name = self._clean_company_name(ent.text)
                    if self._validate_company_name(org_name):
                        org_candidates.append(org_name)

            if org_candidates:
                # Score candidates based on frequency and position
                scored_candidates = self._score_company_candidates(org_candidates, text)
                if scored_candidates:
                    return scored_candidates[0]

            # 4. Try to extract from URL
            company_from_url = self._extract_from_url(url)
            if company_from_url:
                return company_from_url

            # 5. Try to extract from job title
            if "at" in title.lower():
                company = title.split("at")[-1].strip()
                company = self._clean_company_name(company)
                if self._validate_company_name(company):
                    return company

            return "Unknown Company"
        except Exception as e:
            logger.error(f"Error extracting company name: {str(e)}")
            return "Unknown Company"

    async def _extract_text_from_url(self, url: str) -> Dict[str, str]:
        """Extract text content from URL with support for multiple job boards"""
        try:
            domain = urlparse(url).netloc
            logger.info(f"Parsing job from domain: {domain}")
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, timeout=30.0)
                response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract sections using common selectors
            title = self._find_element_by_selectors(soup, self.selectors['title'])
            initial_company = self._find_element_by_selectors(soup, self.selectors['company'])
            location = self._find_element_by_selectors(soup, self.selectors['location'])
            
            # Get main content area
            main_content = None
            content_selectors = [
                'main',
                'article',
                '#content',
                '.content',
                '.job-posting',
                '.job-details'
            ]
            
            for selector in content_selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            if not main_content:
                main_content = soup.body
            
            # Remove unwanted elements
            for element in main_content.select('script, style, nav, header, footer, iframe, noscript'):
                element.decompose()
            
            # Get text content
            text = main_content.get_text(separator='\n', strip=True)
            
            # Extract description and requirements
            sections = self._split_content_sections(text)
            
            # Extract company name using intelligent extraction if not found through selectors
            company = initial_company if initial_company else self._extract_company_name(text, url, title, soup)
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'description': sections['description'],
                'requirements': sections['requirements']
            }
            
        except Exception as e:
            logger.error(f"Error extracting text from URL: {str(e)}")
            raise ValueError(f"Error accessing the URL: {str(e)}")

    def _split_content_sections(self, text: str) -> Dict[str, str]:
        """Split content into sections using common markers"""
        sections = {
            'description': '',
            'requirements': ''
        }
        
        # Common section markers
        requirement_markers = [
            'requirements',
            'qualifications',
            'what you\'ll need',
            'what we\'re looking for',
            'skills'
        ]
        
        text_lower = text.lower()
        req_index = -1
        
        # Find where requirements section starts
        for marker in requirement_markers:
            index = text_lower.find(marker)
            if index != -1:
                if req_index == -1 or index < req_index:
                    req_index = index
        
        if req_index != -1:
            sections['description'] = text[:req_index].strip()
            sections['requirements'] = text[req_index:].strip()
        else:
            sections['description'] = text.strip()
        
        return sections

    def _extract_job_type(self, text: str) -> str:
        """Extract job type using patterns"""
        job_types = {
            'full-time': ['full time', 'full-time', 'permanent'],
            'part-time': ['part time', 'part-time'],
            'contract': ['contract', 'temporary', 'interim'],
            'internship': ['intern', 'internship', 'trainee']
        }
        
        text_lower = text.lower()
        
        for job_type, patterns in job_types.items():
            if any(pattern in text_lower for pattern in patterns):
                return job_type
        
        return "full-time"  # Default
    def _extract_experience_level(self, text: str) -> str:
        """Extract experience level using patterns"""
        text_lower = text.lower()
        
        # Check explicit mentions
        if any(senior in text_lower for senior in ['senior', 'sr.', 'lead', 'principal']):
            return 'senior'
        if any(mid in text_lower for mid in ['mid-level', 'intermediate']):
            return 'mid-level'
        if any(junior in text_lower for junior in ['junior', 'jr.', 'entry', 'graduate']):
            return 'entry-level'
            
        # Check years of experience
        experience_matches = re.findall(r'(\d+)[\+]?\s*(?:years?|yrs?)', text_lower)
        if experience_matches:
            years = max(int(year) for year in experience_matches)
            if years >= 5:
                return 'senior'
            elif years >= 3:
                return 'mid-level'
            else:
                return 'entry-level'
        
        return 'not-specified'

    def _extract_requirements(self, text: str) -> List[str]:
        """Extract requirements from text"""
        requirements = []
        
        # Split by common bullet points and newlines
        items = re.split(r'[•\n\-★·]', text)
        
        for item in items:
            item = item.strip()
            # Filter out short items and headers
            if len(item) > 10 and not any(header in item.lower() for header in ['requirements:', 'qualifications:']):
                if len(requirements) < 5:  # Limit to 5 requirements
                    requirements.append(item)
        
        return requirements

    async def parse_job_posting(self, url: str) -> Dict:
        """Main method to parse job posting"""
        try:
            # Extract text with sections
            sections = await self._extract_text_from_url(url)
            
            # Process sections
            job_type = self._extract_job_type(sections['description'])
            experience_level = self._extract_experience_level(sections['description'])
            requirements = self._extract_requirements(sections['requirements'])
            
            # Build response
            return {
                "title": sections['title'],
                "company": sections['company'],
                "description": sections['description'][:500],
                "requirements": requirements,
                "location": sections['location'],
                "job_type": job_type,
                "experience_level": experience_level,
                "url": url
            }
            
        except Exception as e:
            logger.error(f"Error parsing job posting: {str(e)}")
            raise ValueError(f"Error parsing job posting: {str(e)}")

# Create a singleton instance
job_parser = JobParser()