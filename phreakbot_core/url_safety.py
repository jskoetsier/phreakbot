#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
URL safety utilities for PhreakBot.

Prevents SSRF (Server-Side Request Forgery) attacks by blocking requests
to private IP addresses, loopback addresses, link-local addresses,
and cloud metadata endpoints.
"""

import socket

import netaddr


# IP ranges that should never be accessed by the bot
BLOCKED_NETWORKS = [
    # IPv4 loopback
    netaddr.IPNetwork("127.0.0.0/8"),
    # RFC 1918 private addresses
    netaddr.IPNetwork("10.0.0.0/8"),
    netaddr.IPNetwork("172.16.0.0/12"),
    netaddr.IPNetwork("192.168.0.0/16"),
    # Link-local
    netaddr.IPNetwork("169.254.0.0/16"),
    # Cloud provider metadata endpoints
    netaddr.IPNetwork("169.254.169.254/32"),
    # Carrier-grade NAT
    netaddr.IPNetwork("100.64.0.0/10"),
    # IPv6 loopback
    netaddr.IPNetwork("::1/128"),
    # IPv6 link-local
    netaddr.IPNetwork("fe80::/10"),
    # IPv6 unique local addresses
    netaddr.IPNetwork("fc00::/7"),
]


def is_url_safe(url, hostname=None):
    """Check if a URL points to a safe (non-private) IP address.

    Resolves the hostname to an IP and checks it against blocked networks.

    Args:
        url: The URL to check (used for hostname extraction if hostname not given).
        hostname: Optional hostname to check directly. If not provided,
                  extracted from the url.

    Returns:
        tuple: (is_safe: bool, reason: str) - is_safe is True if the URL
               passes all checks, False otherwise. reason explains why
               the URL was blocked.
    """
    if hostname is None:
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            hostname = parsed.hostname
            if not hostname:
                return False, "Could not extract hostname from URL"
        except Exception as e:
            return False, f"Invalid URL: {e}"

    # Resolve hostname to IP addresses (handle DNS resolution)
    try:
        # getaddrinfo returns all A/AAAA records
        addr_infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        return False, f"Could not resolve hostname: {hostname}"

    for addr_info in addr_infos:
        # addr_info[4] is (ip, port) for IPv4 or (ip, port, flow, scopeid) for IPv6
        ip_str = addr_info[4][0]
        try:
            ip = netaddr.IPAddress(ip_str)
        except (netaddr.AddrFormatError, ValueError):
            continue

        for network in BLOCKED_NETWORKS:
            if ip in network:
                return (
                    False,
                    f"Hostname {hostname} resolves to blocked IP {ip_str} "
                    f"(matches {network})",
                )

    return True, ""