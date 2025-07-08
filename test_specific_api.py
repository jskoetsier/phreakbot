#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for the specific Frys-IX API endpoint
"""

import requests
import json
import sys

def test_specific_api():
    """Test the specific Frys-IX API endpoint"""
    # The correct API endpoint provided by the user
    api_url = "https://ixpmanager.frys-ix.net/api/v4/member-export/ixf/1.0"
    
    print(f"Testing API endpoint: {api_url}")

    # Headers to use
    headers = {
        'User-Agent': 'PhreakBot/1.0 (IRC Bot; +https://github.com/jskoetsier/phreakbot)'
    }

    try:
        # Try to fetch data from the API
        print(f"Sending request to: {api_url}")
        response = requests.get(api_url, headers=headers, timeout=30)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                # Try to parse the response as JSON
                data = response.json()
                print(f"Response is valid JSON")
                print(f"Top-level keys in response: {list(data.keys())}")
                
                # Print the structure of the response
                print("\nResponse structure:")
                for key, value in data.items():
                    if isinstance(value, list):
                        print(f"  {key}: list with {len(value)} items")
                        if value and len(value) > 0:
                            print(f"  First item in {key} (truncated): {json.dumps(value[0], indent=2)[:200]}...")
                    elif isinstance(value, dict):
                        print(f"  {key}: dict with keys {list(value.keys())}")
                    else:
                        print(f"  {key}: {value}")
                
                # Look for member data in the IXF format
                if "member_list" in data:
                    print(f"\nFound 'member_list' with {len(data['member_list'])} members")
                    if data['member_list']:
                        member = data['member_list'][0]
                        print(f"First member sample: {json.dumps(member, indent=2)[:300]}...")
                        
                        # Extract ASN and member name for a sample
                        if "asnum" in member:
                            print(f"Sample ASN: {member['asnum']}")
                        if "member_name" in member:
                            print(f"Sample name: {member['member_name']}")
                else:
                    print("\nNo 'member_list' found in response")
                    print(f"Full response (truncated): {json.dumps(data, indent=2)[:500]}...")
            except ValueError as e:
                print(f"Response is not valid JSON: {e}")
                print(f"Response content (first 200 chars): {response.text[:200]}")
        else:
            print(f"Failed with status code {response.status_code}")
            print(f"Response content (first 200 chars): {response.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Testing specific Frys-IX API endpoint...")
    test_specific_api()
    print("\nAPI testing complete")