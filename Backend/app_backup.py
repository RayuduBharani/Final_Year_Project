from flask import Flask, jsonify, request
from flask_cors import CORS
from pdf2image import convert_from_bytes
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image
import torch
import numpy as np
import cv2

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Load the LARGE model for better accuracy (use "microsoft/trocr-large-handwritten" for best results)
print("Loading TrOCR model... This may take a moment.")
processor = TrOCRProcessor.from_pretrained("microsoft/trocr-large-handwritten")
model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-large-handwritten")
print("Model loaded successfully!")

def detect_text_lines(img):
    """
    Detect actual text lines in the image using contour detection.
    Returns bounding boxes for each line of text.
    """
    # Convert PIL to OpenCV format
    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    
    # Apply threshold to get binary image
    _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
    
    # Dilate horizontally to connect text on the same line
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 1))
    dilated = cv2.dilate(binary, kernel, iterations=3)
    
    # Find contours (text lines)
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Get bounding boxes and sort by y-coordinate (top to bottom)
    boxes = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        # Filter out very small boxes (noise) and very large ones
        if h > 10 and w > 50 and h < img.size[1] * 0.5:
            # Add some padding
            padding = 5
            x = max(0, x - padding)
            y = max(0, y - padding)
            w = min(img.size[0] - x, w + 2 * padding)
            h = min(img.size[1] - y, h + 2 * padding)
            boxes.append((x, y, w, h))
    
    # Sort by y-coordinate (top to bottom)
    boxes.sort(key=lambda b: b[1])
    
    return boxes

def extract_text_from_image(img):
    """
    Extract text from an image by detecting and processing individual text lines.
    """
    # Convert to RGB if necessary
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Detect text line regions
    text_boxes = detect_text_lines(img)
    
    # If no lines detected, try processing the whole image in strips
    if not text_boxes:
        return extract_text_strips(img)
    
    extracted_lines = []
    
    for (x, y, w, h) in text_boxes:
        # Crop the text line region
        line_img = img.crop((x, y, x + w, y + h))
        
        # Process the line
        try:
            pixel_values = processor(images=line_img, return_tensors="pt").pixel_values
            generated_ids = model.generate(pixel_values, max_length=150)
            text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            
            # Only add meaningful text (filter out noise)
            if text.strip() and len(text.strip()) > 1 and not is_garbage_text(text):
                extracted_lines.append(text.strip())
        except Exception as e:
            print(f"Error processing line: {e}")
            continue
    
    return "\n".join(extracted_lines)

def extract_text_strips(img):
    """
    Fallback: Extract text by processing horizontal strips.
    """
    width, height = img.size
    line_height = 60
    extracted_lines = []
    
    y = 0
    while y < height:
        bottom = min(y + line_height, height)
        strip = img.crop((0, y, width, bottom))
        
        # Check if strip has content
        strip_array = np.array(strip.convert('L'))
        if np.mean(strip_array) < 250:  # Not mostly white
            try:
                pixel_values = processor(images=strip, return_tensors="pt").pixel_values
                generated_ids = model.generate(pixel_values, max_length=150)
                text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
                
                if text.strip() and len(text.strip()) > 1 and not is_garbage_text(text):
                    extracted_lines.append(text.strip())
            except:
                pass
        
        y += line_height - 10
    
    return "\n".join(extracted_lines)

def is_garbage_text(text):
    """
    Filter out garbage/hallucinated text.
    """
    # Check for repetitive patterns
    if len(text) > 20:
        # Check if any 4+ character sequence repeats more than 3 times
        for i in range(len(text) - 4):
            pattern = text[i:i+4]
            if text.count(pattern) > 3:
                return True
    
    # Check for too many numbers/special chars ratio
    num_count = sum(c.isdigit() for c in text)
    if len(text) > 10 and num_count / len(text) > 0.6:
        return True
    
    # Check for too many zeros
    if text.count('0') > 10:
        return True
        
    return False

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Flask server running!"})

@app.route("/extract-text", methods=["POST"])
def extract_text():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files["file"]

    # Convert PDF to images with high DPI
    images = convert_from_bytes(file.read(), dpi=300)

    extracted_texts = []

    for i, img in enumerate(images):
        print(f"Processing page {i + 1}...")
        text = extract_text_from_image(img)
        extracted_texts.append(text)
        print(f"Page {i + 1} done.")

    return jsonify({"text": extracted_texts})


if __name__ == "__main__":
    app.run(debug=True)
