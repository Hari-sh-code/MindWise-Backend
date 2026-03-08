"""
Resume Extractor Service.
Extracts text content from Google Drive PDF resumes.
"""
import requests
import pdfplumber
import tempfile
import os
import logging
import re

logger = logging.getLogger(__name__)


class ResumeExtractor:
    
    def __init__(self):
        self.timeout = 30
    
    def extract(self, drive_link: str) -> str:

        try:
            download_url = self._get_download_url(drive_link)
            
            temp_file_path = self._download_pdf(download_url)
            
            try:
                resume_text = self._extract_text_from_pdf(temp_file_path)
                
                if not resume_text or len(resume_text.strip()) < 50:
                    raise ValueError("Extracted resume text is too short or empty")
                
                return resume_text
                
            finally:

                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                    logger.info(f"Deleted temporary file: {temp_file_path}")
            
        except Exception as e:
            logger.error(f"Failed to extract resume: {e}")
            raise ValueError(f"Failed to extract resume: {str(e)}")
    
    def _get_download_url(self, drive_link: str) -> str:

        file_id = None
        
        match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', drive_link)
        if match:
            file_id = match.group(1)
        
        if not file_id:
            match = re.search(r'[?&]id=([a-zA-Z0-9_-]+)', drive_link)
            if match:
                file_id = match.group(1)
        
        if not file_id:
            raise ValueError("Invalid Google Drive link. Could not extract file ID.")

        return f"https://drive.google.com/uc?export=download&id={file_id}"
    
    def _download_pdf(self, download_url: str) -> str:

        try:
            response = requests.get(download_url, timeout=self.timeout, stream=True)
            response.raise_for_status()

            content_type = response.headers.get('Content-Type', '')
            if 'pdf' not in content_type.lower():

                if 'text/html' in content_type.lower():

                    content = response.text
                    match = re.search(r'confirm=([0-9A-Za-z_-]+)', content)
                    if match:
                        confirm_token = match.group(1)
                        download_url += f"&confirm={confirm_token}"
                        response = requests.get(download_url, timeout=self.timeout, stream=True)
                        response.raise_for_status()

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_file_path = temp_file.name
            
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    temp_file.write(chunk)
            
            temp_file.close()
            logger.info(f"Downloaded PDF to: {temp_file_path}")
            
            return temp_file_path
            
        except requests.RequestException as e:
            raise ValueError(f"Failed to download resume from Google Drive: {str(e)}")
    
    def _extract_text_from_pdf(self, pdf_path: str) -> str:

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

resume_extractor = ResumeExtractor()