import os
import re
import pytesseract
import fitz
import cv2
import numpy as np
from typing import Optional, Dict, Any
from PIL import Image


# Import configuration values
from config import KASPI_CARD_NUMBER, KASPI_PHONE, RECIPIENT_NAME, ONE_MONTH_PRICE, UNLIMITED_PRICE, TESSERACT_PATH, pdf_path

class OCRHandler:
    # PDF processing class
    def __init__(self):
        self.kaspi_card = KASPI_CARD_NUMBER
        self.kaspi_phone = KASPI_PHONE
        self.recipient = RECIPIENT_NAME
        self.one_month_price = ONE_MONTH_PRICE
        self.unlimited_price = UNLIMITED_PRICE

        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
        

    async def process_file(self, file_content: bytes, file_path: str) -> Optional[Dict[str, Any]]:
        # Process PDF file and extract text using OCR
        try:
            
            doc = fitz.open(stream=file_content, filetype="pdf")

            # Temporary file for saving images
            text = ""
            
            for page in doc:
                # Get page image
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # OCR for image - recognize in three languages
                processed_image = self.preprocess_image(img)
                page_text = pytesseract.image_to_string(processed_image, lang='kaz+rus+eng') 
                text += page_text + "\n"
            
            # Close document
            doc.close()

            if not text.strip():
                return {
                    'is_valid': False,
                    'error': 'No text found in image'
                }

            # Analyze text
            result = self.analyze_check_text(text)
            if not result:
                return {
                    'is_valid': False,
                    'error': 'Error during text analysis'
                }

            return result

        except Exception as e:
            print(f"Error processing PDF file: {e}")
            return None

    def convert_pdf_to_images(self, file_content: bytes) -> list:
        # Convert PDF file into list of images
        
        try:
            # Save PDF
            print("PDF conversion started...")
            
            with open(pdf_path, 'wb') as f:
                f.write(file_content)
            
            # Convert PDF to images
            doc = fitz.open(pdf_path)
            images = []
            for page in doc:
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                images.append(img)
            
            # Close document
            doc.close()
            
            return images
            
        except Exception as e:
            print(f"Error converting PDF: {e}")
            return []
            
        finally:
            # Remove temporary file
            if pdf_path and os.path.exists(pdf_path):
                try:
                    os.remove(pdf_path)
                except Exception as e:
                    print(f"Error deleting temporary file: {e}")

    def preprocess_image(self, image) -> np.ndarray:
        # Preprocess image for better OCR recognition
        # 1. Convert to grayscale
        # 2. Apply Gaussian blur
        # 3. Use adaptive threshold
        # 4. Remove noise
        try:
          
            image_np = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            height, width = image_np.shape[:2]
            image_np = cv2.resize(image_np, (width * 2, height * 2), interpolation=cv2.INTER_CUBIC)
            gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            binary = cv2.adaptiveThreshold(
                blurred,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                11,
                2    
            )
            
            kernel = np.ones((1, 1), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            binary = cv2.medianBlur(binary, 3)
            
            return binary
            
        except Exception as e:
            print(f"Error processing image: {e}")
            return image

    def analyze_check_text(self, text: str) -> Optional[Dict[str, Any]]:
        # Analyze Kaspi receipt text
        # - Find payment amount
        # - Verify card number
        # - Check recipient name
        # - Extract transaction time
        try:
            print("Receipt text:")
            print(text)
            # Search for payment amount (more flexible pattern)
            amount_patterns = [
                r'(?:Sum|Amount)[:\s]*(\d+)[.,\s]*(?:₸|KZT)',
                r'(\d+)[.,\s]*(?:₸|KZT)',
                r'(\d+)\s*(?:T)'
            ]
            
            amount = None
            for pattern in amount_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        amount = int(match.group(1))
                        break
                    except ValueError:
                        continue
            
            # Search for card number (consider different formats)
            card_patterns = [
                r'(\d{4}[\s-]*\d{4}[\s-]*\d{4}[\s-]*\d{4})',
                r'(?:Card)[:\s]*(\d{4}[\s-]*\d{4}[\s-]*\d{4}[\s-]*\d{4})',
                r'(?:Kaspi\s*Gold)[:\s]*(\d{4}[\s-]*\d{4}[\s-]*\d{4}[\s-]*\d{4})'
            ]
            
            card_number = None
            for pattern in card_patterns:
                match = re.search(pattern, text)
                if match:
                    card_number = match.group(1).replace(' ', '').replace('-', '')
                    break
            
            # Search for recipient name (consider different writing variants)
            recipient_patterns = [
                self.recipient.lower(),
                self.recipient.lower().replace(' ', ''),
                transliterate_text(self.recipient.lower())
            ]
            
            recipient_found = any(pattern in text.lower() or 
                                pattern in text.lower().replace(' ', '')
                                for pattern in recipient_patterns)
            
            # Search for transaction time (consider different date formats)
            time_patterns = [
                r'(\d{2}[./-]\d{2}[./-]\d{4}\s+\d{2}:\d{2})',
                r'(\d{2}[./-]\d{2}[./-]\d{2}\s+\d{2}:\d{2})',
                r'(?:Date)[:\s]*(\d{2}[./-]\d{2}[./-]\d{4}\s+\d{2}:\d{2})'
            ]
            
            transaction_time = None
            for pattern in time_patterns:
                match = re.search(pattern, text)
                if match:
                    transaction_time = match.group(1)
                    break
            
            # Validation result
            is_valid = (
                amount in [self.one_month_price, self.unlimited_price] and
                card_number == self.kaspi_card and
                recipient_found and
                transaction_time is not None
            )
            
            return {
                'is_valid': is_valid,
                'amount': amount,
                'card_number': card_number,
                'recipient_found': recipient_found,
                'transaction_time': transaction_time,
                'subscription_type': 'one_month' if amount == self.one_month_price else 'unlimited' if amount == self.unlimited_price else None
            }
            
        except Exception as e:
            print(f"Error analyzing text: {e}")
            return None

    def validate_check(self, check_data: Optional[Dict[str, Any]]) -> tuple[bool, str]:
        # Validate receipt data
        # - Check payment amount matches subscription price
        # - Verify card number matches configured number
        # - Confirm recipient name
        # - Ensure transaction time exists
        if not check_data:
            return False, "Receipt not read"
            
        if 'error' in check_data and check_data['error']:
            return False, check_data['error']
            
        if not check_data['is_valid']:
            errors = []
            print("Validation result:")
            print(f"  - Amount: {check_data['amount']}")
            print(f"  - Card number: {check_data['card_number']}")
            print(f"  - Recipient: {check_data['recipient_found']}")
            print(f"  - Transaction time: {check_data['transaction_time']}")
            print(f"  - Subscription type: {check_data['subscription_type']}")
            if not check_data['recipient_found']:
                errors.append("Incorrect recipient name")
            if check_data['amount'] not in [self.one_month_price, self.unlimited_price]:
                errors.append("Incorrect payment amount")
            if not check_data.get('transaction_time'):
                errors.append("Transaction time not found")
            
            return False, ", ".join(errors)
            
        return True, check_data['subscription_type']
    
def transliterate_text(text: str) -> str:
    # Transliterate text for name variants search
    translit_dict = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        'ә': 'a', 'і': 'i', 'ң': 'n', 'ғ': 'g', 'ү': 'u', 'ұ': 'u', 'қ': 'k',
        'ө': 'o', 'һ': 'h'
    }
    return ''.join(translit_dict.get(char, char) for char in text.lower())

ocr = OCRHandler()