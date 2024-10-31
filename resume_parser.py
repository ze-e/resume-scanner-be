from dotenv import load_dotenv
import os
from openai import OpenAI
from config_loader import load_job_criteria
from pdfminer.high_level import extract_text
from docx import Document

# Load API key from .env file
load_dotenv()
client = OpenAI()  # This automatically uses OPENAI_API_KEY from environment


def parse_pdf(file_path):
    try:
        text = extract_text(file_path)
        return text
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return None



def parse_docx(file_path):
    try:
        doc = Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        print(f"Error parsing DOCX: {e}")
        return None

import os

def parse_resume(file_path):
    _, file_extension = os.path.splitext(file_path)
    if file_extension.lower() == '.pdf':
        return parse_pdf(file_path)
    elif file_extension.lower() == '.docx':
        return parse_docx(file_path)
    else:
        print("Unsupported file format")
        return None


def score_resume(parsed_text, job_criteria):
    weights = job_criteria['weights']

    # Skills scoring based on keyword matching with synonyms
    skill_matches = 0
    for skill in job_criteria['skills']:
        # Check if any synonym for the skill is in the parsed text
        if any(synonym.lower() in parsed_text.lower() for synonym in skill['synonyms']):
            skill_matches += 1

    skill_score = (skill_matches / len(job_criteria['skills'])) * weights['skills']

    # Experience scoring based on keyword matching
    experience_matches = sum(1 for keyword in job_criteria['experience_keywords'] if keyword.lower() in parsed_text.lower())
    experience_score = (experience_matches / len(job_criteria['experience_keywords'])) * weights['experience']

    # Education scoring based on keyword matching
    education_score = weights['education'] if job_criteria['education'].lower() in parsed_text.lower() else 0

    # Total score without ChatGPT
    score_without_chatgpt = round(skill_score + experience_score + education_score, 2)

    # ChatGPT analysis for contextual scoring
    job_role = job_criteria['role']
    chatgpt_analysis = analyze_with_chatgpt(parsed_text, job_role)
    experience_score_with_chatgpt = skill_score_with_chatgpt = 0
    summary = ""

    if chatgpt_analysis:
        # Parse ChatGPT's response for experience and skill scores and summary
        try:
            lines = chatgpt_analysis.split("\n")
            experience_score_with_chatgpt = float(lines[0].split(":")[1].strip()) * weights['experience']
            skill_score_with_chatgpt = float(lines[1].split(":")[1].strip()) * weights['skills']
            summary = "\n".join(lines[2:])  # The summary starts after the score lines
        except (IndexError, ValueError) as e:
            print(f"Error parsing ChatGPT output: {e}")

    # Total score with ChatGPT
    score_with_chatgpt = round(skill_score_with_chatgpt + experience_score_with_chatgpt + education_score, 2)

    # Print both scores and the summary
    print(f"Score without ChatGPT: {score_without_chatgpt}")
    print(f"Score with ChatGPT: {score_with_chatgpt}")
    print("ChatGPT Summary:", summary)

    return score_with_chatgpt  # Returning the ChatGPT-enhanced score as the main output


def analyze_with_chatgpt(parsed_text, job_role):
    prompt = f"""
    Analyze the following resume text for a {job_role}. 
    Assess if the candidate has relevant experience, skills, and education for this role.
    
    Resume Text: {parsed_text}
    
    Provide your response in this format:
    Experience_Score:0.X
    Skills_Score:0.X

    After providing the scores, include a short paragraph (3-5 sentences) explaining why the candidate may or may not be a good fit for this role.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        output = response.choices[0].message.content.strip()
        return output
    except Exception as e:
        print(f"Error with ChatGPT analysis: {e}")
        return None

def screen_resume(file_path, job_criteria):
    # Step 1: Parse the resume
    parsed_text = parse_resume(file_path)
    if not parsed_text:
        print("Failed to parse the resume.")
        return None

    # Step 2: Score the resume (without ChatGPT and with ChatGPT)
    print(f"Processing resume for role: {job_criteria['role']}")
    score_with_chatgpt = score_resume(parsed_text, job_criteria)
    return score_with_chatgpt


if __name__ == "__main__":
    # Load job criteria
    job_criteria = load_job_criteria()['job_roles'][0]  

    final_score = screen_resume("sample_resume.pdf", job_criteria)
    print(f"Final Resume Score: {final_score}")

