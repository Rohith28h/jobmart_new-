#!/usr/bin/env python3
"""
Specific test for resume upload functionality after dependency fix
"""
import requests
import tempfile
import os

# Backend URL
BACKEND_URL = "https://resume-genius-65.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

def create_test_resume():
    """Create a text-based resume for testing (simulating PDF content)"""
    resume_content = """
Sarah Johnson
sarah.johnson@email.com
(555) 987-6543

TECHNICAL SKILLS
Python, JavaScript, React, Node.js, MongoDB, AWS, Docker, Git, Machine Learning, TensorFlow, PyTorch, Pandas, NumPy, Flask, Django, PostgreSQL, Redis, Kubernetes, Jenkins, CI/CD

EXPERIENCE
Senior Software Engineer - TechCorp Inc.
2021 - Present
• Developed scalable web applications using React and Node.js
• Implemented machine learning models for predictive analytics using TensorFlow and PyTorch
• Deployed applications on AWS using Docker containers and Kubernetes
• Built RESTful APIs using Python Flask and Django frameworks
• Optimized database queries in PostgreSQL and implemented Redis caching

Software Developer - StartupXYZ
2019 - 2021
• Built responsive web interfaces using JavaScript, HTML, and CSS
• Worked with MongoDB for data storage and retrieval
• Implemented CI/CD pipelines using Jenkins
• Collaborated with cross-functional teams using Git version control

EDUCATION
Master of Science in Computer Science
University of Technology, 2019

Bachelor of Science in Software Engineering
State University, 2017
"""
    return resume_content.encode('utf-8')

def test_resume_upload():
    """Test resume upload with a text file (simulating PDF)"""
    print("🔍 Testing Resume Upload...")
    
    # Create a text resume
    resume_content = create_test_resume()
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
        temp_file.write(resume_content)
        temp_pdf_path = temp_file.name
    
    try:
        # Upload the resume
        with open(temp_pdf_path, 'rb') as pdf_file:
            files = {'file': ('sarah_johnson_resume.pdf', pdf_file, 'application/pdf')}
            response = requests.post(f"{API_URL}/upload-resume", files=files)
        
        print(f"Response Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Resume upload successful!")
            
            # Check extracted data
            resume = data.get("resume", {})
            print(f"📋 Extracted Resume Data:")
            print(f"   Name: {resume.get('name', 'Not extracted')}")
            print(f"   Email: {resume.get('email', 'Not extracted')}")
            print(f"   Phone: {resume.get('phone', 'Not extracted')}")
            print(f"   Skills: {', '.join(resume.get('skills', []))}")
            print(f"   Total Skills Extracted: {len(resume.get('skills', []))}")
            
            # Verify specific skills were extracted
            expected_skills = ["Python", "JavaScript", "React", "Node.js", "MongoDB", "AWS", "Docker", "Git", "Machine Learning", "TensorFlow"]
            extracted_skills = resume.get('skills', [])
            found_skills = [skill for skill in expected_skills if skill in extracted_skills]
            
            print(f"   Expected Skills Found: {len(found_skills)}/{len(expected_skills)}")
            print(f"   Found Skills: {', '.join(found_skills)}")
            
            # Test database storage
            resume_id = resume.get('id')
            if resume_id:
                print(f"   Resume ID: {resume_id}")
                
                # Verify resume is stored in database
                get_response = requests.get(f"{API_URL}/resumes")
                if get_response.status_code == 200:
                    resumes = get_response.json()
                    resume_ids = [r.get('id') for r in resumes]
                    if resume_id in resume_ids:
                        print("✅ Resume successfully stored in database")
                    else:
                        print("❌ Resume not found in database")
                
                # Test job matching with uploaded resume
                match_response = requests.post(f"{API_URL}/match-jobs/{resume_id}")
                if match_response.status_code == 200:
                    match_data = match_response.json()
                    matches = match_data.get('matches', [])
                    print(f"✅ Job matching successful - {len(matches)} matches found")
                    
                    if matches:
                        best_match = matches[0]
                        print(f"   Best Match: {best_match['job']['title']} ({best_match['match_score']:.2f}%)")
                        print(f"   Matching Skills: {', '.join(best_match['matching_skills'])}")
                else:
                    print(f"❌ Job matching failed: {match_response.status_code}")
            
            return True
            
        else:
            print(f"❌ Resume upload failed with status code: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"   Error response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during resume upload test: {e}")
        return False
    
    finally:
        # Clean up temporary file
        if os.path.exists(temp_pdf_path):
            os.unlink(temp_pdf_path)

def test_service_connectivity():
    """Test basic service connectivity"""
    print("🔍 Testing Service Connectivity...")
    
    try:
        # Test API root
        response = requests.get(f"{API_URL}/", timeout=10)
        if response.status_code == 200:
            print("✅ Backend service is responding")
            return True
        else:
            print(f"❌ Backend service returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to connect to backend service: {e}")
        return False

def test_dependency_availability():
    """Test if required dependencies are available"""
    print("🔍 Testing Dependency Availability...")
    
    # Test by trying to import the dependencies that were missing
    try:
        import pdfplumber
        print("✅ pdfplumber dependency available")
    except ImportError:
        print("⚠️ pdfplumber not available - will use fallback")
    
    try:
        import docx2txt
        print("✅ docx2txt dependency available")
    except ImportError:
        print("⚠️ docx2txt not available - will use fallback")
    
    try:
        import scipy
        print("✅ scipy dependency available")
    except ImportError:
        print("❌ scipy dependency missing")
        return False
    
    return True

def test_error_handling():
    """Test error handling for invalid files"""
    print("🔍 Testing Error Handling...")
    
    # Test with invalid file type
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
        temp_file.write(b"This is not a valid resume file")
        temp_txt_path = temp_file.name
    
    try:
        with open(temp_txt_path, 'rb') as txt_file:
            files = {'file': ('invalid.txt', txt_file, 'text/plain')}
            response = requests.post(f"{API_URL}/upload-resume", files=files)
        
        if response.status_code == 400:
            print("✅ Correctly rejected invalid file type")
            return True
        else:
            print(f"❌ Expected 400 error, got {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Exception during error handling test: {e}")
        return False
    
    finally:
        if os.path.exists(temp_txt_path):
            os.unlink(temp_txt_path)

if __name__ == "__main__":
    print("🚀 Starting Resume Upload Specific Tests")
    print(f"🌐 Testing against: {API_URL}")
    print("=" * 60)
    
    # Run tests
    connectivity_ok = test_service_connectivity()
    dependencies_ok = test_dependency_availability()
    upload_ok = False
    error_handling_ok = False
    
    if connectivity_ok:
        upload_ok = test_resume_upload()
        error_handling_ok = test_error_handling()
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print(f"   Service Connectivity: {'✅ PASS' if connectivity_ok else '❌ FAIL'}")
    print(f"   Dependencies: {'✅ PASS' if dependencies_ok else '❌ FAIL'}")
    print(f"   Resume Upload: {'✅ PASS' if upload_ok else '❌ FAIL'}")
    print(f"   Error Handling: {'✅ PASS' if error_handling_ok else '❌ FAIL'}")
    
    if connectivity_ok and upload_ok and error_handling_ok:
        print("\n🎉 All critical tests passed! Resume upload functionality is working correctly.")
    else:
        print("\n❌ Some tests failed. Resume upload functionality needs attention.")