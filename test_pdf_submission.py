"""
Test resume submission with a real PDF file.
"""

import requests
import io
import sys
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_test_pdf():
    """Create a proper PDF file for testing."""
    buffer = io.BytesIO()
    
    # Create PDF with reportlab
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Add content to the PDF
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 100, "John Doe")
    
    c.setFont("Helvetica", 12)
    c.drawString(100, height - 130, "Senior Software Engineer")
    c.drawString(100, height - 150, "Email: john.doe@email.com")
    c.drawString(100, height - 170, "Phone: (555) 123-4567")
    
    c.drawString(100, height - 210, "Experience:")
    c.drawString(120, height - 230, "• 5+ years of software development")
    c.drawString(120, height - 250, "• Python, JavaScript, React expertise")
    c.drawString(120, height - 270, "• API design and microservices")
    c.drawString(120, height - 290, "• AWS/GCP cloud platforms")
    
    c.drawString(100, height - 330, "Education:")
    c.drawString(120, height - 350, "• B.S. Computer Science")
    c.drawString(120, height - 370, "• University of Technology")
    
    c.save()
    buffer.seek(0)
    return buffer

def test_with_real_pdf():
    """Test resume submission with a properly formatted PDF."""
    base_url = "https://resume-stabilize.preview.emergentagent.com"
    
    print("🔧 Testing resume submission with proper PDF...")
    
    try:
        # Create a real PDF
        pdf_buffer = create_test_pdf()
        
        # Prepare form data
        files = {
            'resume': ('john_doe_resume.pdf', pdf_buffer, 'application/pdf')
        }
        
        data = {
            'job_description': """
            Senior Software Engineer position at a leading tech company.
            We are looking for an experienced developer with expertise in:
            - Python, JavaScript, React
            - API design and microservices
            - Cloud platforms (AWS/GCP)
            - Database design (SQL/NoSQL)
            - Agile development methodologies
            - Strong problem-solving skills
            
            The ideal candidate will have 5+ years of experience building scalable web applications.
            Bachelor's degree in Computer Science or related field preferred.
            """.strip(),
            'template': 'professional'
        }
        
        response = requests.post(
            f"{base_url}/api/optimize-resume",
            files=files,
            data=data,
            timeout=30
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ PDF submission successful!")
            print(f"Job ID: {result.get('job_id')}")
            print(f"Status: {result.get('status')}")
            print(f"Message: {result.get('message')}")
            return result.get('job_id')
        else:
            print(f"❌ PDF submission failed: {response.status_code}")
            try:
                error_detail = response.json().get('detail', 'No detail provided')
                print(f"Error: {error_detail}")
            except:
                print(f"Response: {response.text[:500]}")
            return None
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return None

def test_job_status(job_id):
    """Test job status endpoint with the job ID."""
    if not job_id:
        print("No job ID to test status")
        return
        
    base_url = "https://resume-stabilize.preview.emergentagent.com"
    
    print(f"\n🔧 Testing job status for ID: {job_id}")
    
    try:
        response = requests.get(f"{base_url}/api/status/{job_id}", timeout=10)
        
        print(f"Status Response: {response.status_code}")
        
        if response.status_code == 200:
            status_data = response.json()
            print("✅ Job status retrieved successfully!")
            print(f"Status: {status_data.get('status')}")
            print(f"Progress: {status_data.get('progress')}%")
            print(f"Created: {status_data.get('created_at')}")
        else:
            print(f"❌ Status check failed: {response.status_code}")
            try:
                print(f"Error: {response.json()}")
            except:
                print(f"Response: {response.text[:200]}")
                
    except Exception as e:
        print(f"❌ Status test failed: {e}")

if __name__ == "__main__":
    # Test with proper PDF
    job_id = test_with_real_pdf()
    
    # Test status if job was created
    if job_id:
        test_job_status(job_id)
        print(f"\n💡 You can check job progress at: https://resume-stabilize.preview.emergentagent.com/api/status/{job_id}")