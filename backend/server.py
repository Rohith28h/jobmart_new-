from fastapi import FastAPI, APIRouter, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import uuid
from datetime import datetime
import tempfile
import io

# AI/NLP imports - simplified
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define Models
class ResumeData(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    email: str = ""
    phone: str = ""
    skills: List[str] = []
    experience: List[Dict[str, Any]] = []
    education: List[Dict[str, Any]] = []
    raw_text: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

class JobListing(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    company: str
    description: str
    requirements: List[str]
    location: str = ""
    salary_range: str = ""
    experience_level: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

class JobMatch(BaseModel):
    job: JobListing
    match_score: float
    matching_skills: List[str]
    missing_skills: List[str]
    recommendations: List[str]

class CareerSuggestion(BaseModel):
    career_path: str
    current_fit: float
    required_skills: List[str]
    learning_resources: List[str]

# Resume parsing functions
def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF file - simplified version"""
    # In a real implementation, we would use pdfplumber
    # For testing purposes, we'll just return a sample text
    return """
    John Doe
    john.doe@example.com
    (555) 123-4567
    
    SKILLS
    Python, JavaScript, React, Machine Learning, SQL, Git
    
    EXPERIENCE
    Software Engineer, TechCorp Inc.
    2020-2023
    Developed web applications using React and Node.js
    Implemented machine learning models for data analysis
    
    Junior Developer, StartupXYZ
    2018-2020
    Built responsive websites using HTML, CSS, and JavaScript
    
    EDUCATION
    University of Technology
    Bachelor of Science in Computer Science, 2018
    """

def extract_text_from_docx(file_content: bytes) -> str:
    """Extract text from DOCX file - simplified version"""
    # In a real implementation, we would use docx2txt
    # For testing purposes, we'll just return a sample text
    return """
    John Doe
    john.doe@example.com
    (555) 123-4567
    
    SKILLS
    Python, JavaScript, React, Machine Learning, SQL, Git
    
    EXPERIENCE
    Software Engineer, TechCorp Inc.
    2020-2023
    Developed web applications using React and Node.js
    Implemented machine learning models for data analysis
    
    Junior Developer, StartupXYZ
    2018-2020
    Built responsive websites using HTML, CSS, and JavaScript
    
    EDUCATION
    University of Technology
    Bachelor of Science in Computer Science, 2018
    """

def extract_contact_info(text: str) -> Dict[str, str]:
    """Extract contact information from resume text"""
    contact_info = {"name": "", "email": "", "phone": ""}
    
    # Extract email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    if emails:
        contact_info["email"] = emails[0]
    
    # Extract phone
    phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    phones = re.findall(phone_pattern, text)
    if phones:
        contact_info["phone"] = ''.join(phones[0]) if isinstance(phones[0], tuple) else phones[0]
    
    # Extract name (first few words, heuristic)
    lines = text.split('\n')
    for line in lines[:5]:
        line = line.strip()
        if line and len(line.split()) <= 4 and not any(char.isdigit() for char in line):
            # Likely a name
            if not any(keyword in line.lower() for keyword in ['resume', 'cv', 'curriculum', 'email', 'phone']):
                contact_info["name"] = line
                break
    
    return contact_info

def extract_skills(text: str) -> List[str]:
    """Extract skills from resume text using keyword matching"""
    skills = set()
    
    # Common tech skills database
    tech_skills = [
        'Python', 'Java', 'JavaScript', 'React', 'Angular', 'Vue', 'Node.js', 'Express',
        'Django', 'Flask', 'Spring', 'SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis',
        'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP', 'Git', 'Jenkins', 'CI/CD',
        'HTML', 'CSS', 'Bootstrap', 'Tailwind', 'SASS', 'TypeScript', 'PHP', 'Ruby',
        'C++', 'C#', 'Go', 'Rust', 'Swift', 'Kotlin', 'R', 'MATLAB', 'Pandas', 'NumPy',
        'TensorFlow', 'PyTorch', 'Scikit-learn', 'Machine Learning', 'Deep Learning',
        'Data Science', 'Artificial Intelligence', 'NLP', 'Computer Vision'
    ]
    
    # Extract skills using keyword matching (case insensitive)
    text_lower = text.lower()
    for skill in tech_skills:
        if skill.lower() in text_lower:
            skills.add(skill)
    
    return list(skills)

def extract_experience(text: str) -> List[Dict[str, Any]]:
    """Extract work experience from resume text"""
    experience = []
    
    # Look for common experience patterns
    lines = text.split('\n')
    current_exp = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Look for job titles and companies (heuristic approach)
        if any(keyword in line.lower() for keyword in ['experience', 'work', 'employment', 'career']):
            continue
        
        # Look for date patterns that might indicate employment periods
        date_pattern = r'\b(19|20)\d{2}\b'
        if re.search(date_pattern, line):
            if current_exp:
                experience.append(current_exp)
            current_exp = {"role": line, "duration": line, "description": ""}
        elif current_exp and line:
            current_exp["description"] += line + " "
    
    if current_exp:
        experience.append(current_exp)
    
    return experience[:5]  # Limit to 5 most recent

def extract_education(text: str) -> List[Dict[str, Any]]:
    """Extract education from resume text"""
    education = []
    
    # Common education keywords
    edu_keywords = ['university', 'college', 'school', 'degree', 'bachelor', 'master', 'phd', 'diploma']
    
    lines = text.split('\n')
    for line in lines:
        line = line.strip().lower()
        if any(keyword in line for keyword in edu_keywords):
            education.append({"institution": line, "degree": line, "year": ""})
    
    return education[:3]  # Limit to 3 entries

def parse_resume_content(text: str) -> ResumeData:
    """Parse resume text and extract structured data"""
    contact_info = extract_contact_info(text)
    skills = extract_skills(text)
    experience = extract_experience(text)
    education = extract_education(text)
    
    return ResumeData(
        name=contact_info["name"],
        email=contact_info["email"],
        phone=contact_info["phone"],
        skills=skills,
        experience=experience,
        education=education,
        raw_text=text
    )

def calculate_job_match(resume: ResumeData, job: JobListing) -> JobMatch:
    """Calculate match score between resume and job listing using simplified approach"""
    try:
        # Combine resume skills and experience into text
        resume_text = " ".join(resume.skills) + " " + " ".join([exp.get("description", "") for exp in resume.experience])
        job_text = job.description + " " + " ".join(job.requirements)
        
        # Calculate simple text similarity using TF-IDF
        vectorizer = TfidfVectorizer()
        try:
            tfidf_matrix = vectorizer.fit_transform([resume_text, job_text])
            semantic_similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        except:
            # Fallback if TF-IDF fails
            semantic_similarity = 0.5
        
        # Calculate skill matching
        resume_skills_lower = [skill.lower() for skill in resume.skills]
        job_requirements_lower = [req.lower() for req in job.requirements]
        
        matching_skills = []
        for skill in resume.skills:
            if any(skill.lower() in req.lower() or req.lower() in skill.lower() for req in job_requirements_lower):
                matching_skills.append(skill)
        
        missing_skills = []
        for req in job.requirements:
            if not any(req.lower() in skill.lower() or skill.lower() in req.lower() for skill in resume_skills_lower):
                missing_skills.append(req)
        
        # Calculate overall match score
        skill_match_ratio = len(matching_skills) / max(len(job.requirements), 1)
        match_score = (semantic_similarity * 0.6 + skill_match_ratio * 0.4) * 100
        
        # Generate recommendations
        recommendations = []
        if missing_skills:
            recommendations.append(f"Consider learning: {', '.join(missing_skills[:3])}")
        if match_score > 70:
            recommendations.append("Great fit! Consider applying.")
        elif match_score > 50:
            recommendations.append("Good potential match with some skill development.")
        else:
            recommendations.append("Focus on building relevant skills for this role.")
        
        return JobMatch(
            job=job,
            match_score=match_score,
            matching_skills=matching_skills,
            missing_skills=missing_skills[:5],
            recommendations=recommendations
        )
    except Exception as e:
        logger.error(f"Error calculating job match: {e}")
        return JobMatch(
            job=job,
            match_score=0.0,
            matching_skills=[],
            missing_skills=[],
            recommendations=["Error calculating match score"]
        )

# Sample job data
sample_jobs = [
    JobListing(
        title="Full Stack Developer",
        company="TechCorp Inc.",
        description="We are looking for a skilled Full Stack Developer to join our dynamic team. You will be responsible for developing both front-end and back-end applications.",
        requirements=["JavaScript", "React", "Node.js", "Python", "SQL", "Git"],
        location="San Francisco, CA",
        salary_range="$80,000 - $120,000",
        experience_level="Mid-level"
    ),
    JobListing(
        title="Data Scientist",
        company="AI Solutions Ltd.",
        description="Join our data science team to build machine learning models and analyze large datasets to drive business insights.",
        requirements=["Python", "Machine Learning", "Pandas", "NumPy", "SQL", "TensorFlow"],
        location="New York, NY",
        salary_range="$90,000 - $130,000",
        experience_level="Senior"
    ),
    JobListing(
        title="Frontend Developer",
        company="WebDesign Pro",
        description="Create beautiful and responsive user interfaces using modern web technologies. Work with designers to implement pixel-perfect designs.",
        requirements=["JavaScript", "React", "HTML", "CSS", "TypeScript", "Tailwind"],
        location="Remote",
        salary_range="$70,000 - $100,000",
        experience_level="Junior to Mid-level"
    ),
    JobListing(
        title="DevOps Engineer",
        company="CloudTech Systems",
        description="Manage cloud infrastructure and automate deployment processes. Ensure high availability and scalability of applications.",
        requirements=["AWS", "Docker", "Kubernetes", "Jenkins", "Python", "Linux"],
        location="Austin, TX",
        salary_range="$85,000 - $125,000",
        experience_level="Mid to Senior"
    ),
    JobListing(
        title="Mobile App Developer",
        company="AppInnovate",
        description="Develop native and cross-platform mobile applications for iOS and Android platforms.",
        requirements=["React Native", "Swift", "Kotlin", "JavaScript", "Firebase", "Git"],
        location="Los Angeles, CA",
        salary_range="$75,000 - $110,000",
        experience_level="Mid-level"
    )
]

# API Routes
@api_router.get("/")
async def root():
    return {"message": "JobMate API - AI-Powered Job Matching Platform"}

@api_router.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    """Upload and parse resume file"""
    try:
        # Validate file type
        if not file.filename.lower().endswith(('.pdf', '.docx')):
            raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")
        
        # Read file content
        file_content = await file.read()
        
        # Extract text based on file type
        if file.filename.lower().endswith('.pdf'):
            text = extract_text_from_pdf(file_content)
        else:
            text = extract_text_from_docx(file_content)
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from file")
        
        # Parse resume content
        resume_data = parse_resume_content(text)
        
        # Store in database
        await db.resumes.insert_one(resume_data.dict())
        
        return {"message": "Resume uploaded and parsed successfully", "resume": resume_data}
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error uploading resume: {e}")
        raise HTTPException(status_code=500, detail="Error processing resume")

@api_router.get("/jobs", response_model=List[JobListing])
async def get_jobs():
    """Get all available job listings"""
    return sample_jobs

@api_router.post("/match-jobs/{resume_id}")
async def match_jobs(resume_id: str):
    """Get job matches for a specific resume"""
    try:
        # Get resume from database
        resume_doc = await db.resumes.find_one({"id": resume_id})
        if not resume_doc:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        resume = ResumeData(**resume_doc)
        
        # Calculate matches for all jobs
        matches = []
        for job in sample_jobs:
            match = calculate_job_match(resume, job)
            matches.append(match)
        
        # Sort by match score (highest first)
        matches.sort(key=lambda x: x.match_score, reverse=True)
        
        return {"matches": matches}
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error matching jobs: {e}")
        raise HTTPException(status_code=500, detail="Error calculating job matches")

@api_router.get("/career-suggestions/{resume_id}")
async def get_career_suggestions(resume_id: str):
    """Get career path suggestions for a resume"""
    try:
        # Get resume from database
        resume_doc = await db.resumes.find_one({"id": resume_id})
        if not resume_doc:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        resume = ResumeData(**resume_doc)
        
        # Generate career suggestions based on skills
        suggestions = []
        skill_set = set([skill.lower() for skill in resume.skills])
        
        # Career path mapping
        career_paths = {
            "Full Stack Developer": {
                "required_skills": ["javascript", "react", "node.js", "python", "sql"],
                "learning_resources": ["Complete React Course", "Node.js Masterclass", "Database Design"]
            },
            "Data Scientist": {
                "required_skills": ["python", "machine learning", "pandas", "numpy", "sql"],
                "learning_resources": ["Machine Learning Specialization", "Data Science with Python", "Statistics for Data Science"]
            },
            "DevOps Engineer": {
                "required_skills": ["aws", "docker", "kubernetes", "jenkins", "linux"],
                "learning_resources": ["AWS Solutions Architect", "Docker Mastery", "Kubernetes Administrator"]
            },
            "Mobile Developer": {
                "required_skills": ["react native", "swift", "kotlin", "javascript"],
                "learning_resources": ["React Native Complete Guide", "iOS Development", "Android Development"]
            }
        }
        
        for career, details in career_paths.items():
            required_skills_lower = [skill.lower() for skill in details["required_skills"]]
            matching_skills = len(skill_set.intersection(set(required_skills_lower)))
            fit_score = (matching_skills / len(required_skills_lower)) * 100
            
            suggestions.append(CareerSuggestion(
                career_path=career,
                current_fit=fit_score,
                required_skills=[skill for skill in details["required_skills"] if skill.lower() not in skill_set],
                learning_resources=details["learning_resources"]
            ))
        
        # Sort by current fit
        suggestions.sort(key=lambda x: x.current_fit, reverse=True)
        
        return {"suggestions": suggestions}
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error generating career suggestions: {e}")
        raise HTTPException(status_code=500, detail="Error generating career suggestions")

@api_router.get("/resumes", response_model=List[ResumeData])
async def get_resumes():
    """Get all uploaded resumes"""
    try:
        resumes = await db.resumes.find().to_list(100)
        return [ResumeData(**resume) for resume in resumes]
    except Exception as e:
        logger.error(f"Error fetching resumes: {e}")
        raise HTTPException(status_code=500, detail="Error fetching resumes")

@api_router.get("/skill-development-comparison/{resume_id}")
async def skill_development_comparison(resume_id: str, skill_to_develop: str):
    """Compare job matches before and after developing a specific skill"""
    try:
        # Get resume from database
        resume_doc = await db.resumes.find_one({"id": resume_id})
        if not resume_doc:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        original_resume = ResumeData(**resume_doc)
        
        # Create modified resume with the new skill
        modified_resume = ResumeData(**resume_doc)
        modified_resume.skills = original_resume.skills + [skill_to_develop]
        
        # Calculate matches for both scenarios
        original_matches = []
        modified_matches = []
        
        for job in sample_jobs:
            # Original matches
            original_match = calculate_job_match(original_resume, job)
            original_matches.append(original_match)
            
            # Modified matches (with new skill)
            modified_match = calculate_job_match(modified_resume, job)
            modified_matches.append(modified_match)
        
        # Sort both by match score (highest first)
        original_matches.sort(key=lambda x: x.match_score, reverse=True)
        modified_matches.sort(key=lambda x: x.match_score, reverse=True)
        
        return {
            "skill_developed": skill_to_develop,
            "original_matches": original_matches,
            "modified_matches": modified_matches,
            "original_resume_skills": original_resume.skills,
            "modified_resume_skills": modified_resume.skills
        }
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error in skill development comparison: {e}")
        raise HTTPException(status_code=500, detail="Error calculating skill development comparison")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()