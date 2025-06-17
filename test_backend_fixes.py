#!/usr/bin/env python3
"""
Simple test script to verify backend fixes for contract history.
This script tests the new delete endpoint and improved history data structure.
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api/v1"

def test_health():
    """Test if the backend is running"""
    try:
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/health")
        print(f"✓ Health check: {response.json()}")
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

def test_contract_history():
    """Test the improved contract history endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/contracts/history")
        data = response.json()
        print(f"✓ History endpoint status: {response.status_code}")
        print(f"✓ History data structure: {len(data)} items")
        
        if data:
            first_item = data[0]
            print(f"✓ First item structure: {list(first_item.keys())}")
            if 'details' in first_item:
                print(f"✓ Details keys: {list(first_item['details'].keys())}")
        
        return data
    except Exception as e:
        print(f"✗ History test failed: {e}")
        return None

def test_delete_endpoint(contract_id):
    """Test the new delete endpoint"""
    try:
        response = requests.delete(f"{BASE_URL}/contracts/history/{contract_id}")
        print(f"✓ Delete endpoint status: {response.status_code}")
        if response.status_code == 200:
            print(f"✓ Delete response: {response.json()}")
            return True
        elif response.status_code == 404:
            print(f"✓ Contract {contract_id} not found (expected)")
            return True
        else:
            print(f"✗ Unexpected delete response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Delete test failed: {e}")
        return False

def main():
    print("🧪 Testing Smart Contract Rewriter Backend Fixes")
    print("=" * 50)
    
    # Test 1: Health check
    if not test_health():
        print("❌ Backend is not running. Please start with: docker-compose up")
        return
    
    # Test 2: Contract history with improved data structure
    history_data = test_contract_history()
    
    # Test 3: Delete endpoint (use a non-existent ID to avoid deleting real data)
    test_delete_endpoint("999999")
    
    # Test 4: If there's real data, show the improved structure
    if history_data:
        print("\n📊 Sample Data Structure:")
        print("-" * 30)
        for item in history_data[:2]:  # Show first 2 items
            print(f"ID: {item.get('id')}")
            print(f"Type: {item.get('type')}")
            print(f"Name: {item.get('contract_name', 'N/A')}")
            print(f"Success: {item.get('success', 'N/A')}")
            
            details = item.get('details', {})
            if item.get('type') == 'analysis':
                vuln_count = details.get('vulnerabilities_count', 0)
                print(f"Vulnerabilities: {vuln_count}")
            elif item.get('type') == 'rewrite':
                gas_savings = details.get('gas_savings_percentage', 0)
                changes = details.get('changes_count', 0)
                print(f"Gas Savings: {gas_savings}%")
                print(f"Changes: {changes}")
            print("-" * 30)
    
    print("\n✅ Backend testing completed")

if __name__ == "__main__":
    main()
