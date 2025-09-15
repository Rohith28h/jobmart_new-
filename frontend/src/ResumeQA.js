import React, { useState } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ResumeQA = ({ resumeId }) => {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);

  // Predefined example questions
  const exampleQuestions = [
    "What are my strongest skills?",
    "What skills should I add to get better job matches?",
    "How can I improve my resume?",
    "What career paths are best suited for my profile?",
    "What experience gaps should I address?",
    "How competitive is my profile in the job market?"
  ];

  const handleAskQuestion = async (questionText = question) => {
    if (!questionText.trim()) return;
    
    setLoading(true);
    
    try {
      const response = await axios.post(`${API}/resume-qa`, {
        resume_id: resumeId,
        question: questionText
      });

      const newQA = {
        question: questionText,
        answer: response.data.answer,
        suggestions: response.data.suggestions,
        timestamp: new Date()
      };

      setChatHistory(prev => [...prev, newQA]);
      setAnswer(response.data.answer);
      setSuggestions(response.data.suggestions);
      setQuestion('');
      
    } catch (error) {
      console.error('Error asking question:', error);
      const errorQA = {
        question: questionText,
        answer: "Sorry, I couldn't process your question at the moment. Please try again.",
        suggestions: [],
        timestamp: new Date(),
        isError: true
      };
      setChatHistory(prev => [...prev, errorQA]);
    } finally {
      setLoading(false);
    }
  };

  const handleExampleClick = (exampleQuestion) => {
    setQuestion(exampleQuestion);
    handleAskQuestion(exampleQuestion);
  };

  const clearChat = () => {
    setChatHistory([]);
    setAnswer(null);
    setSuggestions([]);
    setQuestion('');
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">AI Resume Assistant</h2>
          <p className="text-gray-600">Ask questions about your resume and get intelligent suggestions</p>
        </div>
        {chatHistory.length > 0 && (
          <button
            onClick={clearChat}
            className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 border border-gray-300 rounded-lg hover:border-gray-400 transition-colors"
          >
            Clear Chat
          </button>
        )}
      </div>

      {/* Example Questions */}
      {chatHistory.length === 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Try asking:</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {exampleQuestions.map((example, index) => (
              <button
                key={index}
                onClick={() => handleExampleClick(example)}
                disabled={loading}
                className="text-left p-3 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <div className="flex items-start space-x-2">
                  <svg className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="text-sm text-gray-700">{example}</span>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Chat History */}
      {chatHistory.length > 0 && (
        <div className="mb-6 max-h-96 overflow-y-auto space-y-4">
          {chatHistory.map((qa, index) => (
            <div key={index} className="border-l-4 border-blue-200 pl-4">
              {/* Question */}
              <div className="flex items-start space-x-2 mb-2">
                <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg className="w-3 h-3 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">{qa.question}</p>
                  <p className="text-xs text-gray-500">{qa.timestamp.toLocaleTimeString()}</p>
                </div>
              </div>

              {/* Answer */}
              <div className="flex items-start space-x-2 ml-8">
                <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
                  qa.isError ? 'bg-red-100' : 'bg-green-100'
                }`}>
                  <svg className={`w-3 h-3 ${qa.isError ? 'text-red-600' : 'text-green-600'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                </div>
                <div className="flex-1">
                  <p className="text-sm text-gray-700 mb-2">{qa.answer}</p>
                  
                  {/* Suggestions */}
                  {qa.suggestions && qa.suggestions.length > 0 && (
                    <div className="mt-3">
                      <h4 className="text-sm font-medium text-gray-900 mb-2">💡 Suggestions:</h4>
                      <ul className="space-y-1">
                        {qa.suggestions.map((suggestion, suggestionIndex) => (
                          <li key={suggestionIndex} className="text-sm text-gray-600 flex items-start space-x-2">
                            <span className="text-blue-600 font-bold">•</span>
                            <span>{suggestion}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Question Input */}
      <div className="space-y-4">
        <div className="flex space-x-3">
          <div className="flex-1">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && !loading && handleAskQuestion()}
              placeholder="Ask a question about your resume..."
              disabled={loading}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
            />
          </div>
          <button
            onClick={() => handleAskQuestion()}
            disabled={loading || !question.trim()}
            className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium rounded-lg hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-xl"
          >
            {loading ? (
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Thinking...</span>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
                <span>Ask</span>
              </div>
            )}
          </button>
        </div>

        <div className="flex items-center justify-center space-x-2 text-xs text-gray-500">
          <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>Powered by AI • Get personalized insights about your resume</span>
        </div>
      </div>
    </div>
  );
};

export default ResumeQA;