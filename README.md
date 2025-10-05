# JobMate - AI-Powered Resume Analysis Platform

JobMate is an intelligent resume analysis platform that helps job seekers optimize their resumes using AI-powered insights, job matching, and skill development recommendations.

## 🚀 Features

- **Resume Upload & Parsing** - Upload PDF/DOCX resumes and extract skills, experience, and contact information
- **AI-Powered Q&A** - Ask questions about your resume and get intelligent answers with improvement suggestions
- **Job Matching** - Match your skills against job descriptions with detailed compatibility scores
- **Skill Development Analysis** - See how learning new skills affects your job match potential
- **Interactive Visualizations** - Charts showing job matches and skill development progression
- **Career Suggestions** - AI-powered recommendations for career advancement

## 📋 Quick Start

### For Emergent Platform Users
The application is pre-configured and ready to use. All dependencies and AI integration are automatically available.

### For Local Development
See [LOCAL_SETUP.md](./LOCAL_SETUP.md) for detailed local setup instructions.

**Quick Local Setup:**
```bash
# Backend
cd backend
pip install -r requirements-local.txt
# Set up your .env file with MongoDB and AI API keys
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Frontend (new terminal)
cd frontend
yarn install
yarn start
```

## 🔧 Configuration

### Environment Variables

**Backend (.env):**
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=jobmate_db

# AI Configuration (choose one)
GOOGLE_API_KEY=your_google_ai_key    # Recommended for local
OPENAI_API_KEY=your_openai_key       # Alternative for local
EMERGENT_LLM_KEY=auto_provided       # Emergent platform only
```

**Frontend (.env):**
```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

## 🤖 AI Integration

The application supports multiple AI providers:

1. **Emergent Integration** (Platform only) - Automatic, no setup needed
2. **Google Generative AI** (Local) - Free tier available, recommended
3. **OpenAI** (Local) - Paid service, high quality

The app automatically detects and uses the available AI service.

## 📁 Project Structure

```
├── backend/           # FastAPI backend
│   ├── server.py     # Main API server
│   ├── requirements.txt        # Platform requirements
│   └── requirements-local.txt  # Local development requirements
├── frontend/          # React frontend
│   ├── src/          # React components
│   └── package.json  # Dependencies
├── LOCAL_SETUP.md    # Local development guide
└── README.md         # This file
```

## 🔄 API Endpoints

- `GET /api/` - API status
- `POST /api/upload-resume` - Upload and parse resume
- `GET /api/resumes` - List uploaded resumes
- `POST /api/job-matches/{resume_id}` - Get job matches for resume
- `POST /api/resume-qa` - AI-powered resume Q&A
- `GET /api/career-suggestions/{resume_id}` - Get career suggestions
- `GET /api/skill-development-comparison/{resume_id}` - Skill development analysis

## 🛠️ Development

### Testing
The project includes comprehensive testing for both backend and frontend components.

### Local Development
1. Follow [LOCAL_SETUP.md](./LOCAL_SETUP.md)
2. Ensure MongoDB is running
3. Set up AI API keys
4. Start backend and frontend services

### Deployment
- **Emergent Platform**: Automatically handled
- **Local/Cloud**: Configure environment variables and deploy FastAPI + React

## 📄 License

This project is configured for both Emergent platform deployment and local development.

## 🆘 Troubleshooting

### AI Features Not Working Locally
- Install AI library: `pip install google-generativeai` or `pip install openai`
- Set API key in backend/.env file
- Verify API key has quota and permissions

### Database Connection Issues
- Ensure MongoDB is running
- Check MONGO_URL in backend/.env
- For MongoDB Atlas, check network access settings

### Import Errors with emergentintegrations
- This is normal for local development
- The app automatically falls back to standard AI libraries
- Use requirements-local.txt for local development

For more help, see [LOCAL_SETUP.md](./LOCAL_SETUP.md)
