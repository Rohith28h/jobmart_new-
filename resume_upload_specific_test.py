#!/usr/bin/env python3
"""
Specific test for resume upload functionality after dependency fix
"""
import requests
import tempfile
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io

# Backend URL
BACKEND_URL = "https://resume-upload-fix-1.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

def create_test_pdf_resume():
    """Create a real PDF resume for testing"""
    buffer = io.BytesIO()
    
    # Create PDF with reportlab
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Add resume content
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, height - 100, "Sarah Johnson")
    
    p.setFont("Helvetica", 12)
    p.drawString(100, height - 120, "sarah.johnson@email.com")
    p.drawString(100, height - 140, "(555) 987-6543")
    
    p.setFont("Helvetica-Bold", 14)
    p.drawString(100, height - 180, "TECHNICAL SKILLS")
    
    p.setFont("Helvetica", 12)
    skills_text = "Python, JavaScript, React, Node.js, MongoDB, AWS, Docker, Git, Machine Learning, TensorFlow"
    p.drawString(100, height - 200, skills_text)
    
    p.setFont("Helvetica-Bold", 14)
    p.drawString(100, height - 240, "EXPERIENCE")
    
    p.setFont("Helvetica", 12)
    p.drawString(100, height - 260, "Senior Software Engineer - TechCorp Inc.")
    p.drawString(100, height - 280, "2021 - Present")
    p.drawString(100, height - 300, "• Developed scalable web applications using React and Node.js")
    p.drawString(100, height - 320, "• Implemented machine learning models for predictive analytics")
    p.drawString(100, height - 340, "• Deployed applications on AWS using Docker containers")
    
    p.drawString(100, height - 380, "Software Developer - StartupXYZ")
    p.drawString(100, height - 400, "2019 - 2021")
    p.drawString(100, height - 420, "• Built responsive web interfaces using JavaScript and CSS")
    p.drawString(100, height - 440, "• Worked with MongoDB for data storage and retrieval")
    
    p.setFont("Helvetica-Bold", 14)
    p.drawString(100, height - 480, "EDUCATION")
    
    p.setFont("Helvetica", 12)
    p.drawString(100, height - 500, "Master of Science in Computer Science")
    p.drawString(100, height - 520, "University of Technology, 2019")
    
    p.save()
    
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return pdf_content

def test_resume_upload_with_real_pdf():
    """Test resume upload with a real PDF file"""
    print("🔍 Testing Resume Upload with Real PDF...")
    
    # Create a real PDF resume
    pdf_content = create_test_pdf_resume()
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
        temp_file.write(pdf_content)
        temp_pdf_path = temp_file.name
    
    try:
        # Upload the PDF resume
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

if __name__ == "__main__":
    print("🚀 Starting Resume Upload Specific Tests")
    print(f"🌐 Testing against: {API_URL}")
    print("=" * 60)
    
    # Run tests
    connectivity_ok = test_service_connectivity()
    dependencies_ok = test_dependency_availability()
    
    if connectivity_ok and dependencies_ok:
        upload_ok = test_resume_upload_with_real_pdf()
        
        print("\n" + "=" * 60)
        print("📊 Test Results Summary:")
        print(f"   Service Connectivity: {'✅ PASS' if connectivity_ok else '❌ FAIL'}")
        print(f"   Dependencies: {'✅ PASS' if dependencies_ok else '❌ FAIL'}")
        print(f"   Resume Upload: {'✅ PASS' if upload_ok else '❌ FAIL'}")
        
        if connectivity_ok and dependencies_ok and upload_ok:
            print("\n🎉 All tests passed! Resume upload functionality is working correctly.")
        else:
            print("\n❌ Some tests failed. Resume upload functionality needs attention.")
    else:
        print("\n❌ Basic connectivity or dependency issues detected.")