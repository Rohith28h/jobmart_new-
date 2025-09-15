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
import asyncio

# AI/NLP imports - simplified
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re
import json

# Emergent LLM integration
from emergentintegrations.llm.chat import LlmChat, UserMessage

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

class ResumeQARequest(BaseModel):
    resume_id: str
    question: str

class ResumeQAResponse(BaseModel):
    answer: str
    suggestions: List[str] = []

class CareerSuggestion(BaseModel):
    career_path: str
    current_fit: float
    required_skills: List[str]
    learning_resources: List[str]

# Resume parsing functions
def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF file using pdfplumber"""
    import pdfplumber
    import io
    
    try:
        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        # Fallback: try basic text extraction
        try:
            text = file_content.decode('utf-8', errors='ignore')
            return text
        except:
            raise Exception("Could not extract text from PDF file")

def extract_text_from_docx(file_content: bytes) -> str:
    """Extract text from DOCX file using docx2txt"""
    import docx2txt
    import io
    
    try:
        text = docx2txt.process(io.BytesIO(file_content))
        return text.strip() if text else ""
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {e}")
        # Fallback: try basic text extraction
        try:
            text = file_content.decode('utf-8', errors='ignore')
            return text
        except:
            raise Exception("Could not extract text from DOCX file")

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
    
    # Extract name (improved heuristic)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Look for name in first few lines
    for i, line in enumerate(lines[:8]):  # Check first 8 lines
        line = line.strip()
        
        # Skip lines that are clearly not names
        if not line:
            continue
        if any(keyword in line.lower() for keyword in [
            'resume', 'cv', 'curriculum', 'email', 'phone', 'address', 
            'experience', 'education', 'skills', 'objective', 'summary',
            'profile', 'contact', 'linkedin', 'github', 'portfolio'
        ]):
            continue
        if '@' in line or any(char.isdigit() for char in line if char not in [' ', '-', '.']):
            continue
        if len(line.split()) > 6:  # Too long to be a name
            continue
            
        # Check if line looks like a name
        words = line.split()
        if 1 <= len(words) <= 4:  # Names are typically 1-4 words
            # Check if words start with capital letters (common for names)
            if all(word[0].isupper() for word in words if word):
                contact_info["name"] = line
                break
    
    return contact_info

def extract_skills(text: str) -> List[str]:
    """Extract skills from resume text using keyword matching"""
    skills = set()
    
    # Comprehensive tech skills database
    tech_skills = [
        # Programming Languages
        'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'C', 'Go', 'Rust', 
        'Swift', 'Kotlin', 'Scala', 'R', 'MATLAB', 'PHP', 'Ruby', 'Perl', 'Shell',
        'PowerShell', 'Bash', 'VB.NET', 'Assembly', 'Objective-C', 'Dart', 'Julia',
        
        # Web Technologies
        'React', 'Angular', 'Vue', 'Vue.js', 'Svelte', 'Next.js', 'Nuxt.js', 'Gatsby',
        'Node.js', 'Express', 'Express.js', 'Koa', 'FastAPI', 'Django', 'Flask', 
        'Spring', 'Spring Boot', 'Laravel', 'CodeIgniter', 'ASP.NET', 'Rails',
        'HTML', 'HTML5', 'CSS', 'CSS3', 'SCSS', 'SASS', 'Less', 'Bootstrap', 
        'Tailwind', 'Tailwind CSS', 'Material-UI', 'Ant Design', 'Semantic UI',
        
        # Databases
        'SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'SQLite', 'Oracle', 
        'SQL Server', 'MariaDB', 'Cassandra', 'DynamoDB', 'Neo4j', 'InfluxDB',
        'CouchDB', 'Firebase', 'Supabase', 'PlanetScale',
        
        # Cloud & DevOps
        'AWS', 'Azure', 'GCP', 'Google Cloud', 'Docker', 'Kubernetes', 'Jenkins',
        'CI/CD', 'GitHub Actions', 'GitLab CI', 'Travis CI', 'CircleCI', 'Terraform',
        'Ansible', 'Chef', 'Puppet', 'Vagrant', 'Nginx', 'Apache', 'Linux', 'Ubuntu',
        
        # Version Control & Tools
        'Git', 'GitHub', 'GitLab', 'Bitbucket', 'SVN', 'Mercurial', 'Jira', 'Confluence',
        'Slack', 'Trello', 'Asana', 'Monday.com', 'Notion', 'Figma', 'Adobe XD',
        'Sketch', 'InVision', 'Zeplin', 'Postman', 'Insomnia', 'Swagger',
        
        # Data Science & AI
        'Machine Learning', 'Deep Learning', 'Artificial Intelligence', 'AI', 'ML',
        'Data Science', 'Data Analysis', 'Statistics', 'Pandas', 'NumPy', 'SciPy',
        'Matplotlib', 'Seaborn', 'Plotly', 'TensorFlow', 'PyTorch', 'Keras',
        'Scikit-learn', 'OpenCV', 'NLTK', 'spaCy', 'Hugging Face', 'LangChain',
        'NLP', 'Computer Vision', 'Neural Networks', 'CNN', 'RNN', 'LSTM', 'GAN',
        'Jupyter', 'Colab', 'Tableau', 'Power BI', 'Looker', 'D3.js',
        
        # Mobile Development
        'iOS', 'Android', 'React Native', 'Flutter', 'Xamarin', 'Cordova', 'PhoneGap',
        'Ionic', 'Xcode', 'Android Studio', 'SwiftUI', 'UIKit', 'Jetpack Compose',
        
        # Game Development
        'Unity', 'Unreal Engine', 'Godot', 'GameMaker', 'Construct', 'Phaser',
        'Three.js', 'WebGL', 'OpenGL', 'DirectX', 'Vulkan',
        
        # Other Technologies
        'Blockchain', 'Ethereum', 'Solidity', 'Web3', 'Smart Contracts', 'DeFi',
        'GraphQL', 'REST', 'SOAP', 'gRPC', 'WebSocket', 'Socket.io', 'RabbitMQ',
        'Kafka', 'Elasticsearch', 'Solr', 'Spark', 'Hadoop', 'Flink', 'Storm',
        'Microservices', 'Serverless', 'Lambda', 'API Gateway', 'Load Balancing',
        
        # Methodologies & Concepts
        'Agile', 'Scrum', 'Kanban', 'DevOps', 'TDD', 'BDD', 'DDD', 'Clean Code',
        'SOLID', 'Design Patterns', 'Microservices', 'Monolith', 'Event-Driven',
        'Test Automation', 'Unit Testing', 'Integration Testing', 'E2E Testing',
        'Performance Testing', 'Security Testing', 'UI/UX', 'Responsive Design',
        'SEO', 'Accessibility', 'PWA', 'SPA', 'SSR', 'JAMstack'
    ]
    
    # Extract skills using keyword matching (case insensitive)
    text_lower = text.lower()
    
    # Also look for skills in specific sections
    sections = ['skills', 'technical skills', 'technologies', 'competencies', 'expertise']
    for section in sections:
        section_pattern = rf'{section}[:\s]+(.*?)(?=\n\s*[A-Z][A-Z\s]*[:\n]|\n\s*\n|$)'
        matches = re.findall(section_pattern, text, re.IGNORECASE | re.DOTALL)
        for match in matches:
            # Skills in dedicated sections are more likely to be accurate
            for skill in tech_skills:
                if skill.lower() in match.lower():
                    skills.add(skill)
    
    # General text search for skills
    for skill in tech_skills:
        # Use word boundaries to avoid partial matches
        pattern = rf'\b{re.escape(skill.lower())}\b'
        if re.search(pattern, text_lower):
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

# AI Resume Q&A Helper Functions
def format_resume_for_ai(resume: ResumeData) -> str:
    """Format resume data for AI context"""
    resume_text = f"""
