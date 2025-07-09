#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# RBL (Realtime Blackhole List) lookup module for PhreakBot

import re
import socket
import dns.resolver
import ipaddress


def config(bot):
    """Return module configuration"""
    return {
        "events": [],
        "commands": ["rbl", "blacklist"],
        "permissions": ["user"],
        "help": "Check if a domain's mail servers are listed in various RBLs (blacklists).\n"
        "Usage: !rbl <domain> - Check if a domain's mail servers are blacklisted\n"
        "       !rbl <IP> - Check if an IP address is blacklisted\n"
        "       !blacklist <domain or IP> - Alias for !rbl",
    }


def run(bot, event):
    """Handle RBL lookup command"""
    if event["command"] not in ["rbl", "blacklist"]:
        return

    query = event["command_args"].strip()

    if not query:
        bot.add_response("Please provide a domain or IP address to check (e.g., !rbl example.com or !rbl 192.0.2.1)")
        return

    try:
        # Check if the query is an IP address
        try:
            ip = ipaddress.ip_address(query)
            bot.add_response(f"Checking IP: {ip}")
            check_ip_in_rbls(bot, str(ip))
            return
        except ValueError:
            # Not an IP address, continue with domain processing
            pass

        # Check if the query is a domain
        domain_pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
        if re.match(domain_pattern, query):
            bot.add_response(f"Checking domain: {query}")
            
            # Look up MX records for the domain
            mx_records = get_mx_records(query)
            
            if mx_records:
                mx_summary = ", ".join([f"{mx_host}" for mx_host, _ in mx_records[:3]])
                if len(mx_records) > 3:
                    mx_summary += f", and {len(mx_records) - 3} more"
                bot.add_response(f"Mail servers: {mx_summary}")
                
                # Check only the first MX record to avoid too many lookups
                mx_host, _ = mx_records[0]
                try:
                    # Try to resolve the MX hostname to an IP
                    ips = get_host_ips(mx_host)
                    if ips:
                        ip = ips[0]  # Just use the first IP
                        bot.add_response(f"Primary mail server {mx_host} → {ip}")
                        check_ip_in_rbls(bot, ip)
                    else:
                        bot.add_response(f"Could not resolve mail server {mx_host}")
                except Exception as e:
                    bot.add_response(f"Error: {str(e)[:50]}")
            else:
                bot.add_response(f"No mail servers found for {query}, checking A record")
                
                # Fall back to A record if no MX records
                try:
                    ips = get_host_ips(query)
                    if ips:
                        ip = ips[0]  # Just use the first IP
                        bot.add_response(f"Domain {query} → {ip}")
                        check_ip_in_rbls(bot, ip)
                    else:
                        bot.add_response(f"Could not resolve {query}")
                except Exception as e:
                    bot.add_response(f"Error: {str(e)[:50]}")
            return
        else:
            bot.add_response(f"Invalid input: {query}. Please provide a valid domain or IP address.")
            return
    except Exception as e:
        bot.add_response(f"Error processing request: {str(e)[:50]}")
        return


def get_mx_records(domain):
    """Get MX records for a domain"""
    try:
        # Set a timeout for DNS queries
        resolver = dns.resolver.Resolver()
        resolver.timeout = 2.0
        resolver.lifetime = 2.0
        
        answers = resolver.resolve(domain, 'MX')
        mx_records = [(str(rdata.exchange).rstrip('.'), rdata.preference) for rdata in answers]
        return sorted(mx_records, key=lambda x: x[1])  # Sort by preference
    except Exception:
        return []


def get_host_ips(hostname):
    """Get all IP addresses for a hostname"""
    try:
        # Set a timeout for DNS queries
        resolver = dns.resolver.Resolver()
        resolver.timeout = 2.0
        resolver.lifetime = 2.0
        
        answers = resolver.resolve(hostname, 'A')
        return [str(rdata) for rdata in answers]
    except Exception:
        return []


def check_ip_in_rbls(bot, ip):
    """Check if an IP is listed in various RBLs"""
    # Reduced list of popular RBLs to avoid overwhelming the bot
    rbls = [
        "zen.spamhaus.org",
        "bl.spamcop.net",
        "xbl.spamhaus.org",
        "sbl.spamhaus.org"
    ]

    # Reverse the IP for RBL lookup
    reversed_ip = '.'.join(reversed(ip.split('.')))
    
    listed_on = []
    
    # Set a timeout for DNS queries
    resolver = dns.resolver.Resolver()
    resolver.timeout = 1.0
    resolver.lifetime = 1.0

    for rbl in rbls:
        lookup = f"{reversed_ip}.{rbl}"
        try:
            answers = resolver.resolve(lookup, 'A')
            if answers:
                listed_on.append(rbl)
        except dns.resolver.NXDOMAIN:
            pass  # Not listed
        except Exception:
            pass  # Ignore errors

    # Report results in a single message
    if listed_on:
        bot.add_response(f"⚠️ IP {ip} is LISTED on: {', '.join(listed_on)}")
    else:
        bot.add_response(f"✅ IP {ip} is NOT listed on any checked blacklists")