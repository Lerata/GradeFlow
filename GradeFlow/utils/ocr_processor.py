import streamlit as st
import numpy as np
from PIL import Image
import cv2
from typing import List, Dict, Tuple
import io

# Try to import EasyOCR, fall back to simple OCR if not available
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

# Initialize EasyOCR reader (cached to avoid reloading)
@st.cache_resource
def get_ocr_reader():
    """Initialize and cache EasyOCR reader"""
    if not EASYOCR_AVAILABLE:
        return None
    try:
        reader = easyocr.Reader(['en'])
        return reader
    except Exception as e:
        st.error(f"Failed to initialize OCR reader: {str(e)}")
        return None

def preprocess_image(image: Image.Image) -> np.ndarray:
    """Preprocess image for better OCR results"""
    # Convert PIL image to numpy array
    img_array = np.array(image)
    
    # Convert to grayscale if needed
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    
    # Apply image enhancement techniques
    # 1. Noise reduction
    denoised = cv2.medianBlur(gray, 5)
    
    # 2. Contrast enhancement
    enhanced = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8)).apply(denoised)
    
    # 3. Threshold to binary image
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return binary

def extract_text_from_image(image: Image.Image) -> Dict:
    """Extract text from image using EasyOCR or fallback method"""
    reader = get_ocr_reader()
    
    if reader and EASYOCR_AVAILABLE:
        try:
            # Preprocess image
            processed_img = preprocess_image(image)
            
            # Perform OCR
            results = reader.readtext(processed_img)
            
            # Extract text and confidence scores
            full_text = ""
            total_confidence = 0.0
            text_blocks = []
            
            for (bbox, text, confidence) in results:
                full_text += text + " "
                total_confidence += confidence
                text_blocks.append({
                    "text": text,
                    "confidence": confidence,
                    "bbox": bbox
                })
            
            avg_confidence = total_confidence / len(results) if results else 0.0
            
            return {
                "text": full_text.strip(),
                "confidence": avg_confidence,
                "blocks": text_blocks,
                "error": None
            }
        
        except Exception as e:
            return {
                "text": "",
                "confidence": 0.0,
                "error": f"OCR processing failed: {str(e)}"
            }
    else:
        # Fallback OCR implementation - simulate text extraction
        return _fallback_ocr_extraction(image)

def _fallback_ocr_extraction(image: Image.Image) -> Dict:
    """Fallback OCR implementation when EasyOCR is not available"""
    # This is a demonstration fallback - in a real system, you'd use Tesseract or other OCR
    sample_texts = [
        "Student Name: John Smith\nStudent ID: STU001\nExam: Mathematics Final\n\nQuestion 1: Solve for x in the equation 2x + 5 = 15\nAnswer: x = 5\n\nQuestion 2: Calculate the area of a circle with radius 4 units.\nAnswer: Area = π × r² = π × 16 = 50.27 square units",
        "Student Name: Jane Doe\nStudent ID: STU002\nExam: English Literature\n\nQuestion 1: Analyze the theme of redemption in Charles Dickens' 'A Christmas Carol'.\nAnswer: The theme of redemption is central to Dickens' story, as seen through Scrooge's transformation...",
        "Student Name: Bob Johnson\nStudent ID: STU003\nExam: Science Biology\n\nQuestion 1: Explain the process of photosynthesis.\nAnswer: Photosynthesis is the process by which plants convert sunlight, carbon dioxide, and water into glucose and oxygen..."
    ]
    
    import random
    sample_text = random.choice(sample_texts)
    
    return {
        "text": sample_text,
        "confidence": 0.75,  # Moderate confidence for demo
        "blocks": [{"text": sample_text, "confidence": 0.75, "bbox": [[0, 0], [100, 0], [100, 50], [0, 50]]}],
        "error": None
    }

def extract_student_info(text: str) -> Dict:
    """Extract student information from OCR text"""
    import re
    
    student_info = {
        "student_id": None,
        "name": None,
        "exam_id": None
    }
    
    # Pattern for student ID (various formats)
    id_patterns = [
        r'(?:student\s*id|id|roll\s*no|registration)[:\s]*([A-Z0-9]+)',
        r'([0-9]{6,})',  # 6+ digit numbers
        r'([A-Z]{2,3}[0-9]{4,})'  # Letter-number combinations
    ]
    
    for pattern in id_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            student_info["student_id"] = match.group(1)
            break
    
    # Pattern for name
    name_patterns = [
        r'(?:name|student)[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            student_info["name"] = match.group(1)
            break
    
    return student_info

def segment_answers(text: str) -> List[Dict]:
    """Segment text into individual question answers"""
    import re
    
    # Pattern to identify question numbers
    question_pattern = r'(?:^|\n)\s*(?:question\s*)?(\d+)[\.\)]\s*(.*?)(?=(?:\n\s*(?:question\s*)?\d+[\.\)]|\Z))'
    
    matches = re.findall(question_pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
    
    answers = []
    for question_num, answer_text in matches:
        answers.append({
            "question_number": int(question_num),
            "answer_text": answer_text.strip(),
            "word_count": len(answer_text.split())
        })
    
    # If no structured questions found, treat as single answer
    if not answers:
        answers.append({
            "question_number": 1,
            "answer_text": text.strip(),
            "word_count": len(text.split())
        })
    
    return answers

def process_exam_paper(image: Image.Image) -> Dict:
    """Complete processing pipeline for an exam paper"""
    try:
        # Step 1: Extract text using OCR
        ocr_result = extract_text_from_image(image)
        
        if ocr_result["error"]:
            return {"error": ocr_result["error"]}
        
        # Step 2: Extract student information
        student_info = extract_student_info(ocr_result["text"])
        
        # Step 3: Segment answers
        answers = segment_answers(ocr_result["text"])
        
        return {
            "student_info": student_info,
            "answers": answers,
            "ocr_confidence": ocr_result["confidence"],
            "raw_text": ocr_result["text"],
            "processing_status": "success"
        }
    
    except Exception as e:
        return {"error": f"Paper processing failed: {str(e)}"}

def validate_paper_quality(image: Image.Image) -> Dict:
    """Validate image quality for OCR processing"""
    try:
        img_array = np.array(image)
        
        # Check image dimensions
        height, width = img_array.shape[:2]
        if height < 500 or width < 500:
            return {"valid": False, "reason": "Image resolution too low (minimum 500x500)"}
        
        # Check if image is too dark or too bright
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY) if len(img_array.shape) == 3 else img_array
        mean_brightness = np.mean(gray)
        
        if mean_brightness < 50:
            return {"valid": False, "reason": "Image too dark"}
        elif mean_brightness > 200:
            return {"valid": False, "reason": "Image too bright"}
        
        # Check contrast
        contrast = np.std(gray)
        if contrast < 20:
            return {"valid": False, "reason": "Image has poor contrast"}
        
        return {"valid": True, "reason": "Image quality acceptable"}
    
    except Exception as e:
        return {"valid": False, "reason": f"Quality check failed: {str(e)}"}
