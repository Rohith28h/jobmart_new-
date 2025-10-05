# JobMate - Local Development Setup

This guide will help you run the JobMate resume analysis application on your local system.

## Prerequisites

- Python 3.9+
- Node.js 16+
- MongoDB (local installation or MongoDB Atlas)

## Installation Steps

### 1. Clone and Setup Backend

```bash
cd backend
pip install -r requirements.txt
```

### 2. Setup Frontend

```bash
cd frontend
yarn install
# or
npm install
```

### 3. Configure Environment Variables

Create a `.env` file in the `backend` directory with the following:

```env
# Database Configuration
MONGO_URL=mongodb://localhost:27017
DB_NAME=jobmate_db

# AI Configuration (Choose ONE option)

# Option 1: Google Generative AI (Recommended for local development)
GOOGLE_API_KEY=your_google_ai_api_key_here

# Option 2: OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Option 3: Alternative Google AI key name
GEMINI_API_KEY=your_gemini_api_key_here
```

Create a `.env` file in the `frontend` directory with:

```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

### 4. Get API Keys

#### Option 1: Google AI (Recommended)
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your backend `.env` file as `GOOGLE_API_KEY`

#### Option 2: OpenAI
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create a new API key
3. Add it to your backend `.env` file as `OPENAI_API_KEY`

### 5. Setup MongoDB

#### Option A: Local MongoDB
```bash
# Install MongoDB on your system
# Ubuntu/Debian:
sudo apt-get install mongodb

# macOS:
brew install mongodb-community

# Start MongoDB service
sudo systemctl start mongodb  # Linux
brew services start mongodb/brew/mongodb-community  # macOS
```

#### Option B: MongoDB Atlas (Cloud)
1. Create account at [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Create a free cluster
3. Get connection string
4. Update `MONGO_URL` in backend `.env` file

### 6. Install AI Dependencies

The application will automatically detect which AI library is available:

```bash
# For Google AI (recommended - free tier available)
pip install google-generativeai

# OR for OpenAI (requires paid account)
pip install openai
```

### 7. Run the Application

Start backend:
```bash
cd backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

Start frontend (in a new terminal):
```bash
cd frontend
yarn start
# or
npm start
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001

## Features Available Locally

✅ **Resume Upload & Parsing** - Extract skills, experience, and contact info  
✅ **Job Matching** - Match resumes against job descriptions  
✅ **AI-Powered Q&A** - Ask questions about resume content  
✅ **Career Suggestions** - Get AI-powered career recommendations  
✅ **Skill Development Analysis** - Compare job matches before/after learning new skills  
✅ **Interactive Charts** - Visualize job matching and skill development  

## Troubleshooting

### AI Not Working
- Ensure you have either `GOOGLE_API_KEY` or `OPENAI_API_KEY` set in backend/.env
- Verify the API key is valid and has quota remaining
- Check backend logs for specific error messages

### Database Connection Issues
- Ensure MongoDB is running
- Check the `MONGO_URL` in your backend/.env file
- For Atlas, ensure IP whitelist includes your IP address

### Frontend Not Loading
- Verify `REACT_APP_BACKEND_URL` points to http://localhost:8001
- Ensure backend is running on port 8001
- Check browser console for errors

### Missing Dependencies
- Run `pip install -r requirements.txt` in backend directory
- Run `yarn install` or `npm install` in frontend directory
- For AI features, install either `google-generativeai` or `openai`

## API Keys Cost Information

- **Google AI (Gemini)**: Free tier with generous limits
- **OpenAI**: Paid service, starts at $5 minimum

## Development Notes

The application automatically detects available AI libraries in this order:
1. `emergentintegrations` (Emergent platform only)
2. `google-generativeai` (Local development - recommended)
3. `openai` (Local development - alternative)

If no AI library is detected, the app will still work but AI features will show helpful setup messages.