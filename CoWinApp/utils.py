import base64

import fitz  # PyMuPDF
import pytesseract
import requests
from CoWinApp import EmailException
from django.conf import settings
from django.core.mail import send_mail, get_connection
from groq import Groq


def send_mail_using_smtp(otp, email_data):
    try:
        connection = get_connection(
            backend=settings.EMAIL_BACKEND,
            host=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            username=settings.EMAIL_HOST_USER,
            password=settings.EMAIL_HOST_PASSWORD,
            use_tls=settings.EMAIL_USE_TLS,
        )
        message_with_otp = f"Your OTP is: {otp}. Please use this OTP to reset your password."
        send_mail(
            subject=email_data.get("subject"),
            message="",
            html_message=message_with_otp,
            from_email=email_data.get("from_email"),
            recipient_list=email_data.get("recipient"),
            connection=connection,
            fail_silently=False,
        )
    except Exception as exc:
        raise EmailException(exc)


# ocr_image
def perform_ocr(image_path, tesseract_path):
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
    # Extract text from image
    text = pytesseract.image_to_string(image_path)
    return text


# ocr_resume
def perform_ocr_recognition(resume):
    doc = fitz.open(resume)
    text = ""
    for page in doc:
        text = text + page.get_text()
    return text


def perform_ocr_detection(question, programming_language, user_position, resume_data, temperature, latest_model_value,
                          latest_token):
    coding_Interview_Question = question
    programming_Language = programming_language
    user_role = user_position
    resume_data = resume_data

    client = Groq(
        api_key=''
    )

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are an intelligent agent to give the answers of the user input question. The question can be the programming/code question. Give me response as markdown format."
            },
            {
                "role": "user",
                "content": f"""
                    Please provide a detailed Main idea of the coding interview Question. 
    
                    Ensure that the response alligns with the provided instructions and the user's expertise.
    
                    formated as: Give me the answers in paragraph and bullet point format. also  Start With this heading 'Main IDEA:' also add <br> at the end of each answer.
    
                    Question: {coding_Interview_Question}
    
                    Programming Language: {programming_Language}
    
                    User Information:
                    Role: {user_role} (For the user's interest only; do not include in the answer)
    
                    User CV Data:{resume_data}(For interview purposes only; extract relevant information as per custom instructions)
    
                    User Cover Letter Data:{resume_data}(For interview purposes only; extract relevant information as per custom instructions)
    
                    Provide a concise overview of the coding interview question without including the actual code.Focus on conveying the main idea and key points of the question.
    
                    Additional Details:
                    This prompt is designed to assist the user in gathering specific information tailored to their expertise and requirements. The provided user role and main goal are for context purposes only and should not be included in the response. The user's CV data is provided solely for interview purposes, allowing for the extraction of pertinent details to formulate an informed answer.
    
                """,
            }
        ],
        model=f"{latest_model_value}",
        temperature=temperature,
        max_tokens=latest_token,
        top_p=1,
    )
    response = chat_completion.choices[0].message.content

    # Convert all headings to Markdown format
    lines = response.split('\n')
    markdown_response = ''
    for line in lines:
        if line.startswith(('Main Idea:', 'Key Points:', 'Additional Details:', 'Bullet Points:', 'Steps:')):
            markdown_response += f'# {line.lstrip("#").strip()}\n\n'
        else:
            markdown_response += line + '\n'

    return markdown_response


# IMAGE TO  TEXT EXPLAINITION  code
# OpenAI API Key
api_key = ""


# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def decode_image(image_path):
    # Path to your image
    image_path = image_path
    api_endpoint = "https://api.openai.com/v1/chat/completions"
    # Getting the base64 string
    base64_image = encode_image(image_path)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": "gpt-4-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Explain the image?. Give response in markdown format."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 1000
    }
    # start_time = time.time()
    try:
        response = requests.post(api_endpoint, headers=headers, json=payload)
        data = response.json()
        extracted = data['choices'][0]['message']['content']
        return extracted
    except Exception as e:
        print("An error occurred:", e)
        return str(e)
