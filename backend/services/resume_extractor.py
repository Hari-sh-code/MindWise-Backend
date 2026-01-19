"""
Resume Extractor Service.
Extracts text content from Google Drive PDF resumes.
"""
import requests
import pdfplumber
import tempfile
import os
from typing import Optional
import logging
import re

logger = logging.getLogger(__name__)


class ResumeExtractor:
    """Extracts text from Google Drive PDF resumes."""
    
    def __init__(self):
        self.timeout = 30
    
    def extract(self, drive_link: str) -> str:
        """
        Extract text from a Google Drive PDF resume.
        
        Args:
            drive_link: Google Drive sharing link
            
        Returns:
            Extracted resume text
            
        Raises:
            ValueError: If extraction fails
        """
        try:
            # Convert to direct download URL
            download_url = self._get_download_url(drive_link)
            
            # Download PDF to temporary file
            temp_file_path = self._download_pdf(download_url)
            
            try:
                # Extract text from PDF
                resume_text = self._extract_text_from_pdf(temp_file_path)
                
                if not resume_text or len(resume_text.strip()) < 50:
                    raise ValueError("Extracted resume text is too short or empty")
                
                return resume_text
                
            finally:
                # Always delete temporary file
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                    logger.info(f"Deleted temporary file: {temp_file_path}")
            
        except Exception as e:
            logger.error(f"Failed to extract resume: {e}")
            raise ValueError(f"Failed to extract resume: {str(e)}")
    
    def _get_download_url(self, drive_link: str) -> str:
        """
        Convert Google Drive sharing link to direct download URL.
        
        Supports formats:
        - https://drive.google.com/file/d/FILE_ID/view
        - https://drive.google.com/open?id=FILE_ID
        """
        # Extract file ID from various Google Drive URL formats
        file_id = None
        
        # Pattern 1: /file/d/FILE_ID/
        match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', drive_link)
        if match:
            file_id = match.group(1)
        
        # Pattern 2: ?id=FILE_ID
        if not file_id:
            match = re.search(r'[?&]id=([a-zA-Z0-9_-]+)', drive_link)
            if match:
                file_id = match.group(1)
        
        if not file_id:
            raise ValueError("Invalid Google Drive link. Could not extract file ID.")
        
        # Create direct download URL
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    
    def _download_pdf(self, download_url: str) -> str:
        """
        Download PDF from URL to a temporary file.
        
        Args:
            download_url: Direct download URL
            
        Returns:
            Path to temporary file
        """
        try:
            response = requests.get(download_url, timeout=self.timeout, stream=True)
            response.raise_for_status()
            
            # Check if it's actually a PDF
            content_type = response.headers.get('Content-Type', '')
            if 'pdf' not in content_type.lower():
                # Google Drive might require confirmation for large files
                # Try to handle the confirmation page
                if 'text/html' in content_type.lower():
                    # Look for download warning confirmation
                    content = response.text
                    match = re.search(r'confirm=([0-9A-Za-z_-]+)', content)
                    if match:
                        confirm_token = match.group(1)
                        download_url += f"&confirm={confirm_token}"
                        response = requests.get(download_url, timeout=self.timeout, stream=True)
                        response.raise_for_status()
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_file_path = temp_file.name
            
            # Write PDF content
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    temp_file.write(chunk)
            
            temp_file.close()
            logger.info(f"Downloaded PDF to: {temp_file_path}")
            
            return temp_file_path
            
        except requests.RequestException as e:
            raise ValueError(f"Failed to download resume from Google Drive: {str(e)}")
    
    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from PDF file using pdfplumber.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text
        """
        try:
            text_parts = []
            
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
            
            full_text = '\n\n'.join(text_parts)
            return full_text.strip()
            
        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")


# Global instance
resume_extractor = ResumeExtractor()
