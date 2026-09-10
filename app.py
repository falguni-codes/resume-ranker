import subprocess
import sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "scikit-learn", "PyPDF2", "pandas", "numpy"])
import streamlit as st
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import PyPDF2
import re

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Resume Ranker Pro ✨",
    page_icon="✨",
    layout="wide"
)

# --- CUSTOM CSS (Lusion Vibe) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');
    
    .stApp {
        background: #0a0a0a;
        font-family: 'Inter', sans-serif;
    }
    
    .css-1r6slb0, .css-1v3fvcr, .st-bb, .st-cb {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 24px !important;
        padding: 2rem !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4) !important;
    }
    
    h1, h2, h3 {
        font-weight: 900 !important;
        letter-spacing: -0.02em !important;
        background: linear-gradient(135deg, #ffffff 0%, #ff2a2a 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #ff2a2a, #cc0000) !important;
        color: white !important;
        border: none !important;
        border-radius: 50px !important;
        padding: 0.75rem 2.5rem !important;
        font-weight: 700 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 0 30px rgba(255, 42, 42, 0.2) !important;
    }
    .stButton>button:hover {
        transform: scale(1.05) !important;
        box-shadow: 0 0 50px rgba(255, 42, 42, 0.4) !important;
    }
    
    .stApp::before {
        content: "";
        position: fixed;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle at 30% 50%, rgba(255,42,42,0.08) 0%, transparent 60%),
                    radial-gradient(circle at 70% 80%, rgba(0,150,255,0.05) 0%, transparent 60%);
        animation: rotateBackground 30s infinite alternate ease-in-out;
        z-index: -1;
    }
    @keyframes rotateBackground {
        0% { transform: rotate(0deg) scale(1); }
        100% { transform: rotate(10deg) scale(1.1); }
    }
</style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def clean_text(text):
    """Text ko clean karna"""
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_text_from_pdf(pdf_file):
    """PDF se text extract karna"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        return f"Error: {str(e)}"

def calculate_similarity(resume_text, job_description):
    """Resume aur JD ke beech similarity score"""
    resume_clean = clean_text(resume_text)
    jd_clean = clean_text(job_description)
    
    vectorizer = TfidfVectorizer(stop_words='english')
    vectors = vectorizer.fit_transform([resume_clean, jd_clean])
    similarity = cosine_similarity(vectors[0:1], vectors[1:2])
    score = round(similarity[0][0] * 100, 2)
    
    return score

def get_matching_keywords(resume_text, job_description):
    """Matching keywords dhoondna"""
    resume_clean = clean_text(resume_text)
    jd_clean = clean_text(job_description)
    
    resume_words = set(resume_clean.split())
    jd_words = set(jd_clean.split())
    matching = resume_words.intersection(jd_words)
    return list(matching)[:10]

def extract_resume_details(text):
    """Resume se Name, Email, Phone, Skills nikaalna"""
    details = {
        "name": "Not found",
        "email": "Not found",
        "phone": "Not found",
        "skills": []
    }
    
    # Email extract karo
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    if emails:
        details["email"] = emails[0]
    
    # Phone number extract karo
    phone_pattern = r'\b[6-9]\d{9}\b'
    phones = re.findall(phone_pattern, text)
    if phones:
        details["phone"] = phones[0]
    
    # Name guess karo
    lines = text.split('\n')
    for line in lines[:5]:
        line = line.strip()
        if line and len(line.split()) <= 4 and line.replace(' ', '').isalpha():
            details["name"] = line.title()
            break
    
    # Skills dhoondho
    common_skills = [
        "python", "java", "javascript", "react", "angular", "node",
        "sql", "mysql", "mongodb", "aws", "docker", "kubernetes",
        "machine learning", "deep learning", "nlp", "data science",
        "django", "flask", "spring boot", "html", "css", "git",
        "tensorflow", "pytorch", "pandas", "numpy", "streamlit"
    ]
    
    text_lower = text.lower()
    for skill in common_skills:
        if skill in text_lower:
            details["skills"].append(skill.title())
    
    return details

# --- UI STARTS HERE ---
# TITLE
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1 style="font-size: 4rem; margin: 0;">✨ Resume Ranker</h1>
        <p style="color: #888; font-size: 1.2rem; margin-top: 0.5rem;">
            AI-powered match score for your resume
        </p>
    </div>
    """, unsafe_allow_html=True)

