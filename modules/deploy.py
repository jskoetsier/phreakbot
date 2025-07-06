#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Deploy module for PhreakBot
#
# This module provides commands for deploying the bot to a remote server
# using git and Docker.

import os
import subprocess
import tempfile


def config(bot):
    """Return module configuration"""
    return {
        "events": [],
        "commands": ["deploy"],
        "permissions": ["owner", "admin"],
        "help": "Deploy the bot to a remote server.\n"
        "Usage: !deploy push - Push changes to git repo\n"
        "       !deploy pull - Pull changes on remote server\n"
        "       !deploy restart - Rebuild and restart Docker containers on remote server\n"
        "       !deploy status - Check deployment status\n"
        "       !deploy all - Perform all deployment steps (push, pull, restart)",
    }


def run(bot, event):
    """Handle deploy commands"""
    if not event["command_args"]:
        bot.add_response(
            "Please specify a deploy command: push, pull, restart, status, or all"
        )
        return

    args = event["command_args"].split()
    command = args[0].lower()

    # Only owner and admins can use deploy commands
    if not bot._is_owner(event["hostmask"]) and not (
        event["user_info"] and event["user_info"].get("is_admin")
    ):
        bot.add_response("Only the bot owner and admins can use deploy commands.")
        return

    if command == "push":
        _git_push(bot, event)
    elif command == "pull":
        _git_pull(bot, event)
    elif command == "restart":
        _docker_restart(bot, event)
    elif command == "status":
        _deployment_status(bot, event)
    elif command == "all":
        _deploy_all(bot, event)
    else:
        bot.add_response(
            "Unknown deploy command. Use: push, pull, restart, status, or all"
        )


def _git_push(bot, event):
    """Push changes to git repo"""
    bot.add_response("Pushing changes to git repo...")

    try:
        # Get current directory
        current_dir = os.getcwd()

        # Run git status to check for changes
        status_output = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=current_dir,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )

        if status_output.strip():
            # There are changes to commit
            bot.add_response("Changes detected, committing...")

            # Add all changes
            subprocess.check_output(
                ["git", "add", "."], cwd=current_dir, stderr=subprocess.STDOUT
            )

            # Commit changes
            commit_message = f"Auto-commit by {event['nick']} via deploy command"
            subprocess.check_output(
                ["git", "commit", "-m", commit_message],
                cwd=current_dir,
                stderr=subprocess.STDOUT,
            )

            bot.add_response("Changes committed successfully.")
        else:
            bot.add_response("No changes to commit.")

        # Push changes
        push_output = subprocess.check_output(
            ["git", "push"],
            cwd=current_dir,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )

        bot.add_response("Changes pushed to git repo successfully.")

    except subprocess.CalledProcessError as e:
        bot.add_response(f"Error pushing changes: {e.output}")
    except Exception as e:
        bot.add_response(f"Error pushing changes: {str(e)}")


def _git_pull(bot, event):
    """Pull changes on remote server"""
    bot.add_response("Pulling changes on remote server...")

    try:
        # Get SSH command from config or use default
        ssh_command = bot.config.get("remote_ssh_command", "")

        if not ssh_command:
            bot.add_response(
                "Remote SSH command not configured. Please set 'remote_ssh_command' in config."
            )
            return

        # Get remote directory from config or use default
        remote_dir = bot.config.get("remote_directory", "/opt/phreakbot")

        # Create SSH command to pull changes
        command = f"{ssh_command} 'cd {remote_dir} && git pull'"

        # Execute command
        output = subprocess.check_output(
            command, shell=True, stderr=subprocess.STDOUT, universal_newlines=True
        )

        bot.add_response(f"Pull result: {output.strip()}")

    except subprocess.CalledProcessError as e:
        bot.add_response(f"Error pulling changes: {e.output}")
    except Exception as e:
        bot.add_response(f"Error pulling changes: {str(e)}")


def _docker_restart(bot, event):
    """Rebuild and restart Docker containers on remote server"""
    bot.add_response("Rebuilding and restarting Docker containers on remote server...")

    try:
        # Get SSH command from config or use default
        ssh_command = bot.config.get("remote_ssh_command", "")

        if not ssh_command:
            bot.add_response(
                "Remote SSH command not configured. Please set 'remote_ssh_command' in config."
            )
            return

        # Get remote directory from config or use default
        remote_dir = bot.config.get("remote_directory", "/opt/phreakbot")

        # Create SSH command to rebuild and restart containers
        command = f"{ssh_command} 'cd {remote_dir} && docker-compose down && docker-compose build && docker-compose up -d'"

        # Execute command
        output = subprocess.check_output(
            command, shell=True, stderr=subprocess.STDOUT, universal_newlines=True
        )

        bot.add_response("Docker containers rebuilt and restarted successfully.")

    except subprocess.CalledProcessError as e:
        bot.add_response(f"Error restarting containers: {e.output}")
    except Exception as e:
        bot.add_response(f"Error restarting containers: {str(e)}")


def _deployment_status(bot, event):
    """Check deployment status"""
    bot.add_response("Checking deployment status...")

    try:
        # Get SSH command from config or use default
        ssh_command = bot.config.get("remote_ssh_command", "")

        if not ssh_command:
            bot.add_response(
                "Remote SSH command not configured. Please set 'remote_ssh_command' in config."
            )
            return

        # Get remote directory from config or use default
        remote_dir = bot.config.get("remote_directory", "/opt/phreakbot")

        # Create SSH command to check status
        command = f"{ssh_command} 'cd {remote_dir} && git status && docker-compose ps'"

        # Execute command
        output = subprocess.check_output(
            command, shell=True, stderr=subprocess.STDOUT, universal_newlines=True
        )

        # Create a temporary file to store the output
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp:
            temp.write(output)
            temp_path = temp.name

        # Send the first few lines of output
        lines = output.strip().split("\n")
        summary = "\n".join(lines[:5])
        if len(lines) > 5:
            summary += f"\n... and {len(lines) - 5} more lines"

        bot.add_response(f"Deployment status:\n{summary}")
        bot.add_response(f"Full output saved to temporary file: {temp_path}")

    except subprocess.CalledProcessError as e:
        bot.add_response(f"Error checking status: {e.output}")
    except Exception as e:
        bot.add_response(f"Error checking status: {str(e)}")


def _deploy_all(bot, event):
    """Perform all deployment steps"""
    bot.add_response("Starting full deployment process...")

    # Push changes
    _git_push(bot, event)

    # Pull changes
    _git_pull(bot, event)

    # Restart containers
    _docker_restart(bot, event)

    bot.add_response("Full deployment completed.")
