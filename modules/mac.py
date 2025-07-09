#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# MAC address lookup module for PhreakBot

import re
import requests


def config(bot):
    """Return module configuration"""
    return {
        "events": [],
        "commands": ["mac"],
        "permissions": ["user"],
        "help": "Look up information about a MAC address.\n"
        "Usage: !mac <address> - Show MAC address vendor information\n"
        "Supports full or partial MAC addresses in various formats (e.g., 00:11:22:33:44:55, 001122334455, 00-11-22).",
    }


def run(bot, event):
    """Handle MAC address lookup command"""
    if event["command"] != "mac":
        return

    query = event["command_args"].strip()

    if not query:
        bot.add_response("Please provide a MAC address (e.g., !mac 00:11:22:33:44:55 or !mac 00-11-22)")
        return

    try:
        # Clean and validate the MAC address
        mac_address = clean_mac_address(query)
        if not mac_address:
            bot.add_response(f"Invalid MAC address format: {query}")
            return

        # Get MAC address information
        mac_info = get_mac_info(mac_address)
        bot.add_response(mac_info)

    except Exception as e:
        bot.logger.error(f"Error in MAC module: {e}")
        bot.add_response(f"Error looking up MAC information for {query}: {str(e)}")


def clean_mac_address(mac):
    """Clean and validate the MAC address format"""
    # Remove all non-hexadecimal characters
    mac = re.sub(r'[^0-9a-fA-F]', '', mac)
    
    # Check if we have a valid length (at least 6 characters for OUI lookup)
    if len(mac) < 6:
        return None
    
    # Truncate to first 6 characters (OUI) if longer than 12
    if len(mac) > 12:
        mac = mac[:12]
    
    return mac.upper()


def get_mac_info(mac):
    """Get information about a MAC address"""
    try:
        # Format MAC for display
        formatted_mac = format_mac_for_display(mac)
        
        # For OUI lookup, we need the first 6 characters (3 bytes)
        oui = mac[:6]
        
        # Use the macaddress.io API for lookup
        api_url = f"https://api.macaddress.io/v1?apiKey=at_XqJi1rAyYWQwMNBcOUGOdA7aMFKH8&output=json&search={oui}"
        
        response = requests.get(api_url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract vendor information
            vendor_name = data.get("vendorDetails", {}).get("companyName", "Unknown")
            vendor_address = data.get("vendorDetails", {}).get("companyAddress", "Unknown")
            
            # Check if this is a partial MAC address
            is_partial = len(mac) < 12
            partial_note = " (Partial MAC - showing OUI information only)" if is_partial else ""
            
            # Format the result
            result = f"MAC: {formatted_mac}{partial_note} | Vendor: {vendor_name} | Address: {vendor_address}"
            
            # Add block type information if available
            block_type = data.get("blockDetails", {}).get("blockType", None)
            if block_type:
                result += f" | Block Type: {block_type}"
                
            return result
        else:
            # Fallback to macvendors.co API if the first one fails
            api_url = f"https://api.macvendors.com/{oui}"
            response = requests.get(api_url, timeout=5)
            
            if response.status_code == 200:
                vendor_name = response.text.strip()
                
                # Check if this is a partial MAC address
                is_partial = len(mac) < 12
                partial_note = " (Partial MAC - showing OUI information only)" if is_partial else ""
                
                # Format the result
                result = f"MAC: {formatted_mac}{partial_note} | Vendor: {vendor_name}"
                return result
            else:
                return f"MAC: {formatted_mac} | Vendor: Unknown (No information found)"

    except Exception as e:
        return f"Error processing MAC {mac}: {str(e)}"


def format_mac_for_display(mac):
    """Format MAC address for display"""
    # If it's a partial MAC, pad with zeros to make it look nicer
    if len(mac) < 12:
        mac = mac.ljust(12, '0')
    
    # Format as XX:XX:XX:XX:XX:XX
    return ':'.join(mac[i:i+2] for i in range(0, len(mac), 2))