"""
Comprehensive test with working job ID.
"""

import requests
import asyncio
import websockets
import json
import time

def test_comprehensive_apis():
    """Test all APIs with the working job ID."""
    base_url = "https://resume-stabilize.preview.emergentagent.com"
    job_id = "977b9a87-6e3f-4ec9-8efa-c3f8ebe85c28"
    
    print("🔍 COMPREHENSIVE API TESTING")
    print("="*50)
    
    tests_passed = 0
    total_tests = 4
    
    # Test 1: Job Status
    try:
        print("\n1️⃣ Testing Job Status...")
        response = requests.get(f"{base_url}/api/status/{job_id}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {data.get('status')} ({data.get('progress')}%)")
            tests_passed += 1
        else:
            print(f"❌ Status failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Status error: {e}")
    
    # Test 2: Jobs List
    try:
        print("\n2️⃣ Testing Jobs List...")
        response = requests.get(f"{base_url}/api/jobs", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {data.get('count')} total jobs")
            tests_passed += 1
        else:
            print(f"❌ Jobs list failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Jobs list error: {e}")
    
    # Test 3: Jobs List with Filter
    try:
        print("\n3️⃣ Testing Jobs List with Filter...")
        response = requests.get(f"{base_url}/api/jobs?status=processing", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {data.get('count')} processing jobs")
            tests_passed += 1
        else:
            print(f"❌ Filtered jobs list failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Filtered jobs list error: {e}")
    
    # Test 4: WebSocket Connection
    try:
        print("\n4️⃣ Testing WebSocket Connection...")
        ws_url = base_url.replace('https://', 'wss://') + f"/api/ws/{job_id}"
        
        async def websocket_test():
            try:
                async with websockets.connect(ws_url, timeout=10) as websocket:
                    print(f"✅ WebSocket connected successfully")
                    
                    # Wait for initial message
                    message = await asyncio.wait_for(websocket.recv(), timeout=5)
                    data = json.loads(message)
                    print(f"✅ Received: {data.get('type')} event")
                    return True
                    
            except Exception as e:
                print(f"❌ WebSocket error: {e}")
                return False
        
        result = asyncio.run(websocket_test())
        if result:
            tests_passed += 1
            
    except Exception as e:
        print(f"❌ WebSocket test error: {e}")
    
    print(f"\n{'='*50}")
    print(f"📊 RESULTS: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 ALL BACKEND APIS WORKING PERFECTLY!")
        return True
    elif tests_passed >= 3:
        print("✅ BACKEND APIS MOSTLY WORKING")
        return True
    else:
        print("❌ BACKEND HAS SIGNIFICANT ISSUES")
        return False

if __name__ == "__main__":
    success = test_comprehensive_apis()
    
    # Show job processing status
    print(f"\n💡 Monitor job progress:")
    print(f"curl https://resume-stabilize.preview.emergentagent.com/api/status/977b9a87-6e3f-4ec9-8efa-c3f8ebe85c28")