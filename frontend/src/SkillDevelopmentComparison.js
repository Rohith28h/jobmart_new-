import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const SkillDevelopmentComparison = ({ resumeId, availableSkills }) => {
  const [selectedSkill, setSelectedSkill] = useState('');
  const [comparisonData, setComparisonData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSkillSelection = async (skill) => {
    setSelectedSkill(skill);
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(`${API}/skill-development-comparison/${resumeId}`, null, {
        params: { skill_to_develop: skill }
      });
      setComparisonData(response.data);
    } catch (err) {
      console.error('Error fetching comparison data:', err);
      setError('Failed to fetch comparison data');
    } finally {
      setLoading(false);
    }
  };

  const generateChartData = (matches, title, color) => {
    const jobTitles = matches.map(match => match.job.title);
    const matchScores = matches.map(match => Math.round(match.match_score));

    return {
      labels: jobTitles,
      datasets: [
        {
          label: `${title} - Match Score (%)`,
          data: matchScores,
          backgroundColor: color,
          borderColor: color.replace('0.6', '1'),
          borderWidth: 1,
        },
      ],
    };
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Job Match Scores',
      },
      tooltip: {
        callbacks: {
          afterLabel: function(context) {
            const match = context.dataset.label.includes('Before') 
              ? comparisonData?.original_matches[context.dataIndex]
              : comparisonData?.modified_matches[context.dataIndex];
            
            if (match) {
              return [
                `Company: ${match.job.company}`,
                `Location: ${match.job.location}`,
                `Matching Skills: ${match.matching_skills.length}`,
                `Skills to Develop: ${match.missing_skills.length}`
              ];
            }
            return [];
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
        title: {
          display: true,
          text: 'Match Score (%)'
        }
      },
      x: {
        title: {
          display: true,
          text: 'Job Positions'
        }
      }
    },
  };

  if (!availableSkills || availableSkills.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Skill Development Impact</h2>
        <p className="text-gray-500">No skills available for development comparison.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Skill Development Impact Analysis</h2>
      
      {/* Skill Selection */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Select a Skill to Develop:</h3>
        <div className="flex flex-wrap gap-2">
          {availableSkills.map((skill, index) => (
            <button
              key={index}
              onClick={() => handleSkillSelection(skill)}
              className={`px-4 py-2 rounded-lg border transition-all duration-200 ${
                selectedSkill === skill
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
            >
              {skill}
            </button>
          ))}
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600">Analyzing skill development impact...</span>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {/* Comparison Charts */}
      {comparisonData && !loading && (
        <div className="space-y-8">
          {/* Before and After Summary */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 mb-2">
              Impact of Learning: <span className="text-blue-600">{comparisonData.skill_developed}</span>
            </h3>
            <div className="grid md:grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-medium text-gray-700">Original Skills:</span>
                <span className="ml-2 text-gray-600">{comparisonData.original_resume_skills.length} skills</span>
              </div>
              <div>
                <span className="font-medium text-gray-700">After Learning:</span>
                <span className="ml-2 text-gray-600">{comparisonData.modified_resume_skills.length} skills</span>
              </div>
            </div>
          </div>

          {/* Before Chart */}
          <div className="space-y-4">
            <h3 className="text-xl font-semibold text-gray-900">Before Learning {comparisonData.skill_developed}</h3>
            <div className="h-96">
              <Bar
                data={generateChartData(comparisonData.original_matches, 'Before', 'rgba(239, 68, 68, 0.6)')}
                options={{
                  ...chartOptions,
                  plugins: {
                    ...chartOptions.plugins,
                    title: {
                      display: true,
                      text: `Job Match Scores - Before Learning ${comparisonData.skill_developed}`,
                    },
                  },
                }}
              />
            </div>
          </div>

          {/* After Chart */}
          <div className="space-y-4">
            <h3 className="text-xl font-semibold text-gray-900">After Learning {comparisonData.skill_developed}</h3>
            <div className="h-96">
              <Bar
                data={generateChartData(comparisonData.modified_matches, 'After', 'rgba(34, 197, 94, 0.6)')}
                options={{
                  ...chartOptions,
                  plugins: {
                    ...chartOptions.plugins,
                    title: {
                      display: true,
                      text: `Job Match Scores - After Learning ${comparisonData.skill_developed}`,
                    },
                  },
                }}
              />
            </div>
          </div>

          {/* Improvement Summary */}
          <div className="bg-blue-50 rounded-lg p-4">
            <h4 className="font-semibold text-blue-900 mb-3">Impact Summary</h4>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <h5 className="font-medium text-blue-800 mb-2">Top Improvements:</h5>
                <div className="space-y-2">
                  {comparisonData.original_matches.map((originalMatch, index) => {
                    const modifiedMatch = comparisonData.modified_matches.find(
                      m => m.job.title === originalMatch.job.title
                    );
                    const improvement = modifiedMatch ? modifiedMatch.match_score - originalMatch.match_score : 0;
                    return improvement > 0 ? (
                      <div key={index} className="flex justify-between text-sm">
                        <span className="text-gray-700">{originalMatch.job.title}</span>
                        <span className="text-green-600 font-medium">+{improvement.toFixed(1)}%</span>
                      </div>
                    ) : null;
                  }).filter(Boolean).slice(0, 3)}
                </div>
              </div>
              <div>
                <h5 className="font-medium text-blue-800 mb-2">Average Improvement:</h5>
                <div className="text-2xl font-bold text-green-600">
                  +{(
                    comparisonData.modified_matches.reduce((sum, match, index) => 
                      sum + (match.match_score - comparisonData.original_matches[index].match_score), 0
                    ) / comparisonData.modified_matches.length
                  ).toFixed(1)}%
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SkillDevelopmentComparison;