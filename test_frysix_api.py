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
    """Test the correct Frys-IX API endpoint"""
    # The correct API endpoint provided by the user
    api_url = "https://ixpmanager.frys-ix.net/api/v4/member-export/ixf/1.0"

    print(f"\nTesting the correct API endpoint: {api_url}")

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
                print(f"Keys in response: {list(data.keys())}")

                # Print the structure of the response
                print("\nResponse structure:")
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, list):
                            print(f"  {key}: list with {len(value)} items")
                            if value and len(value) > 0:
                                print(f"  First item in {key}: {json.dumps(value[0], indent=2)[:200]}...")
                        elif isinstance(value, dict):
                            print(f"  {key}: dict with keys {list(value.keys())}")
                        else:
                            print(f"  {key}: {value}")

                # Check for member data in various formats
                if "member_list" in data:
                    print(f"\nFound 'member_list' with {len(data['member_list'])} items")
                    if data['member_list']:
                        print(f"First member: {json.dumps(data['member_list'][0], indent=2)[:200]}...")
                elif "members" in data:
                    print(f"\nFound 'members' with {len(data['members'])} items")
                    if data['members']:
                        print(f"First member: {json.dumps(data['members'][0], indent=2)[:200]}...")
                elif "data" in data and isinstance(data["data"], list):
                    print(f"\nFound 'data' with {len(data['data'])} items")
                    if data['data']:
                        print(f"First item: {json.dumps(data['data'][0], indent=2)[:200]}...")
                else:
                    print("\nNo obvious member data found in response")
                    print(f"Full response (first 500 chars): {json.dumps(data, indent=2)[:500]}...")
            except ValueError as e:
                print(f"Response is not valid JSON: {e}")
                print(f"Response content (first 200 chars): {response.text[:200]}")
        else:
            print(f"Failed with status code {response.status_code}")
            print(f"Response content (first 200 chars): {response.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Testing Frys-IX API endpoints...")
    test_api()
    print("\nAPI testing complete")
