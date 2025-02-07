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

    def _extract_company_name(self, text: str, url: str, title: str) -> str:
        """Extract company name using multiple strategies"""
        # Try to extract from URL first
        domain = urlparse(url).netloc
        domain_parts = domain.split('.')
        
        # Common job board domains to exclude
        job_boards = {'greenhouse', 'lever', 'workday', 'careers', 'jobs', 'boards', 'io', 'com', 'net', 'org'}
        
        # Get company from domain
        company_from_domain = next((part for part in domain_parts if part.lower() not in job_boards), '')
        
        # Clean up company name
        company_from_domain = company_from_domain.replace('-', ' ').title()
        
        # Look for common patterns in text
        company_patterns = [
            r'About (.*?)\n',
            r'About (.*?)$',
            r'(.*?)(?:is hiring|is looking|is seeking)',
            r'Welcome to (.*?)[.!]',
            r'Join (.*?)(?:team|today|now)',
            r'work(?:ing)? (?:at|with|for) (.*?)(?:\.|,|\n)',
        ]
        
        text_lower = text.lower()
        
        # Check for common prefixes that might appear before company names
        for pattern in company_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                company = matches[0].strip()
                # Clean up common suffixes
                company = re.sub(r'\'s team$', '', company)
                company = re.sub(r'\'s$', '', company)
                return company

        # Try to extract from job title
        if "at " in title:
            company = title.split("at ")[-1].strip()
            return company
        
        # If company was found in domain, use it
        if company_from_domain:
            return company_from_domain
        
        # Use NLP to find organization names
        doc = self.nlp(text[:1000])  # Limit text length for performance
        orgs = [ent.text for ent in doc.ents if ent.label_ == 'ORG']
        
        if orgs:
            # Filter out common false positives
            false_positives = {'LLC', 'Inc', 'Ltd', 'Limited', 'Corporation', 'Corp', 'Company'}
            valid_orgs = [org for org in orgs if org not in false_positives]
            if valid_orgs:
                return valid_orgs[0]
        
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
            company = initial_company if initial_company else self._extract_company_name(text, url, title)
            
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