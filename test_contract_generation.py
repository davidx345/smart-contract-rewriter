#!/usr/bin/env python3
"""
Test script to verify contract generation functionality.
This script tests the backend endpoints for contract generation.
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1/contracts"

def test_contract_generation():
    """Test the contract generation endpoint"""
    print("🧪 Testing Contract Generation Endpoint...")
    
    # Test data
    generation_request = {
        "description": "Create a simple ERC20 token contract with basic transfer functionality and owner controls",
        "contract_name": "TestToken",
        "features": ["ERC20", "Ownable", "Pausable"],
        "compiler_version": "0.8.19"
    }
    
    try:
        # Test contract generation
        print(f"📤 Sending generation request to {API_BASE}/generate")
        response = requests.post(
            f"{API_BASE}/generate",
            json=generation_request,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Contract generation successful!")
            print(f"📋 Request ID: {result.get('request_id')}")
            print(f"⏱️  Processing Time: {result.get('processing_time_seconds', 0):.2f}s")
            print(f"📝 Message: {result.get('message')}")
            print(f"🔗 Generation Notes: {result.get('generation_notes', 'N/A')}")
            
            if result.get('original_code'):
                code_length = len(result['original_code'])
                print(f"📄 Generated Code Length: {code_length} characters")
                print("📄 Generated Code Preview:")
                print("-" * 50)
                print(result['original_code'][:500] + "..." if code_length > 500 else result['original_code'])
                print("-" * 50)
            
            return result.get('request_id')
        else:
            print(f"❌ Generation failed: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def test_contract_history():
    """Test the contract history endpoint to verify generated contracts appear"""
    print("\n🧪 Testing Contract History Endpoint...")
    
    try:
        print(f"📤 Fetching history from {API_BASE}/history")
        response = requests.get(f"{API_BASE}/history")
        
        print(f"📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            history = response.json()
            print(f"✅ History retrieved successfully!")
            print(f"📊 Total contracts: {len(history)}")
            
            # Look for generated contracts
            generated_contracts = [item for item in history if item.get('type') == 'generation']
            print(f"🤖 Generated contracts found: {len(generated_contracts)}")
            
            if generated_contracts:
                print("\n🔍 Generated contracts details:")
                for contract in generated_contracts[:3]:  # Show first 3
                    print(f"  - ID: {contract.get('id')}")
                    print(f"    Name: {contract.get('contract_name')}")
                    print(f"    Timestamp: {contract.get('timestamp')}")
                    print(f"    Success: {contract.get('success')}")
                    details = contract.get('details', {})
                    if details.get('description'):
                        print(f"    Description: {details['description'][:100]}...")
                    print()
            
            return len(generated_contracts) > 0
        else:
            print(f"❌ History fetch failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error fetching history: {e}")
        return False

def test_health_check():
    """Test if the backend is running"""
    print("🧪 Testing Backend Health...")
    
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is healthy!")
            return True
        else:
            print(f"⚠️  Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend not accessible: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Contract Generation Tests")
    print("=" * 50)
    
    # Health check first
    if not test_health_check():
        print("\n❌ Backend is not running. Please start the backend server first.")
        print("Run: cd backend && python -m uvicorn app.main:app --reload")
        return
    
    # Test contract generation
    request_id = test_contract_generation()
    
    # Small delay for database operations
    if request_id:
        print("\n⏳ Waiting for database operations...")
        time.sleep(2)
    
    # Test history retrieval
    history_has_generated = test_contract_history()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"  ✅ Backend Health: {'PASS' if True else 'FAIL'}")
    print(f"  ✅ Contract Generation: {'PASS' if request_id else 'FAIL'}")
    print(f"  ✅ History Contains Generated: {'PASS' if history_has_generated else 'FAIL'}")
    
    if request_id and history_has_generated:
        print("\n🎉 All tests passed! Contract generation is working correctly.")
        print("✨ The feature should work in the frontend now.")
    else:
        print("\n⚠️  Some tests failed. Check the backend logs for more details.")

if __name__ == "__main__":
    main()
