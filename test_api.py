"""
Test script for Cricket News Bot API
Run this after starting the server to verify all endpoints
"""
import requests
import time

BASE_URL = "http://localhost:8000"

def test_endpoint(method, endpoint, description):
    """Test a single endpoint"""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Endpoint: {method} {endpoint}")
    print(f"{'='*60}")
    
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=30)
        elif method == "POST":
            response = requests.post(f"{BASE_URL}{endpoint}", timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success!")
            print(f"Response Preview: {str(data)[:200]}...")
            return True
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("🏏 Cricket News Bot API Test Suite")
    print("="*60)
    print(f"Testing API at: {BASE_URL}")
    print("Make sure the server is running!")
    print("="*60)
    
    time.sleep(1)
    
    results = []
    
    # Test all endpoints
    results.append(test_endpoint("GET", "/", "Root Endpoint"))
    results.append(test_endpoint("GET", "/api/health", "Health Check"))
    results.append(test_endpoint("GET", "/api/articles", "Get All Articles"))
    results.append(test_endpoint("GET", "/api/headlines", "Get Today's Headlines"))
    results.append(test_endpoint("GET", "/api/status", "Get Bot Status"))
    results.append(test_endpoint("GET", "/api/scheduler/status", "Scheduler Status"))
    results.append(test_endpoint("GET", "/api/scheduler/health", "Scheduler Health"))
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n✅ All tests passed! API is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Check the output above.")
    
    print("\n" + "="*60)
    print("🔗 Useful Links:")
    print(f"  - Interactive Docs: {BASE_URL}/docs")
    print(f"  - Alternative Docs: {BASE_URL}/redoc")
    print(f"  - OpenAPI JSON: {BASE_URL}/openapi.json")
    print("="*60)
    
    # Optional: Test manual trigger (commented out by default)
    print("\n⚠️ Manual trigger test is disabled by default.")
    print("To test manual trigger, uncomment the line in test_api.py")
    # Uncomment the line below to test manual trigger
    # test_endpoint("POST", "/api/trigger", "Manual News Fetch (This will post to Telegram!)")

if __name__ == "__main__":
    main()