# --- MAIN CONTENT ---
with st.container():
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.markdown("### 📎 Upload Resume")
        uploaded_file = st.file_uploader("Choose a PDF file", type=['pdf'])
        
        resume_text = ""
        if uploaded_file is not None:
            resume_text = extract_text_from_pdf(uploaded_file)
            if resume_text.startswith("Error"):
                st.error(resume_text)
            else:
                st.success("✅ Resume uploaded successfully!")
                with st.expander("👀 Preview Resume Text"):
                    st.text(resume_text[:500] + "..." if len(resume_text) > 500 else resume_text)
        
        # Sample resume
        st.markdown("---")
        st.caption("Or try with sample resume:")
        sample_resumes = {
            "Web Developer": "I have 5 years of experience in Python, Django, and REST APIs. Worked on web development projects.",
            "Data Scientist": "Expert in Python, Machine Learning, Deep Learning, and NLP. Built multiple AI models.",
            "Backend Developer": "Skilled in Java, Spring Boot, Microservices, and AWS cloud deployment.",
            "Frontend Developer": "Experienced in React, Angular, JavaScript, HTML, CSS and frontend development.",
            "Data Analyst": "Proficient in Python, SQL, Data Analysis, and Visualization using Tableau."
        }
        sample_choice = st.selectbox("Select sample:", ["None"] + list(sample_resumes.keys()))
        if sample_choice != "None":
            resume_text = sample_resumes[sample_choice]
            st.success(f"✅ Sample loaded: {sample_choice}")
    
    with col2:
        st.markdown("### 💼 Job Description")
        job_description = st.text_area(
            "Paste the job description here:",
            height=200,
            placeholder="e.g., We are looking for a Python Developer with experience in Django, REST APIs..."
        )
        
        # Sample JD
        sample_jd = st.selectbox(
            "Or use sample JD:",
            ["None", "Web Developer", "Data Scientist", "Backend Developer", "Frontend Developer"]
        )
        sample_jd_texts = {
            "Web Developer": "Looking for Web Developer with Python, Django, REST API experience.",
            "Data Scientist": "Data Scientist role requiring Python, Machine Learning, Deep Learning skills.",
            "Backend Developer": "Backend Developer with Java, Spring Boot, AWS experience.",
            "Frontend Developer": "Frontend Developer skilled in React, Angular, JavaScript, CSS."
        }
        if sample_jd != "None":
            job_description = sample_jd_texts.get(sample_jd, "")
            st.success(f"✅ Sample JD loaded: {sample_jd}")

# --- ANALYZE BUTTON ---
st.markdown("---")
center_col1, center_col2, center_col3 = st.columns([1, 1, 1])
with center_col2:
    analyze_btn = st.button("🔍 Analyze Match", use_container_width=True)

# --- RESULTS ---
if analyze_btn:
    if not resume_text:
        st.error("❌ Please upload a resume or select a sample!")
    elif not job_description:
        st.error("❌ Please enter a job description!")
    else:
        with st.spinner("Analyzing..."):
            # Calculate score
            score = calculate_similarity(resume_text, job_description)
            keywords = get_matching_keywords(resume_text, job_description)
            
            # Display results
            st.markdown("---")
            st.markdown("## 📊 Results")
            
            # Score card
            col_score1, col_score2, col_score3 = st.columns([1, 2, 1])
            with col_score2:
                if score >= 70:
                    st.success(f"## ✅ Match Score: {score}%")
                    st.write("🎉 Great match! This candidate looks promising.")
                elif score >= 40:
                    st.warning(f"## ⚠️ Match Score: {score}%")
                    st.write("📌 Moderate match. Consider checking skills again.")
                else:
                    st.error(f"## ❌ Match Score: {score}%")
                    st.write("🔴 Low match. Skills don't align well.")
            
            # Matching keywords
            st.markdown("### 🔑 Matching Keywords")
            if keywords:
                cols = st.columns(min(5, len(keywords)))
                for idx, keyword in enumerate(keywords[:10]):
                    with cols[idx % min(5, len(keywords))]:
                        st.code(keyword)
            else:
                st.info("No matching keywords found.")
            
            # --- SMART FEEDBACK ---
            st.markdown("---")
            st.markdown("### 📝 Smart Feedback")
            
            if score >= 70:
                st.success("✅ **Excellent Match!** Your skills are well-aligned. You are ready to apply!")
            elif score >= 40:
                jd_words = set(job_description.lower().split())
                resume_words = set(resume_text.lower().split())
                missing_words = [word for word in jd_words if word not in resume_words and len(word) > 4]
                
                if missing_words:
                    st.info(f"💡 **Tip:** Consider adding these keywords to your resume: `{', '.join(missing_words[:5])}`")
                else:
                    st.info("💡 **Tip:** Try to quantify your achievements (e.g., 'Improved sales by 20%')")
            else:
                st.warning("🔴 **Low Match.** Review the job description and update your resume with relevant skills.")
            
            # --- EXTRACTED DETAILS (Resume Parser) ---
            st.markdown("---")
            st.markdown("### 👤 Resume Details")
            
            details = extract_resume_details(resume_text)
            
            col_d1, col_d2, col_d3 = st.columns(3)
            with col_d1:
                st.metric("👤 Name", details["name"])
            with col_d2:
                st.metric("📧 Email", details["email"])
            with col_d3:
                st.metric("📱 Phone", details["phone"])
            
            if details["skills"]:
                st.markdown("### 🛠️ Detected Skills")
                st.write(", ".join(details["skills"]))

# --- FOOTER ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #444; padding: 2rem 0;">
    <p>Made with ❤️ using Streamlit + AI</p>
    <p style="font-size: 0.8rem;">✨ Next-gen resume matching ✨</p>
</div>
""", unsafe_allow_html=True)