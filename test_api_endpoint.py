#!/usr/bin/env python
"""
Debug script to test the wholesale API endpoint
"""
import requests
import json

# Test local API endpoint
BASE_URL = "http://localhost:8000"
API_ENDPOINT = f"{BASE_URL}/api/wholesales/"

def test_api_endpoint():
    print("🔍 Testing Wholesale API Endpoint")
    print("=" * 60)
    
    # Test GET request
    print("1. Testing GET request...")
    try:
        response = requests.get(API_ENDPOINT, timeout=5)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response length: {len(data)} items")
            
            if len(data) > 0:
                print("   Sample item:")
                sample = data[0]
                for key, value in sample.items():
                    print(f"     {key}: {value}")
                
                # Test PATCH request with first item
                if 'id' in sample:
                    test_patch_request(sample['id'])
            else:
                print("   No data returned")
        else:
            print(f"   Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection error - is Django server running?")
    except Exception as e:
        print(f"   ❌ Error: {e}")

def test_patch_request(wholesale_id):
    print(f"\n2. Testing PATCH request for ID {wholesale_id}...")
    
    patch_url = f"{API_ENDPOINT}{wholesale_id}/"
    patch_data = {
        "parent": None  # Set to root
    }
    
    try:
        response = requests.patch(
            patch_url,
            json=patch_data,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ PATCH request successful")
            print(f"   Updated parent: {data.get('parent')}")
            print(f"   Updated level: {data.get('level')}")
        else:
            print(f"   ❌ PATCH failed: {response.text}")
            
    except Exception as e:
        print(f"   ❌ PATCH error: {e}")

def test_create_test_data():
    print("\n3. Testing CREATE request...")
    
    create_data = {
        "name": "Test Wholesale API",
        "phone_number": "081234567890",
        "address": "Test Address",
        "city": "Test City",
        "pic": "Test PIC",
        "is_active": True
    }
    
    try:
        response = requests.post(
            API_ENDPOINT,
            json=create_data,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            print("   ✅ CREATE request successful")
            print(f"   Created ID: {data.get('id')}")
            print(f"   Created name: {data.get('name')}")
            print(f"   Created parent: {data.get('parent')}")
            print(f"   Created level: {data.get('level')}")
            return data.get('id')
        else:
            print(f"   ❌ CREATE failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ CREATE error: {e}")
        return None

if __name__ == "__main__":
    test_api_endpoint()
    
    # Test creating new data
    new_id = test_create_test_data()
    
    if new_id:
        print(f"\n4. Testing PATCH with new item {new_id}...")
        test_patch_request(new_id)
        
        # Clean up
        print(f"\n5. Cleaning up test data...")
        try:
            response = requests.delete(f"{API_ENDPOINT}{new_id}/", timeout=5)
            if response.status_code == 204:
                print("   ✅ Test data cleaned up")
            else:
                print(f"   ❌ Cleanup failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Cleanup error: {e}")
    
    print("\n🎉 API test completed!")
