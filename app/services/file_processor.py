import os
import aiofiles
from typing import Tuple
from fastapi import UploadFile, HTTPException
import PyPDF2
import pdfplumber
from PIL import Image
import pytesseract
from bs4 import BeautifulSoup
import requests
from app.core.config import settings


class FileProcessor:
    """Service for processing different file types and extracting text content"""

    @staticmethod
    async def save_upload_file(upload_file: UploadFile) -> str:
        """Save uploaded file to disk and return path"""
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

        file_path = os.path.join(settings.UPLOAD_DIR, upload_file.filename)
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await upload_file.read()
            await out_file.write(content)

        return file_path

    @staticmethod
    async def process_text(content: str) -> str:
        """Process plain text content"""
        return content.strip()

    @staticmethod
    async def process_pdf(file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            text = ""

            # Try pdfplumber first (better for complex layouts)
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

            # Fallback to PyPDF2 if pdfplumber fails
            if not text.strip():
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"

            return text.strip()

        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to process PDF: {str(e)}"
            )

    @staticmethod
    async def process_image(file_path: str) -> str:
        """Extract text from image using OCR"""
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            return text.strip()

        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to process image: {str(e)}"
            )

    @staticmethod
    async def process_url(url: str) -> str:
        """Scrape and extract text from URL"""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Get text
            text = soup.get_text()

            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)

            return text.strip()

        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to fetch URL: {str(e)}"
            )

    @classmethod
    async def process_content(cls, content: str, content_type: str, file_path: str = None) -> str:
        """Route content to appropriate processor based on type"""

        if content_type == "text":
            return await cls.process_text(content)

        elif content_type == "url":
            return await cls.process_url(content)

        elif content_type == "pdf" and file_path:
            return await cls.process_pdf(file_path)

        elif content_type == "image" and file_path:
            return await cls.process_image(file_path)

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported content type: {content_type}"
            )