RESUME CONTENT:

PERSONAL INFORMATION:
- Name: {resume.name or 'Not provided'}
- Email: {resume.email or 'Not provided'}
- Phone: {resume.phone or 'Not provided'}

SKILLS:
{', '.join(resume.skills) if resume.skills else 'No skills listed'}

EXPERIENCE:
"""
    
    if resume.experience:
        for i, exp in enumerate(resume.experience, 1):
            resume_text += f"{i}. {exp.get('title', 'Unknown Position')} at {exp.get('company', 'Unknown Company')}\n"
            if exp.get('duration'):
                resume_text += f"   Duration: {exp['duration']}\n"
            if exp.get('description'):
                resume_text += f"   Description: {exp['description']}\n"
            resume_text += "\n"
    else:
        resume_text += "No experience information provided\n"
    
    return resume_text

async def get_ai_resume_answer(resume_text: str, question: str) -> ResumeQAResponse:
    """Get AI-powered answer about the resume"""
    try:
        # Initialize AI chat with system message
        system_message = """You are a helpful AI assistant that answers questions and provides useful suggestions based on the given resume.

Instructions:
- First, answer the user's question strictly based on the resume content.
- Then, if relevant, provide a short and practical suggestion or improvement. 
  (e.g., skills to add, a better way to present experience, and career growth tips).
