import os
import re
from typing import Tuple
from PIL import Image
import pytesseract
from dotenv import load_dotenv
import cv2
import numpy as np
from pdf2image import convert_from_path

# Tesseract жолын орнату
pytesseract.pytesseract.tesseract_cmd = os.getenv('TESSERACT_PATH', r'C:\Program Files\Tesseract-OCR\tesseract.exe')

class OCRHandler:
    def __init__(self):
        load_dotenv('../config/.env')
        pytesseract.pytesseract.tesseract_cmd = os.getenv('TESSERACT_PATH')
        self.kaspi_card = os.getenv('KASPI_CARD_NUMBER')
        self.kaspi_phone = os.getenv('KASPI_PHONE')
        self.recipient = os.getenv('RECIPIENT_NAME')
        self.one_month_price = float(os.getenv('ONE_MONTH_PRICE'))
        self.unlimited_price = float(os.getenv('UNLIMITED_PRICE'))
    
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """Суретті OCR үшін өңдеу"""
        image = cv2.imread(image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Контрастты жақсарту
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        gray = clahe.apply(gray)
        
        # Шуды азайту
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Бинаризация
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return binary
    
    def extract_text(self, image_path: str) -> str:
        """Суреттен мәтінді алу"""
        try:
            # Суретті өңдеу
            processed_image = self.preprocess_image(image_path)
            
            # OCR жасау
            text = pytesseract.image_to_string(processed_image, lang='rus+kaz')
            print(f"Extracted text: {text}")  # Debugging
            
            return text
        except Exception as e:
            print(f"OCR error: {e}")
            return ""
    
    def validate_receipt(self, image_path: str) -> Tuple[bool, float]:
        """Kaspi чекті тексеру"""
        try:
            # Суретті оқу
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, lang='rus')
            print(f"Алынған мәтін: {text}")  # Debugging
            
            # Негізгі ақпаратты тексеру
            if not all(info in text for info in [self.kaspi_card[-4:], self.recipient]):
                print("Карта нөірі немесе алушы аты табылмады")
                return False, 0
            
            # Сомасын табу
            amount_match = re.search(r'(\d+)\s*₸', text)
            if not amount_match:
                print("Сома табылмады")
                return False, 0
            
            amount = float(amount_match.group(1))
            print(f"Табылған сома: {amount}")
            
            # Сомасын тексеру
            if amount not in [self.one_month_price, self.unlimited_price]:
                print(f"Сома дұрыс емес: {amount}")
                return False, 0
            
            print("Чек тексеруден өтті")
            return True, amount
            
        except Exception as e:
            print(f"OCR қатесі: {e}")
            return False, 0 

    def process_kaspi_check(self, file_path):
        try:
            # Файл түрін анықтау
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.pdf':
                # PDF файлын суретке түрлендіру
                pages = convert_from_path(file_path)
                if not pages:
                    return None
                # Бірінші бетті алу
                image = pages[0]
            else:
                # Суретті тікелей оқу
                image = Image.open(file_path)
            
            # OCR арқылы мәтінді алу
            text = pytesseract.image_to_string(image, lang='kaz+rus')
            
            # Нәтижені талдау
            result = self.analyze_check_text(text)
            return result
            
        except Exception as e:
            print(f"OCR қатесі: {e}")
            return None

    def analyze_check_text(self, text):
        try:
            # Төлем сомасын іздеу
            amount_match = re.search(r'(\d+)\s*₸', text)
            amount = int(amount_match.group(1)) if amount_match else None
            
            # Карта нөмірін іздеу
            card_match = re.search(r'(\d{4}\s*\d{4}\s*\d{4}\s*\d{4})', text)
            card_number = card_match.group(1).replace(' ', '') if card_match else None
            
            # Алушы атын іздеу
            recipient_found = self.recipient.lower() in text.lower()
            
            # Тексеру нәтижесі
            is_valid = (
                amount in [self.one_month_price, self.unlimited_price] and
                card_number == self.kaspi_card and
                recipient_found
            )
            
            return {
                'is_valid': is_valid,
                'amount': amount,
                'card_number': card_number,
                'recipient_found': recipient_found,
                'subscription_type': 'one_month' if amount == self.one_month_price else 'unlimited' if amount == self.unlimited_price else None
            }
            
        except Exception as e:
            print(f"Талдау қатесі: {e}")
            return None

    def validate_check(self, check_data):
        if not check_data:
            return False, "Чек оқылмады"
            
        if not check_data['is_valid']:
            errors = []
            if not check_data['recipient_found']:
                errors.append("Алушы аты дұрыс емес")
            if check_data['card_number'] != self.kaspi_card:
                errors.append("Карта нөмірі дұрыс емес")
            if check_data['amount'] not in [self.one_month_price, self.unlimited_price]:
                errors.append("Төлем сомасы дұрыс емес")
            
            return False, ", ".join(errors)
            
        return True, check_data['subscription_type']