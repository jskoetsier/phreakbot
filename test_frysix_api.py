#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for Frys-IX API
This script tests various API endpoints to see which ones work
"""

import requests
import json
import sys

def test_api():
    """Test various API endpoints for Frys-IX"""
    # List of API URLs to try
    api_urls = [
        "https://ixpmanager.frys-ix.net/api/v4",
        "https://www.frys-ix.net/api/v4",
        "https://api.frys-ix.net/v4",
        "https://ixpmanager.frys-ix.net/api",
        "https://www.frys-ix.net/api"
    ]
    
    # List of endpoints to try
    endpoints = [
        "/member/list",
        "/members",
        "/members/list",
        "/public/member/list",
        "/public/members"
    ]
    
    # Headers to use
    headers = {
        'User-Agent': 'PhreakBot/1.0 (IRC Bot; +https://github.com/jskoetsier/phreakbot)'
    }
    
    # Try each API URL and endpoint
    for api_url in api_urls:
        print(f"\nTrying API URL: {api_url}")
        
        for endpoint in endpoints:
            full_url = f"{api_url}{endpoint}"
            print(f"\n  Testing endpoint: {full_url}")
            
            try:
                # Try to fetch data from the API
                response = requests.get(full_url, headers=headers, timeout=30)
                print(f"  Status code: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        # Try to parse the response as JSON
                        data = response.json()
                        print(f"  Response is valid JSON")
                        print(f"  Keys in response: {list(data.keys())}")
                        
                        # Check if the response contains member data
                        if "members" in data:
                            print(f"  Found 'members' key with {len(data['members'])} members")
                            print(f"  First member: {json.dumps(data['members'][0], indent=2)[:200]}...")
                        elif "data" in data and isinstance(data["data"], list):
                            print(f"  Found 'data' key with {len(data['data'])} items")
                            print(f"  First item: {json.dumps(data['data'][0], indent=2)[:200]}...")
                        else:
                            print(f"  No member data found in response")
                    except ValueError as e:
                        print(f"  Response is not valid JSON: {e}")
                        print(f"  Response content (first 200 chars): {response.text[:200]}")
                else:
                    print(f"  Failed with status code {response.status_code}")
                    print(f"  Response content (first 200 chars): {response.text[:200]}")
            except Exception as e:
                print(f"  Error: {e}")

if __name__ == "__main__":
    print("Testing Frys-IX API endpoints...")
    test_api()
    print("\nAPI testing complete")