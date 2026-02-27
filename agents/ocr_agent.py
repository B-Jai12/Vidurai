import pytesseract
from PIL import Image
import cv2
import numpy as np
import io
import os
import base64
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
client = Groq(api_key=GROQ_API_KEY)


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


def groq_vision_ocr(image_bytes):
    try:
        # Convert to RGB JPEG for compatibility
        pil_img = Image.open(io.BytesIO(image_bytes))
        rgb_img = pil_img.convert("RGB")
        buf = io.BytesIO()
        rgb_img.save(buf, format="JPEG")
        b64_image = base64.b64encode(buf.getvalue()).decode("utf-8")
        mime = "image/jpeg"

        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime};base64,{b64_image}"}
                        },
                        {
                            "type": "text",
                            "text": "You are a medical document reader. Extract ALL text from this prescription image exactly as written. Include medicine names, dosages, frequencies, doctor name, hospital name, date, and patient details. Return only the raw extracted text with no formatting or explanation."
                        }
                    ]
                }
            ],
            max_tokens=2000
        )
        return response.choices[0].message.content.strip(), 95.0

    except Exception as e:
        print(f"Groq Vision error: {e}")
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
                text, conf = groq_vision_ocr(img_bytes)
            all_text += text + "\n"
        return all_text.strip(), 90.0, "pdf"
    except Exception as e:
        print(f"PDF error: {e}")
        return "", 0.0, "failed"


def extract_text(file_bytes, file_type):
    try:
        if "pdf" in file_type.lower():
            return extract_from_pdf(file_bytes)

        # Try Tesseract first
        raw_text, confidence = tesseract_ocr(file_bytes)

        # If low confidence use Groq Vision
        if confidence < 70 or len(raw_text.strip()) < 20:
            raw_text, confidence = groq_vision_ocr(file_bytes)
            method = "groq_vision"
        else:
            method = "tesseract"

        return raw_text, confidence, method

    except Exception as e:
        print(f"extract_text error: {e}")
        try:
            raw_text, confidence = groq_vision_ocr(file_bytes)
            return raw_text, confidence, "groq_vision_fallback"
        except:
            return "", 0.0, "failed"