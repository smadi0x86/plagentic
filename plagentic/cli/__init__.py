"""
Plagentic CLI - Command-Line Interface

This module provides the command-line interface for Plagentic,
allowing users to execute infrastructure provisioning tasks through terminal commands.

Usage:
    plagentic run team-name -t "your infrastructure task"
    plagentic list teams
    plagentic --help
"""

from plagentic.cli.cli import app

__all__ = ['app']
