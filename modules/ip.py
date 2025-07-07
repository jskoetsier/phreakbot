#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# IP lookup module for PhreakBot

import re
import socket
import ipaddress
import requests


def config(bot):
    """Return module configuration"""
    return {
        "events": [],
        "commands": ["ip"],
        "permissions": ["user"],
        "help": "Look up information about an IP address or hostname.\n"
        "Usage: !ip <hostname|ip> - Show IP information",
    }


def run(bot, event):
    """Handle IP lookup command"""
    if event["command"] != "ip":
        return

    query = event["command_args"].strip()
    
    if not query:
        bot.add_response("Please provide an IP address or hostname (e.g., !ip 8.8.8.8 or !ip google.com)")
        return
    
    try:
        # Try to resolve the hostname to an IP address
        try:
            ip_addresses = socket.getaddrinfo(query, None)
            # Get unique IPs (both IPv4 and IPv6)
            unique_ips = set()
            for addr_info in ip_addresses:
                family, socktype, proto, canonname, sockaddr = addr_info
                if family == socket.AF_INET:  # IPv4
                    unique_ips.add(sockaddr[0])
                elif family == socket.AF_INET6:  # IPv6
                    unique_ips.add(sockaddr[0])
            
            # If the query itself is an IP address, just use that
            try:
                ipaddress.ip_address(query)
                unique_ips = {query}
            except ValueError:
                pass
            
            if not unique_ips:
                bot.add_response(f"Could not resolve any IP addresses for: {query}")
                return
            
            # For each IP, get information
            for ip in unique_ips:
                ip_info = get_ip_info(ip)
                bot.add_response(ip_info)
                
        except socket.gaierror:
            bot.add_response(f"Could not resolve hostname: {query}")
            return

    except Exception as e:
        bot.logger.error(f"Error in IP module: {e}")
        bot.add_response(f"Error looking up IP information for {query}: {str(e)}")


def get_ip_info(ip):
    """Get information about an IP address"""
    try:
        # Parse the IP address
        ip_obj = ipaddress.ip_address(ip)
        
        # Determine IP version and type
        ip_version = f"IPv{ip_obj.version}"
        
        ip_type = []
        if ip_obj.is_private:
            ip_type.append("Private")
        if ip_obj.is_global:
            ip_type.append("Global")
        if ip_obj.is_multicast:
            ip_type.append("Multicast")
        if ip_obj.is_loopback:
            ip_type.append("Loopback")
        if ip_obj.is_link_local:
            ip_type.append("Link-local")
        if ip_obj.is_reserved:
            ip_type.append("Reserved")
        if ip_obj.is_unspecified:
            ip_type.append("Unspecified")
        
        ip_type_str = ", ".join(ip_type) if ip_type else "Unknown"
        
        # Get geolocation information for public IPs
        geo_info = ""
        if ip_obj.is_global and not ip_obj.is_private:
            try:
                response = requests.get(f"http://ip-api.com/json/{ip}?fields=country,regionName,city,isp,org,as", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    location_parts = []
                    if data.get("city"):
                        location_parts.append(data["city"])
                    if data.get("regionName"):
                        location_parts.append(data["regionName"])
                    if data.get("country"):
                        location_parts.append(data["country"])
                    
                    location = ", ".join(location_parts) if location_parts else "Unknown"
                    isp = data.get("isp", "Unknown")
                    org = data.get("org", "Unknown")
                    asn = data.get("as", "Unknown")
                    
                    geo_info = f" | Location: {location} | ISP: {isp} | Organization: {org} | {asn}"
            except Exception:
                # If geolocation fails, continue without it
                pass
        
        # Format the result
        result = f"IP: {ip} | Type: {ip_version}, {ip_type_str}{geo_info}"
        return result
        
    except Exception as e:
        return f"Error processing IP {ip}: {str(e)}"