import google.generativeai as genai
import io
import time
import logging
import os
from PIL import Image
from django.conf import settings
from bs4 import BeautifulSoup
from langdetect import detect

# Configure logging
logging.basicConfig(level=logging.ERROR)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

class GeminiService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def try_extract_text(self, image, max_retries=5, delay_between_retries=2):
        prompt = """
            You are an HTML generator. Extract and format the content from this image:
            - Return ONLY raw HTML without any markdown code blocks or backticks
            - Do NOT wrap the output in ```html or ``` tags
            - Do NOT add any explanations before or after the HTML
            
            Rules for extraction:
            1. Ignore page numbers
            2. Ignore running headers/footers
            3. Ignore any text outside the main content
            4. Use these HTML tags for formatting:
                - <h1>, <h2>, <h3> for headings
                - <p> for paragraphs
                - <strong> for bold text
                - <em> for italic text
                - <ul>, <ol>, <li> for lists
                - <blockquote> for quotes
                - <br> for line breaks
            5. Preserve exact text alignment
            6. Keep all special characters and mathematical formulas
            
            Begin output now:
            """
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content([prompt, image])
                extracted_text = response.text
                
                # Validate extracted text
                if not extracted_text or len(extracted_text.strip()) < 50:
                    raise Exception("Invalid or empty text extracted")
                    
                return extracted_text
                
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Attempt {attempt + 1} failed. Retrying in {delay_between_retries} seconds...")
                    time.sleep(delay_between_retries)
                else:
                    print(f"All {max_retries} attempts failed for this image")
                    return None

    def extract_text_from_image(self, image_data):
        """Extract text from a single image"""
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))
            return self.try_extract_text(image)
        except Exception as e:
            print(f"Error extracting text from image: {str(e)}")
            return None
        
    def translate_text(self, text, max_retries=5, delay_between_retries=2):
        """Translate text while preserving HTML structure"""
        prompt = """
            You are an HTML translator. Translate the following content:
            - Return ONLY raw HTML without any markdown code blocks or backticks
            - Do NOT wrap the output in ```html or ``` tags
            - Do NOT add any explanations before or after the HTML
            
            Translation rules:
            1. Analyze the HTML structure and content
            2. Detect language (Persian or English)
            3. if the text is in Persian, translate it to English and text is in English, translate it to Persian
            4. Under no circumstances should you return the original text and return the translated text
            5. Keep track of HTML tag positions
            6. Translate text:
                - Persian to English
                - English to Persian
            7. Use these HTML tags in output:
                - <h1>, <h2>, <h3> for headings
                - <p> for paragraphs
                - <strong> for bold text
                - <em> for italic text
                - <ul>, <ol>, <li> for lists
                - <blockquote> for quotes
                - <br> for line breaks
            8. Match original HTML structure exactly
            
            Begin translating this content:
            {text}
            """
        
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content([prompt.format(text=text)])
                return response.text
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Attempt {attempt + 1} failed. Retrying in {delay_between_retries} seconds...")
                    time.sleep(delay_between_retries)
                else:
                    print(f"All {max_retries} attempts failed for this text")
                    return None 