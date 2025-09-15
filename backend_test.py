import requests
import unittest
import os
import tempfile
from pathlib import Path
import base64
import json
import time

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://resume-upload-fix-1.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class JobMateAPITester(unittest.TestCase):
    """Test suite for JobMate API endpoints"""
    
    def setUp(self):
        """Setup for tests"""
        self.resume_id = None  # Will be set after upload
        
        # Create a sample resume for testing
        self.sample_resume_content = """
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
        
        # Create a temporary PDF file with the sample resume content
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            self.temp_pdf_path = temp_file.name
            temp_file.write(self.sample_resume_content.encode('utf-8'))
    
    def tearDown(self):
        """Cleanup after tests"""
        # Remove temporary file
        if hasattr(self, 'temp_pdf_path') and os.path.exists(self.temp_pdf_path):
            os.unlink(self.temp_pdf_path)
    
    def test_01_api_root(self):
        """Test the API root endpoint"""
        print("\n🔍 Testing API root endpoint...")
        response = requests.get(f"{API_URL}/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        print("✅ API root endpoint test passed")
    
    def test_02_get_jobs(self):
        """Test the get jobs endpoint"""
        print("\n🔍 Testing get jobs endpoint...")
        response = requests.get(f"{API_URL}/jobs")
        self.assertEqual(response.status_code, 200)
        jobs = response.json()
        self.assertIsInstance(jobs, list)
        self.assertTrue(len(jobs) > 0)
        
        # Verify job structure
        job = jobs[0]
        required_fields = ['id', 'title', 'company', 'description', 'requirements']
        for field in required_fields:
            self.assertIn(field, job)
        
        print(f"✅ Get jobs endpoint test passed - Found {len(jobs)} jobs")
    
    def test_03_upload_resume(self):
        """Test resume upload endpoint"""
        print("\n🔍 Testing resume upload endpoint...")
        
        # Open the temporary PDF file
        with open(self.temp_pdf_path, 'rb') as pdf_file:
            files = {'file': ('resume.pdf', pdf_file, 'application/pdf')}
            response = requests.post(f"{API_URL}/upload-resume", files=files)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("resume", data)
        
        # Store resume ID for subsequent tests
        JobMateAPITester.resume_id = data["resume"]["id"]
        self.resume_id = data["resume"]["id"]
        
        # Verify extracted skills
        skills = data["resume"]["skills"]
        self.assertIsInstance(skills, list)
        print(f"✅ Resume upload test passed - Extracted skills: {', '.join(skills)}")
        
        # Verify some expected skills were extracted
        expected_skills = ["Python", "JavaScript", "React", "Machine Learning", "SQL", "Git"]
        found_skills = [skill for skill in expected_skills if skill in skills]
        print(f"   Found {len(found_skills)}/{len(expected_skills)} expected skills")
        
        # Verify contact info extraction
        self.assertIn("name", data["resume"])
        self.assertIn("email", data["resume"])
        self.assertIn("phone", data["resume"])
        
        if data["resume"]["email"]:
            self.assertEqual(data["resume"]["email"], "john.doe@example.com")
            print("✅ Email extraction successful")
        else:
            print("⚠️ Email extraction failed")
            
        if data["resume"]["phone"]:
            self.assertEqual(data["resume"]["phone"], "(555) 123-4567")
            print("✅ Phone extraction successful")
        else:
            print("⚠️ Phone extraction failed")
    
    def test_04_match_jobs(self):
        """Test job matching endpoint"""
        if not hasattr(JobMateAPITester, 'resume_id') or not JobMateAPITester.resume_id:
            self.skipTest("Resume ID not available, skipping job matching test")
        
        resume_id = JobMateAPITester.resume_id
        print(f"\n🔍 Testing job matching endpoint with resume ID: {resume_id}...")
        response = requests.post(f"{API_URL}/match-jobs/{resume_id}")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("matches", data)
        matches = data["matches"]
        self.assertIsInstance(matches, list)
        
        if matches:
            # Verify match structure
            match = matches[0]
            required_fields = ['job', 'match_score', 'matching_skills', 'missing_skills', 'recommendations']
            for field in required_fields:
                self.assertIn(field, match)
            
            # Print match scores
            print("✅ Job matching test passed")
            print("   Job Match Results:")
            for match in matches:
                print(f"   - {match['job']['title']}: {match['match_score']:.2f}% match")
                print(f"     Matching skills: {', '.join(match['matching_skills'])}")
        else:
            print("⚠️ No job matches returned")
    
    def test_05_career_suggestions(self):
        """Test career suggestions endpoint"""
        if not hasattr(JobMateAPITester, 'resume_id') or not JobMateAPITester.resume_id:
            self.skipTest("Resume ID not available, skipping career suggestions test")
        
        resume_id = JobMateAPITester.resume_id
        print(f"\n🔍 Testing career suggestions endpoint with resume ID: {resume_id}...")
        response = requests.get(f"{API_URL}/career-suggestions/{resume_id}")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("suggestions", data)
        suggestions = data["suggestions"]
        self.assertIsInstance(suggestions, list)
        
        if suggestions:
            # Verify suggestion structure
            suggestion = suggestions[0]
            required_fields = ['career_path', 'current_fit', 'required_skills', 'learning_resources']
            for field in required_fields:
                self.assertIn(field, suggestion)
            
            # Print career suggestions
            print("✅ Career suggestions test passed")
            print("   Career Suggestions:")
            for suggestion in suggestions:
                print(f"   - {suggestion['career_path']}: {suggestion['current_fit']:.2f}% fit")
                if suggestion['required_skills']:
                    print(f"     Skills to learn: {', '.join(suggestion['required_skills'])}")
        else:
            print("⚠️ No career suggestions returned")
    
    def test_06_get_resumes(self):
        """Test get resumes endpoint"""
        print("\n🔍 Testing get resumes endpoint...")
        response = requests.get(f"{API_URL}/resumes")
        
        self.assertEqual(response.status_code, 200)
        resumes = response.json()
        self.assertIsInstance(resumes, list)
        
        print(f"✅ Get resumes endpoint test passed - Found {len(resumes)} resumes")
        
        # Verify our uploaded resume is in the list
        if hasattr(JobMateAPITester, 'resume_id') and JobMateAPITester.resume_id:
            resume_ids = [resume["id"] for resume in resumes]
            self.assertIn(JobMateAPITester.resume_id, resume_ids)
            print(f"✅ Verified our uploaded resume (ID: {JobMateAPITester.resume_id}) is in the database")

    def test_07_skill_development_comparison(self):
        """Test skill development comparison endpoint"""
        if not hasattr(JobMateAPITester, 'resume_id') or not JobMateAPITester.resume_id:
            self.skipTest("Resume ID not available, skipping skill development comparison test")
        
        resume_id = JobMateAPITester.resume_id
        print(f"\n🔍 Testing skill development comparison endpoint with resume ID: {resume_id}...")
        
        # Test with different skills
        test_skills = ["Docker", "React", "Python"]
        
        for skill in test_skills:
            print(f"   Testing with skill: {skill}")
            response = requests.get(f"{API_URL}/skill-development-comparison/{resume_id}?skill_to_develop={skill}")
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Verify response structure
            required_fields = ['skill_developed', 'original_matches', 'modified_matches', 
                              'original_resume_skills', 'modified_resume_skills']
            for field in required_fields:
                self.assertIn(field, data)
            
            # Verify the skill was added
            self.assertEqual(data['skill_developed'], skill)
            self.assertIn(skill, data['modified_resume_skills'])
            
            # Verify matches structure
            self.assertIsInstance(data['original_matches'], list)
            self.assertIsInstance(data['modified_matches'], list)
            
            # Verify there are matches
            self.assertTrue(len(data['original_matches']) > 0)
            self.assertTrue(len(data['modified_matches']) > 0)
            
            # Compare match scores (at least one job should have a different score)
            score_differences = []
            for i in range(len(data['original_matches'])):
                original_score = data['original_matches'][i]['match_score']
                modified_score = data['modified_matches'][i]['match_score']
                difference = modified_score - original_score
                score_differences.append(difference)
                
                print(f"     Job: {data['original_matches'][i]['job']['title']}")
                print(f"     Original score: {original_score:.2f}%, Modified score: {modified_score:.2f}%, Difference: {difference:.2f}%")
            
            # At least one job should have a different score
            self.assertTrue(any(diff != 0 for diff in score_differences))
            print(f"   ✅ Skill development comparison test passed for skill: {skill}")
    
    def test_08_resume_qa_functionality(self):
        """Test AI Resume Q&A endpoint functionality"""
        if not hasattr(JobMateAPITester, 'resume_id') or not JobMateAPITester.resume_id:
            self.skipTest("Resume ID not available, skipping AI Q&A test")
        
        resume_id = JobMateAPITester.resume_id
        print(f"\n🔍 Testing AI Resume Q&A endpoint with resume ID: {resume_id}...")
        
        # Test various types of questions
        test_questions = [
            "What are the main skills listed in this resume?",
            "What is the candidate's work experience?",
            "What programming languages does this person know?",
            "How can this resume be improved?",
            "What career paths would be suitable for this candidate?",
            "What is the candidate's educational background?",
            "What are the strengths of this candidate?",
            "What skills should this candidate develop next?"
        ]
        
        successful_responses = 0
        
        for i, question in enumerate(test_questions, 1):
            print(f"   Question {i}: {question}")
            
            # Prepare request payload
            payload = {
                "resume_id": resume_id,
                "question": question
            }
            
            try:
                response = requests.post(f"{API_URL}/resume-qa", json=payload)
                
                # Check response status
                self.assertEqual(response.status_code, 200, f"Failed for question: {question}")
                
                # Parse response
                data = response.json()
                
                # Verify response structure
                self.assertIn("answer", data)
                self.assertIn("suggestions", data)
                
                # Verify answer is not empty
                self.assertTrue(len(data["answer"].strip()) > 0, "Answer should not be empty")
                
                # Verify suggestions is a list
                self.assertIsInstance(data["suggestions"], list)
                
                # Print response for verification
                print(f"     Answer: {data['answer'][:100]}{'...' if len(data['answer']) > 100 else ''}")
                if data["suggestions"]:
                    print(f"     Suggestions: {len(data['suggestions'])} provided")
                    for j, suggestion in enumerate(data["suggestions"][:2], 1):  # Show first 2 suggestions
                        print(f"       {j}. {suggestion}")
                
                successful_responses += 1
                
                # Add small delay to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"     ❌ Error with question '{question}': {str(e)}")
                # Don't fail the test immediately, continue with other questions
        
        # Verify at least some questions were answered successfully
        self.assertGreater(successful_responses, 0, "At least one question should be answered successfully")
        print(f"✅ AI Resume Q&A test passed - {successful_responses}/{len(test_questions)} questions answered successfully")

    def test_09_resume_qa_error_handling(self):
        """Test AI Resume Q&A error handling"""
        print("\n🔍 Testing AI Resume Q&A error handling...")
        
        # Test with invalid resume ID
        print("   Testing with invalid resume ID...")
        invalid_payload = {
            "resume_id": "invalid-uuid-12345",
            "question": "What skills does this person have?"
        }
        
        response = requests.post(f"{API_URL}/resume-qa", json=invalid_payload)
        self.assertEqual(response.status_code, 404)
        print("     ✅ Invalid resume ID correctly returns 404")
        
        # Test with missing question
        if hasattr(JobMateAPITester, 'resume_id') and JobMateAPITester.resume_id:
            print("   Testing with missing question...")
            missing_question_payload = {
                "resume_id": JobMateAPITester.resume_id
                # Missing question field
            }
            
            response = requests.post(f"{API_URL}/resume-qa", json=missing_question_payload)
            self.assertNotEqual(response.status_code, 200)
            print("     ✅ Missing question correctly returns error")
            
            # Test with empty question
            print("   Testing with empty question...")
            empty_question_payload = {
                "resume_id": JobMateAPITester.resume_id,
                "question": ""
            }
            
            response = requests.post(f"{API_URL}/resume-qa", json=empty_question_payload)
            # Should still work but might return a generic response
            if response.status_code == 200:
                data = response.json()
                self.assertIn("answer", data)
                print("     ✅ Empty question handled gracefully")
            else:
                print("     ✅ Empty question correctly returns error")
        
        # Test with malformed JSON
        print("   Testing with malformed request...")
        response = requests.post(f"{API_URL}/resume-qa", data="invalid json")
        self.assertNotEqual(response.status_code, 200)
        print("     ✅ Malformed request correctly returns error")
        
        print("✅ AI Resume Q&A error handling test passed")

    def test_10_ai_integration_verification(self):
        """Test AI integration with Gemini model"""
        if not hasattr(JobMateAPITester, 'resume_id') or not JobMateAPITester.resume_id:
            self.skipTest("Resume ID not available, skipping AI integration test")
        
        resume_id = JobMateAPITester.resume_id
        print(f"\n🔍 Testing AI integration with Gemini model...")
        
        # Test a specific question that should demonstrate AI understanding
        test_payload = {
            "resume_id": resume_id,
            "question": "Based on this resume, what specific improvements would you recommend for career advancement?"
        }
        
        response = requests.post(f"{API_URL}/resume-qa", json=test_payload)
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify the response shows AI understanding
            answer = data["answer"].lower()
            suggestions = data.get("suggestions", [])
            
            # Check for AI-like responses (contextual understanding)
            ai_indicators = [
                "recommend", "suggest", "improve", "develop", "enhance", 
                "consider", "focus", "strengthen", "skill", "experience"
            ]
            
            has_ai_indicators = any(indicator in answer for indicator in ai_indicators)
            self.assertTrue(has_ai_indicators, "Response should show AI understanding and recommendations")
            
            # Verify suggestions are provided
            self.assertTrue(len(suggestions) > 0, "AI should provide suggestions")
            
            print("✅ AI integration verification passed")
            print(f"   Answer contains AI-like recommendations: {has_ai_indicators}")
            print(f"   Number of suggestions provided: {len(suggestions)}")
            
            # Print sample of AI response
            print(f"   Sample AI response: {answer[:150]}{'...' if len(answer) > 150 else ''}")
            
        else:
            print(f"❌ AI integration test failed with status code: {response.status_code}")
            if response.text:
                print(f"   Error response: {response.text}")
            self.fail("AI integration test failed")

    def test_11_error_scenarios(self):
        """Test error scenarios"""
        print("\n🔍 Testing error scenarios...")
        
        # Test invalid resume ID
        print("   Testing invalid resume ID...")
        invalid_id = "invalid-uuid-12345"
        response = requests.post(f"{API_URL}/match-jobs/{invalid_id}")
        self.assertEqual(response.status_code, 404)
        
        # Test missing skill parameter
        if hasattr(JobMateAPITester, 'resume_id') and JobMateAPITester.resume_id:
            print("   Testing missing skill parameter...")
            response = requests.get(f"{API_URL}/skill-development-comparison/{JobMateAPITester.resume_id}")
            self.assertNotEqual(response.status_code, 200)
        
        # Test invalid file type for upload
        print("   Testing invalid file type...")
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_txt_path = temp_file.name
            temp_file.write(b"This is a text file, not a resume")
        
        try:
            with open(temp_txt_path, 'rb') as txt_file:
                files = {'file': ('resume.txt', txt_file, 'text/plain')}
                response = requests.post(f"{API_URL}/upload-resume", files=files)
            
            self.assertEqual(response.status_code, 400)
        finally:
            if os.path.exists(temp_txt_path):
                os.unlink(temp_txt_path)
        
        print("✅ Error scenarios test passed")

if __name__ == "__main__":
    # Run the tests
    print("🚀 Starting JobMate API Tests")
    print(f"🌐 Testing against API URL: {API_URL}")
    
    # Create a test suite that preserves test order
    test_suite = unittest.TestSuite()
    test_suite.addTest(JobMateAPITester('test_01_api_root'))
    test_suite.addTest(JobMateAPITester('test_02_get_jobs'))
    test_suite.addTest(JobMateAPITester('test_03_upload_resume'))
    test_suite.addTest(JobMateAPITester('test_04_match_jobs'))
    test_suite.addTest(JobMateAPITester('test_05_career_suggestions'))
    test_suite.addTest(JobMateAPITester('test_06_get_resumes'))
    test_suite.addTest(JobMateAPITester('test_07_skill_development_comparison'))
    test_suite.addTest(JobMateAPITester('test_08_error_scenarios'))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n📊 Test Summary:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    print(f"   Skipped: {len(result.skipped)}")
    
    # Exit with appropriate code
    if result.wasSuccessful():
        print("✅ All tests passed!")
        exit(0)
    else:
        print("❌ Some tests failed!")
        exit(1)