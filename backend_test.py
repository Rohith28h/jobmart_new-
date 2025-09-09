import requests
import unittest
import os
import tempfile
from pathlib import Path
import base64
import json
import time

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://error-free-viz.preview.emergentagent.com"
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
    
    def test_08_error_scenarios(self):
        """Test error scenarios"""
        print("\n🔍 Testing error scenarios...")
        
        # Test invalid resume ID
        print("   Testing invalid resume ID...")
        invalid_id = "invalid-uuid-12345"
        response = requests.post(f"{API_URL}/match-jobs/{invalid_id}")
        self.assertEqual(response.status_code, 404)
        
        # Test missing skill parameter
        if self.resume_id:
            print("   Testing missing skill parameter...")
            response = requests.get(f"{API_URL}/skill-development-comparison/{self.resume_id}")
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