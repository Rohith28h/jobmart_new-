import React, { useState, useEffect } from 'react';
import axios from 'axios';
import SkillDevelopmentComparison from './SkillDevelopmentComparison';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const JobMate = () => {
  const [currentView, setCurrentView] = useState('home');
  const [resumeData, setResumeData] = useState(null);
  const [jobMatches, setJobMatches] = useState([]);
  const [careerSuggestions, setCareerSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  // Get all available skills for development from job matches
  const getAvailableSkillsForDevelopment = () => {
    const skills = new Set();
    jobMatches.forEach(match => {
      match.missing_skills.forEach(skill => skills.add(skill));
    });
    return Array.from(skills);
  };

  // Upload resume function
  const handleResumeUpload = async (file) => {
    setLoading(true);
    setUploadProgress(0);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await axios.post(`${API}/upload-resume`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(progress);
        }
      });
      
      setResumeData(response.data.resume);
      setCurrentView('results');
      
      // Automatically fetch job matches
      await fetchJobMatches(response.data.resume.id);
      await fetchCareerSuggestions(response.data.resume.id);
      
    } catch (error) {
      console.error('Error uploading resume:', error);
      alert('Error uploading resume. Please try again.');
    } finally {
      setLoading(false);
      setUploadProgress(0);
    }
  };

  // Fetch job matches
  const fetchJobMatches = async (resumeId) => {
    try {
      const response = await axios.post(`${API}/match-jobs/${resumeId}`);
      setJobMatches(response.data.matches);
    } catch (error) {
      console.error('Error fetching job matches:', error);
    }
  };

  // Fetch career suggestions
  const fetchCareerSuggestions = async (resumeId) => {
    try {
      const response = await axios.get(`${API}/career-suggestions/${resumeId}`);
      setCareerSuggestions(response.data.suggestions);
    } catch (error) {
      console.error('Error fetching career suggestions:', error);
    }
  };

  // File drop handler
  const handleFileDrop = (e) => {
    e.preventDefault();
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleResumeUpload(files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">JM</span>
              </div>
              <h1 className="text-2xl font-bold text-gray-900">JobMate</h1>
              <span className="px-3 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded-full">
                AI-Powered
              </span>
            </div>
            <nav className="flex space-x-6">
              <button
                onClick={() => setCurrentView('home')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  currentView === 'home'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Home
              </button>
              {resumeData && (
                <button
                  onClick={() => setCurrentView('results')}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    currentView === 'results'
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Results
                </button>
              )}
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {currentView === 'home' && (
          <div className="text-center">
            {/* Hero Section */}
            <div className="mb-12">
              <h2 className="text-4xl font-bold text-gray-900 mb-4">
                Find Your Perfect Job Match with
                <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent"> AI</span>
              </h2>
              <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-8">
                Upload your resume and let our AI analyze your skills, experience, and preferences to recommend 
                the best job opportunities tailored just for you.
              </p>
            </div>

            {/* Upload Section */}
            <div className="max-w-2xl mx-auto">
              <div
                className="border-2 border-dashed border-gray-300 rounded-xl p-12 hover:border-blue-400 transition-colors bg-white shadow-sm"
                onDrop={handleFileDrop}
                onDragOver={handleDragOver}
              >
                {loading ? (
                  <div className="space-y-4">
                    <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    </div>
                    <p className="text-lg font-medium text-gray-900">Processing your resume...</p>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${uploadProgress}%` }}
                      ></div>
                    </div>
                    <p className="text-sm text-gray-600">{uploadProgress}% complete</p>
                  </div>
                ) : (
                  <>
                    <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                      <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                      </svg>
                    </div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">Upload Your Resume</h3>
                    <p className="text-gray-600 mb-6">
                      Drag and drop your resume here, or click to browse
                    </p>
                    <input
                      type="file"
                      accept=".pdf,.docx"
                      onChange={(e) => e.target.files[0] && handleResumeUpload(e.target.files[0])}
                      className="hidden"
                      id="resume-upload"
                    />
                    <label
                      htmlFor="resume-upload"
                      className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 cursor-pointer transition-all duration-200 shadow-lg hover:shadow-xl"
                    >
                      Choose File
                    </label>
                    <p className="text-sm text-gray-500 mt-4">
                      Supports PDF and DOCX files up to 10MB
                    </p>
                  </>
                )}
              </div>
            </div>

            {/* Features Section */}
            <div className="mt-16 grid md:grid-cols-3 gap-8">
              <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Smart Resume Parsing</h3>
                <p className="text-gray-600">
                  Our AI extracts and analyzes your skills, experience, and education with high accuracy.
                </p>
              </div>

              <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">AI Job Matching</h3>
                <p className="text-gray-600">
                  Advanced algorithms match you with jobs based on semantic similarity and skill alignment.
                </p>
              </div>

              <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Career Guidance</h3>
                <p className="text-gray-600">
                  Get personalized career path recommendations and skill development suggestions.
                </p>
              </div>
            </div>
          </div>
        )}

        {currentView === 'results' && resumeData && (
          <div className="space-y-8">
            {/* Resume Summary */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Resume Analysis</h2>
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <h3 className="font-semibold text-gray-900 mb-2">Contact Information</h3>
                  <div className="space-y-1 text-gray-600">
                    <p><strong>Name:</strong> {resumeData.name || 'Not detected'}</p>
                    <p><strong>Email:</strong> {resumeData.email || 'Not detected'}</p>
                    <p><strong>Phone:</strong> {resumeData.phone || 'Not detected'}</p>
                  </div>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 mb-2">Extracted Skills</h3>
                  <div className="flex flex-wrap gap-2">
                    {resumeData.skills.length > 0 ? (
                      resumeData.skills.map((skill, index) => (
                        <span
                          key={index}
                          className="px-3 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded-full"
                        >
                          {skill}
                        </span>
                      ))
                    ) : (
                      <p className="text-gray-500">No skills detected</p>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Job Matches */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Job Matches</h2>
              {jobMatches.length > 0 ? (
                <div className="space-y-4">
                  {jobMatches.map((match, index) => (
                    <div
                      key={index}
                      className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                    >
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">{match.job.title}</h3>
                          <p className="text-gray-600">{match.job.company}</p>
                          <p className="text-sm text-gray-500">{match.job.location} • {match.job.salary_range}</p>
                        </div>
                        <div className="text-right">
                          <div className={`text-2xl font-bold ${
                            match.match_score >= 70 ? 'text-green-600' :
                            match.match_score >= 50 ? 'text-yellow-600' : 'text-red-600'
                          }`}>
                            {Math.round(match.match_score)}%
                          </div>
                          <p className="text-sm text-gray-500">Match Score</p>
                        </div>
                      </div>
                      
                      <div className="grid md:grid-cols-2 gap-4 mt-4">
                        <div>
                          <h4 className="font-medium text-gray-900 mb-2">Matching Skills</h4>
                          <div className="flex flex-wrap gap-1">
                            {match.matching_skills.map((skill, skillIndex) => (
                              <span
                                key={skillIndex}
                                className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded"
                              >
                                {skill}
                              </span>
                            ))}
                          </div>
                        </div>
                        <div>
                          <h4 className="font-medium text-gray-900 mb-2">Skills to Develop</h4>
                          <div className="flex flex-wrap gap-1">
                            {match.missing_skills.slice(0, 5).map((skill, skillIndex) => (
                              <span
                                key={skillIndex}
                                className="px-2 py-1 bg-orange-100 text-orange-800 text-xs font-medium rounded"
                              >
                                {skill}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                      
                      <div className="mt-4">
                        <h4 className="font-medium text-gray-900 mb-2">Recommendations</h4>
                        <ul className="text-sm text-gray-600 space-y-1">
                          {match.recommendations.map((rec, recIndex) => (
                            <li key={recIndex}>• {rec}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500">Loading job matches...</p>
              )}
            </div>

            {/* Career Suggestions */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Career Path Suggestions</h2>
              {careerSuggestions.length > 0 ? (
                <div className="grid md:grid-cols-2 gap-6">
                  {careerSuggestions.map((suggestion, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex justify-between items-center mb-3">
                        <h3 className="text-lg font-semibold text-gray-900">{suggestion.career_path}</h3>
                        <div className={`text-lg font-bold ${
                          suggestion.current_fit >= 70 ? 'text-green-600' :
                          suggestion.current_fit >= 50 ? 'text-yellow-600' : 'text-red-600'
                        }`}>
                          {Math.round(suggestion.current_fit)}%
                        </div>
                      </div>
                      
                      {suggestion.required_skills.length > 0 && (
                        <div className="mb-3">
                          <h4 className="font-medium text-gray-900 mb-2">Skills to Learn</h4>
                          <div className="flex flex-wrap gap-1">
                            {suggestion.required_skills.map((skill, skillIndex) => (
                              <span
                                key={skillIndex}
                                className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded"
                              >
                                {skill}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      <div>
                        <h4 className="font-medium text-gray-900 mb-2">Learning Resources</h4>
                        <ul className="text-sm text-gray-600 space-y-1">
                          {suggestion.learning_resources.map((resource, resourceIndex) => (
                            <li key={resourceIndex}>• {resource}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500">Loading career suggestions...</p>
              )}
            </div>

            {/* Skill Development Comparison */}
            <SkillDevelopmentComparison 
              resumeId={resumeData.id}
              availableSkills={getAvailableSkillsForDevelopment()}
            />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center">
            <div className="flex items-center justify-center space-x-3 mb-4">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold">JM</span>
              </div>
              <span className="text-xl font-bold text-gray-900">JobMate</span>
            </div>
            <p className="text-gray-600">
              AI-powered job matching platform to find your perfect career opportunity.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default JobMate;