- If the answer cannot be found in the resume, say: 
  "This information is not available in the resume." 
  But still try to provide a general suggestion if possible.
- Keep answers clear, concise, and professional.
- Format your response as: ANSWER: [your answer] SUGGESTIONS: [bullet points if any]"""

        # Get API key from environment
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="AI service not configured")

        # Create AI chat instance
        chat = LlmChat(
            api_key=api_key,
            session_id=f"resume_qa_{uuid.uuid4()}",
            system_message=system_message
        ).with_model("gemini", "gemini-2.0-flash")

        # Prepare the message with resume context and question
        user_message = UserMessage(
            text=f"{resume_text}\n\nUser Question: {question}"
        )

        # Get AI response
        response = await chat.send_message(user_message)
        
        # Parse the response to extract answer and suggestions
        response_text = response.strip()
        
        # Try to split answer and suggestions
        answer = ""
        suggestions = []
        
        if "SUGGESTIONS:" in response_text:
            parts = response_text.split("SUGGESTIONS:", 1)
            answer = parts[0].replace("ANSWER:", "").strip()
            suggestions_text = parts[1].strip()
            
            # Extract bullet points or numbered suggestions
            suggestion_lines = [line.strip() for line in suggestions_text.split('\n') if line.strip()]
            suggestions = [line.lstrip('•-*1234567890. ') for line in suggestion_lines if line.strip()]
        else:
            answer = response_text.replace("ANSWER:", "").strip()
        
        return ResumeQAResponse(
            answer=answer,
            suggestions=suggestions[:5]  # Limit to 5 suggestions
        )
        
    except Exception as e:
        logger.error(f"Error getting AI response: {e}")
        # Fallback response
        return ResumeQAResponse(
            answer="I'm sorry, I'm unable to process your question at the moment. Please try again later.",
            suggestions=["Consider updating your resume with more specific details about your experience and skills."]
        )

@api_router.post("/resume-qa", response_model=ResumeQAResponse)
async def ask_resume_question(request: ResumeQARequest):
    """Ask questions about a specific resume using AI"""
    try:
        # Get resume from database
        resume_doc = await db.resumes.find_one({"id": request.resume_id})
        if not resume_doc:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        resume = ResumeData(**resume_doc)
        
        # Format resume for AI context
        resume_text = format_resume_for_ai(resume)
        
        # Get AI response
        response = await get_ai_resume_answer(resume_text, request.question)
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error in resume Q&A: {e}")
        raise HTTPException(status_code=500, detail="Error processing resume question")

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