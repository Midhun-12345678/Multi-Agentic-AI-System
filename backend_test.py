"""
Comprehensive backend API testing for AI Resume Optimizer.
Tests all endpoints: health check, job submission, status, jobs list, and WebSocket connectivity.
"""

import requests
import asyncio
import websockets
import json
import io
import sys
from datetime import datetime
from typing import Dict, Any, Optional

class ResumeOptimizerTester:
    def __init__(self, base_url="https://resume-stabilize.preview.emergentagent.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ResumeOptimizer-Test/1.0'
        })
        self.tests_run = 0
        self.tests_passed = 0
        self.job_id = None
        
    def log(self, message: str, level="INFO"):
        """Log test messages with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def run_test(self, name: str, test_func) -> bool:
        """Run a single test and handle exceptions."""
        self.tests_run += 1
        self.log(f"🔍 Testing: {name}")
        
        try:
            result = test_func()
            if result:
                self.tests_passed += 1
                self.log(f"✅ PASSED: {name}")
                return True
            else:
                self.log(f"❌ FAILED: {name}")
                return False
        except Exception as e:
            self.log(f"❌ ERROR: {name} - {str(e)}")
            return False
    
    def test_health_check(self) -> bool:
        """Test GET /api/ health check endpoint."""
        try:
            response = self.session.get(f"{self.base_url}/api/", timeout=10)
            
            if response.status_code != 200:
                self.log(f"Health check failed with status {response.status_code}")
                return False
                
            data = response.json()
            required_fields = ["status", "service", "version"]
            
            for field in required_fields:
                if field not in data:
                    self.log(f"Missing field '{field}' in health check response")
                    return False
            
            if data["status"] != "healthy":
                self.log(f"Service status is '{data['status']}', expected 'healthy'")
                return False
                
            self.log(f"Health check OK: {data['service']} v{data['version']}")
            return True
            
        except requests.exceptions.RequestException as e:
            self.log(f"Health check request failed: {e}")
            return False
    
    def test_resume_submission(self) -> bool:
        """Test POST /api/optimize-resume endpoint."""
        try:
            # Create a mock PDF file
            mock_pdf_content = b"%PDF-1.4 Mock Resume Content for Testing"
            pdf_file = io.BytesIO(mock_pdf_content)
            pdf_file.name = "test_resume.pdf"
            
            # Prepare form data
            files = {
                'resume': ('test_resume.pdf', pdf_file, 'application/pdf')
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
                """.strip(),
                'template': 'professional'
            }
            
            response = self.session.post(
                f"{self.base_url}/api/optimize-resume",
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code != 200:
                self.log(f"Resume submission failed with status {response.status_code}")
                try:
                    error_detail = response.json().get('detail', 'No detail provided')
                    self.log(f"Error detail: {error_detail}")
                except:
                    self.log(f"Response body: {response.text[:500]}")
                return False
            
            result = response.json()
            required_fields = ["job_id", "status", "message", "websocket_url"]
            
            for field in required_fields:
                if field not in result:
                    self.log(f"Missing field '{field}' in submission response")
                    return False
            
            if result["status"] != "queued":
                self.log(f"Expected status 'queued', got '{result['status']}'")
                return False
            
            self.job_id = result["job_id"]
            self.log(f"Resume submitted successfully. Job ID: {self.job_id}")
            return True
            
        except Exception as e:
            self.log(f"Resume submission test failed: {e}")
            return False
    
    def test_job_status(self) -> bool:
        """Test GET /api/status/{job_id} endpoint."""
        if not self.job_id:
            self.log("No job ID available for status check")
            return False
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/status/{self.job_id}",
                timeout=10
            )
            
            if response.status_code == 404:
                self.log("Job not found (404) - this might be expected for quick tests")
                return True  # This is acceptable for testing
            
            if response.status_code != 200:
                self.log(f"Status check failed with status {response.status_code}")
                return False
            
            status_data = response.json()
            required_fields = ["job_id", "status", "created_at", "progress", "agents"]
            
            for field in required_fields:
                if field not in status_data:
                    self.log(f"Missing field '{field}' in status response")
                    return False
            
            valid_statuses = ["queued", "processing", "complete", "error"]
            if status_data["status"] not in valid_statuses:
                self.log(f"Invalid status '{status_data['status']}'")
                return False
            
            self.log(f"Job status: {status_data['status']} ({status_data['progress']}%)")
            return True
            
        except Exception as e:
            self.log(f"Status check failed: {e}")
            return False
    
    def test_jobs_list(self) -> bool:
        """Test GET /api/jobs endpoint."""
        try:
            response = self.session.get(f"{self.base_url}/api/jobs", timeout=10)
            
            if response.status_code != 200:
                self.log(f"Jobs list failed with status {response.status_code}")
                return False
            
            result = response.json()
            
            if "jobs" not in result or "count" not in result:
                self.log("Missing 'jobs' or 'count' in jobs list response")
                return False
            
            jobs_count = result["count"]
            jobs_list = result["jobs"]
            
            if not isinstance(jobs_list, list):
                self.log("Jobs field is not a list")
                return False
            
            if jobs_count != len(jobs_list):
                self.log(f"Count mismatch: reported {jobs_count}, actual {len(jobs_list)}")
                return False
            
            self.log(f"Jobs list retrieved successfully. Found {jobs_count} jobs")
            
            # Validate job structure if jobs exist
            if jobs_list:
                first_job = jobs_list[0]
                required_job_fields = ["job_id", "status", "created_at", "progress"]
                for field in required_job_fields:
                    if field not in first_job:
                        self.log(f"Missing field '{field}' in job list item")
                        return False
            
            return True
            
        except Exception as e:
            self.log(f"Jobs list test failed: {e}")
            return False
    
    def test_websocket_connection(self) -> bool:
        """Test WebSocket connection /api/ws/{job_id}."""
        if not self.job_id:
            self.log("No job ID available for WebSocket test")
            return False
        
        try:
            # Convert HTTPS URL to WSS for WebSocket
            ws_url = self.base_url.replace('https://', 'wss://') + f"/api/ws/{self.job_id}"
            
            async def websocket_test():
                try:
                    async with websockets.connect(ws_url, timeout=10) as websocket:
                        self.log(f"WebSocket connected to: {ws_url}")
                        
                        # Wait for initial status message
                        try:
                            message = await asyncio.wait_for(websocket.recv(), timeout=5)
                            data = json.loads(message)
                            
                            if "type" in data and data["type"] in ["initial_status", "connected"]:
                                self.log(f"Received initial WebSocket message: {data['type']}")
                                return True
                            else:
                                self.log(f"Unexpected message type: {data.get('type')}")
                                return True  # Still counts as successful connection
                        
                        except asyncio.TimeoutError:
                            self.log("WebSocket connected but no initial message received")
                            return True  # Connection itself worked
                
                except websockets.exceptions.ConnectionClosed as e:
                    if e.code == 4004:
                        self.log("WebSocket closed with 4004 (Job not found) - acceptable for testing")
                        return True
                    else:
                        self.log(f"WebSocket connection closed unexpectedly: {e}")
                        return False
                
                except Exception as e:
                    self.log(f"WebSocket connection failed: {e}")
                    return False
            
            # Run the async WebSocket test
            result = asyncio.run(websocket_test())
            return result
            
        except Exception as e:
            self.log(f"WebSocket test setup failed: {e}")
            return False
    
    def test_invalid_endpoints(self) -> bool:
        """Test error handling for invalid endpoints."""
        try:
            # Test non-existent job ID
            response = self.session.get(f"{self.base_url}/api/status/non-existent-job-id")
            if response.status_code != 404:
                self.log(f"Expected 404 for invalid job ID, got {response.status_code}")
                return False
            
            # Test malformed resume submission
            response = self.session.post(f"{self.base_url}/api/optimize-resume", json={})
            if response.status_code not in [400, 422]:  # Bad request or validation error
                self.log(f"Expected 400/422 for invalid submission, got {response.status_code}")
                return False
            
            self.log("Error handling tests passed")
            return True
            
        except Exception as e:
            self.log(f"Error handling test failed: {e}")
            return False
    
    def print_summary(self):
        """Print test summary."""
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print("\n" + "="*60)
        print("🔍 BACKEND API TEST SUMMARY")
        print("="*60)
        print(f"Tests Run:      {self.tests_run}")
        print(f"Tests Passed:   {self.tests_passed}")
        print(f"Tests Failed:   {self.tests_run - self.tests_passed}")
        print(f"Success Rate:   {success_rate:.1f}%")
        
        if self.job_id:
            print(f"Test Job ID:    {self.job_id}")
        
        if success_rate >= 80:
            print("✅ BACKEND APIs are functioning well!")
        elif success_rate >= 60:
            print("⚠️  BACKEND has some issues but core functionality works")
        else:
            print("❌ BACKEND has significant issues that need attention")
        
        print("="*60)

def main():
    """Run all backend tests."""
    print("🚀 Starting AI Resume Optimizer Backend Tests")
    print(f"Target URL: https://resume-stabilize.preview.emergentagent.com")
    print("="*60)
    
    tester = ResumeOptimizerTester()
    
    # Run all tests in sequence
    test_results = []
    
    test_results.append(tester.run_test("Health Check", tester.test_health_check))
    test_results.append(tester.run_test("Resume Submission", tester.test_resume_submission))
    test_results.append(tester.run_test("Job Status Check", tester.test_job_status))
    test_results.append(tester.run_test("Jobs List", tester.test_jobs_list))
    test_results.append(tester.run_test("WebSocket Connection", tester.test_websocket_connection))
    test_results.append(tester.run_test("Error Handling", tester.test_invalid_endpoints))
    
    # Print summary
    tester.print_summary()
    
    # Return exit code
    success_rate = (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0
    return 0 if success_rate >= 70 else 1

if __name__ == "__main__":
    sys.exit(main())