"""
Code Backup Utility
===================

Creates timestamped backups of critical code files before making changes.

Usage:
    python scripts/maintenance/backup_code.py --all
    python scripts/maintenance/backup_code.py --file ai_chatagent.py

Author: Socializer Development Team
Date: 2024-11-12
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
import argparse


def create_backup(files: list, backup_dir: str = None) -> str:
    """
    Create backup of specified files.
    
    Args:
        files: List of file paths to backup
        backup_dir: Optional custom backup directory
        
    Returns:
        str: Path to backup directory
        
    Example:
        >>> create_backup(['ai_chatagent.py'])
        'backups/code_20241112_072800'
    """
    # Create timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create backup directory
    if backup_dir is None:
        backup_dir = f"backups/code_{timestamp}"
    
    backup_path = Path(backup_dir)
    backup_path.mkdir(parents=True, exist_ok=True)
    
    # Backup each file
    backed_up = []
    for file in files:
        file_path = Path(file)
        if file_path.exists():
            dest = backup_path / file_path.name
            shutil.copy2(file_path, dest)
            backed_up.append(file_path.name)
            print(f"✅ Backed up: {file_path.name}")
        else:
            print(f"⚠️  File not found: {file}")
    
    print(f"\n📦 Backup created: {backup_path}")
    print(f"📊 Files backed up: {len(backed_up)}")
    
    return str(backup_path)


def backup_critical_files():
    """Backup all critical code files."""
    critical_files = [
        "ai_chatagent.py",
        "app/main.py",
        "datamanager/data_manager.py",
        "memory/secure_memory_manager.py",
        "memory/user_agent.py",
        "services/language_detector.py",
    ]
    
    return create_backup(critical_files)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Backup code files")
    parser.add_argument('--all', action='store_true', help='Backup all critical files')
    parser.add_argument('--file', type=str, help='Backup specific file')
    
    args = parser.parse_args()
    
    if args.all:
        backup_critical_files()
    elif args.file:
        create_backup([args.file])
    else:
        print("Error: Specify --all or --file")
        parser.print_help()


if __name__ == "__main__":
    main()
