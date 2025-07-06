#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import subprocess
import logging

def config(wcb):
    return {
        'events': [],
        'commands': ['deploy'],
        'help': {
            'deploy': 'Deploy the bot. Usage: !deploy [push|pull|restart|all]'
        }
    }

def deploy(wcb, event):
    """
    Deploy the bot. This command can push changes to git, pull changes on the server,
    and restart the docker containers.
    
    Usage: !deploy [push|pull|restart|all]
    """
    # Check if the user has permission to deploy
    if not wcb.check_permission(event, 'deploy'):
        wcb.reply(event, "You don't have permission to deploy the bot.")
        return
    
    args = event.arguments[0].split()
    if len(args) < 2:
        wcb.reply(event, "Usage: !deploy [push|pull|restart|all]")
        return
    
    action = args[1].lower()
    
    if action == "push":
        result = git_push()
        wcb.reply(event, result)
    elif action == "pull":
        result = git_pull()
        wcb.reply(event, result)
    elif action == "restart":
        result = restart_containers()
        wcb.reply(event, result)
    elif action == "all":
        # Execute all actions in sequence
        push_result = git_push()
        wcb.reply(event, f"Push: {push_result}")
        
        pull_result = git_pull()
        wcb.reply(event, f"Pull: {pull_result}")
        
        restart_result = restart_containers()
        wcb.reply(event, f"Restart: {restart_result}")
    else:
        wcb.reply(event, f"Unknown action: {action}. Use push, pull, restart, or all.")

def git_push():
    """Push changes to the git repository."""
    try:
        # Add all changes
        subprocess.run(["git", "add", "."], check=True)
        
        # Commit changes with a timestamp
        commit_msg = "Auto-deploy: Update from bot"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        
        # Push to remote
        subprocess.run(["git", "push"], check=True)
        
        return "Successfully pushed changes to git repository."
    except subprocess.CalledProcessError as e:
        logging.error(f"Git push error: {str(e)}")
        return f"Error pushing to git: {str(e)}"

def git_pull():
    """Pull changes on the remote server via SSH."""
    try:
        # SSH into the server and pull changes
        cmd = "ssh root@vuurstorm.nl 'cd /opt/phreakbot && git pull'"
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        
        return f"Successfully pulled changes on server: {result.stdout.strip()}"
    except subprocess.CalledProcessError as e:
        logging.error(f"Git pull error: {str(e)}, {e.stderr}")
        return f"Error pulling on server: {e.stderr}"

def restart_containers():
    """Restart the Docker containers on the remote server."""
    try:
        # SSH into the server and restart containers
        cmd = "ssh root@vuurstorm.nl 'cd /opt/phreakbot && docker-compose down && docker-compose up -d'"
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        
        return f"Successfully restarted containers: {result.stdout.strip()}"
    except subprocess.CalledProcessError as e:
        logging.error(f"Restart error: {str(e)}, {e.stderr}")
        return f"Error restarting containers: {e.stderr}"