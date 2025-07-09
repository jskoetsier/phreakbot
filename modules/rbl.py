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

    # Check if the query is an IP address
    try:
        ip = ipaddress.ip_address(query)
        check_ip_in_rbls(bot, str(ip))
        return
    except ValueError:
        # Not an IP address, continue with domain processing
        pass

    # Check if the query is a domain
    domain_pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    if re.match(domain_pattern, query):
        # Look up MX records for the domain
        mx_records = get_mx_records(query)
        
        if mx_records:
            bot.add_response(f"Found {len(mx_records)} mail servers for domain {query}:")
            for i, (mx_host, mx_pref) in enumerate(mx_records):
                bot.add_response(f"  {i+1}. {mx_host} (priority: {mx_pref})")
                
            # Check each MX record
            for mx_host, _ in mx_records:
                try:
                    # Try to resolve the MX hostname to an IP
                    ips = get_host_ips(mx_host)
                    if ips:
                        bot.add_response(f"\nChecking mail server: {mx_host}")
                        for ip in ips:
                            bot.add_response(f"Mail server {mx_host} resolves to IP: {ip}")
                            check_ip_in_rbls(bot, ip)
                    else:
                        bot.add_response(f"Could not resolve mail server {mx_host} to an IP address.")
                except Exception as e:
                    bot.add_response(f"Error checking mail server {mx_host}: {str(e)}")
        else:
            bot.add_response(f"No mail servers (MX records) found for domain {query}.")
            bot.add_response(f"Falling back to A record check...")
            
            # Fall back to A record if no MX records
            try:
                ips = get_host_ips(query)
                if ips:
                    for ip in ips:
                        bot.add_response(f"Domain {query} resolves to IP: {ip}")
                        check_ip_in_rbls(bot, ip)
                else:
                    bot.add_response(f"Could not resolve domain {query} to an IP address.")
            except Exception as e:
                bot.add_response(f"Error resolving domain {query}: {str(e)}")
        return
    else:
        bot.add_response(f"Invalid input: {query}. Please provide a valid domain or IP address.")
        return


def get_mx_records(domain):
    """Get MX records for a domain"""
    try:
        answers = dns.resolver.resolve(domain, 'MX')
        mx_records = [(str(rdata.exchange).rstrip('.'), rdata.preference) for rdata in answers]
        return sorted(mx_records, key=lambda x: x[1])  # Sort by preference
    except Exception:
        return []


def get_host_ips(hostname):
    """Get all IP addresses for a hostname"""
    try:
        answers = dns.resolver.resolve(hostname, 'A')
        return [str(rdata) for rdata in answers]
    except Exception:
        return []


def check_ip_in_rbls(bot, ip):
    """Check if an IP is listed in various RBLs"""
    # List of popular RBLs
    rbls = [
        "zen.spamhaus.org",
        "bl.spamcop.net",
        "b.barracudacentral.org",
        "dnsbl.sorbs.net",
        "spam.dnsbl.sorbs.net",
        "xbl.spamhaus.org",
        "pbl.spamhaus.org",
        "sbl.spamhaus.org",
        "dnsbl-1.uceprotect.net",
        "psbl.surriel.com",
        "bl.mailspike.net",
        "cbl.abuseat.org"
    ]

    # Reverse the IP for RBL lookup
    reversed_ip = '.'.join(reversed(ip.split('.')))
    
    listed_on = []
    not_listed_on = []
    errors = []

    for rbl in rbls:
        lookup = f"{reversed_ip}.{rbl}"
        try:
            answers = dns.resolver.resolve(lookup, 'A')
            if answers:
                listed_on.append(rbl)
        except dns.resolver.NXDOMAIN:
            not_listed_on.append(rbl)
        except Exception as e:
            errors.append(f"{rbl}: {str(e)}")

    # Report results
    if listed_on:
        bot.add_response(f"⚠️ IP {ip} is LISTED on {len(listed_on)} blacklists:")
        for rbl in listed_on:
            bot.add_response(f"  • {rbl}")
    else:
        bot.add_response(f"✅ IP {ip} is NOT listed on any checked blacklists.")
    
    if errors:
        bot.add_response(f"Errors occurred while checking {len(errors)} blacklists:")
        for error in errors[:3]:  # Limit to first 3 errors to avoid flooding
            bot.add_response(f"  • {error}")
        if len(errors) > 3:
            bot.add_response(f"  • ... and {len(errors) - 3} more errors")