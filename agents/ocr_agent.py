import os
import io
import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from dotenv import load_dotenv

load_dotenv()

import base64
import requests
import google.generativeai as genai
from openai import OpenAI

XAI_API_KEY = os.getenv("XAI_API_KEY")
client = OpenAI(api_key=XAI_API_KEY, base_url="https://api.x.ai/v1")

GEMINI_API_KEY = os.getenv("GOOGLE_GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Stable xAI vision models
VISION_MODELS = [
    "grok-2-vision-1212",
]


def preprocess_image(image_bytes):
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )
    denoised = cv2.fastNlMeansDenoising(thresh, h=10)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    return enhanced


def tesseract_ocr(image_bytes):
    try:
        processed = preprocess_image(image_bytes)
        pil_image = Image.fromarray(processed)
        config = "--oem 3 --psm 6"
        data = pytesseract.image_to_data(
            pil_image, config=config,
            output_type=pytesseract.Output.DICT
        )
        confidences = [
            int(c) for c in data['conf']
            if str(c).isdigit() and int(c) > 0
        ]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        raw_text = pytesseract.image_to_string(pil_image, config=config)
        return raw_text.strip(), avg_confidence
    except Exception as e:
        print(f"Tesseract error: {e}")
        return "", 0.0


def xai_vision_ocr(image_bytes):
    """Try each xAI vision model in order until one succeeds, then fallback to Gemini."""
    pil_img = Image.open(io.BytesIO(image_bytes))
    rgb_img = pil_img.convert("RGB")
    buf = io.BytesIO()
    rgb_img.save(buf, format="JPEG")
    b64_image = base64.b64encode(buf.getvalue()).decode("utf-8")

    for model in VISION_MODELS:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}
                            },
                            {
                                "type": "text",
                                "text": "You are a senior clinical pharmacist specializing in reading messy handwritten medical prescriptions. Extract ALL text from this image exactly as written. If handwriting is unclear, use medical context to infer the most likely medicine name, dosage, or frequency. CRITICAL RULES: 1. Do NOT hallucinate or guess medicines that are not on the paper. 2. Capture every single visible letter, number, and symbol related to the prescription, including dates, doctor names, patient details, and clinic notes. 3. Preserve the structural separation. Return ONLY the raw extracted text. No formatting, no conversational filler, no explanation."
                            }
                        ]
                    }
                ],
                max_tokens=2000
            )
            text = response.choices[0].message.content.strip()
            if text:
                print(f"xAI Grok vision OCR success with model: {model}")
                return text, 0.95
        except Exception as e:
            print(f"xAI Grok vision error with {model}: {e}")
            # Continue to the next Grok model 

    print("xAI Grok models failed. Falling back to Gemini Vision OCR...")
    try:
        gemini_model = genai.GenerativeModel("gemini-flash-latest")
        response = gemini_model.generate_content([
            {
                "mime_type": "image/jpeg",
                "data": b64_image
            },
            "You are a senior clinical pharmacist specializing in reading messy handwritten medical prescriptions. Extract ALL text from this image exactly as written. If handwriting is unclear, use medical context to infer the most likely medicine name, dosage, or frequency. CRITICAL RULES: 1. Do NOT hallucinate or guess medicines that are not on the paper. 2. Capture every single visible letter, number, and symbol related to the prescription. 3. Preserve the structural separation. Return ONLY the raw extracted text. No formatting, no conversational filler, no explanation."
        ])
        return response.text.strip(), 0.90
    except Exception as gemini_e:
        print(f"Gemini fallback error: {gemini_e}")
        return "", 0.0


def extract_from_pdf(file_bytes):
    try:
        from pdf2image import convert_from_bytes
        images = convert_from_bytes(file_bytes)
        all_text = ""
        for image in images:
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()
            text, conf = tesseract_ocr(img_bytes)
            if conf < 70:
                text, conf = xai_vision_ocr(img_bytes)
            all_text += text + "\n"
        return all_text.strip(), 90.0, "pdf"
    except Exception as e:
        print(f"PDF error: {e}")
        return "", 0.0, "failed"


def extract_text(file_bytes, file_type):
    try:
        if "pdf" in file_type.lower():
            return extract_from_pdf(file_bytes)

        # 1. Tesseract OCR (Base pass)
        raw_text, confidence = tesseract_ocr(file_bytes)
        method = "tesseract"

        # 2. If low confidence use xAI Vision
        if confidence < 0.60 or len(raw_text) < 20:
            print(f"Tesseract confidence {confidence:.2f} is low. Triggering xAI Vision...")
            raw_text, confidence = xai_vision_ocr(file_bytes)
            method = "xai_vision"
        else:
            method = "tesseract"

        return raw_text, confidence, method

    except Exception as e:
        print(f"extract_text error: {e}")
        try:
            raw_text, confidence = xai_vision_ocr(file_bytes)
            return raw_text, confidence, "xai_vision_fallback"
        except:
            return "", 0.0, "failed"