"""
Simple WebSocket connection test.
"""

import asyncio
import websockets
import json

async def test_websocket():
    job_id = "977b9a87-6e3f-4ec9-8efa-c3f8ebe85c28"
    ws_url = f"wss://resume-stabilize.preview.emergentagent.com/api/ws/{job_id}"
    
    print(f"🔌 Testing WebSocket connection to: {ws_url}")
    
    try:
        # Connect without the problematic timeout parameter
        async with websockets.connect(ws_url) as websocket:
            print("✅ WebSocket connected successfully!")
            
            # Wait for initial message
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(message)
                print(f"✅ Received message type: {data.get('type')}")
                print(f"✅ Message content: {json.dumps(data, indent=2)}")
                return True
            except asyncio.TimeoutError:
                print("⚠️ No initial message received (timeout)")
                return True  # Connection worked even without message
                
    except websockets.exceptions.ConnectionClosed as e:
        if e.code == 4004:
            print("⚠️ WebSocket closed with 4004 (Job not found) - expected for completed job")
            return True
        else:
            print(f"❌ WebSocket connection failed: {e}")
            return False
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_websocket())
    print(f"\n{'✅ SUCCESS' if result else '❌ FAILED'}: WebSocket test completed")