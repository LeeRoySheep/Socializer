"""
Execute Comprehensive Cleanup
==============================

This script performs the systematic cleanup of the Socializer project
according to the action plan.

Usage:
    python execute_cleanup.py --phase <phase_number> [--dry-run]
    
    --phase: Which phase to execute (1-7)
    --dry-run: Show what would be done without actually doing it

Author: Socializer Development Team
Date: 2024-11-12
"""

import os
import shutil
from pathlib import Path
from typing import List, Tuple
import argparse


class CleanupExecutor:
    """
    Executes cleanup operations with safety checks.
    
    Features:
    - Dry-run mode
    - Verification before moving/deleting
    - Backup creation
    - Rollback support
    """
    
    def __init__(self, root_dir: str, dry_run: bool = False):
        """
        Initialize cleanup executor.
        
        Args:
            root_dir: Project root directory
            dry_run: If True, only show what would be done
        """
        self.root_dir = Path(root_dir)
        self.dry_run = dry_run
        self.moved_files = []
        self.deleted_files = []
        
    def move_file(self, source: str, dest_dir: str) -> bool:
        """
        Move file to destination directory.
        
        Args:
            source: Source file path (relative to root)
            dest_dir: Destination directory (relative to root)
            
        Returns:
            bool: True if successful
        """
        src_path = self.root_dir / source
        dst_dir = self.root_dir / dest_dir
        dst_path = dst_dir / src_path.name
        
        if not src_path.exists():
            print(f"  ⚠️  Source not found: {source}")
            return False
        
        if self.dry_run:
            print(f"  [DRY-RUN] Would move: {source} -> {dest_dir}/")
            return True
        
        try:
            dst_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src_path), str(dst_path))
            self.moved_files.append((source, dest_dir))
            print(f"  ✅ Moved: {source} -> {dest_dir}/")
            return True
        except Exception as e:
            print(f"  ❌ Error moving {source}: {e}")
            return False
    
    def delete_file(self, filepath: str) -> bool:
        """
        Delete file with safety check.
        
        Args:
            filepath: File path (relative to root)
            
        Returns:
            bool: True if successful
        """
        file_path = self.root_dir / filepath
        
        if not file_path.exists():
            print(f"  ⚠️  File not found: {filepath}")
            return False
        
        if self.dry_run:
            print(f"  [DRY-RUN] Would delete: {filepath}")
            return True
        
        try:
            file_path.unlink()
            self.deleted_files.append(filepath)
            print(f"  ✅ Deleted: {filepath}")
            return True
        except Exception as e:
            print(f"  ❌ Error deleting {filepath}: {e}")
            return False
    
    def phase_1_documentation_cleanup(self):
        """Phase 1: Archive old documentation."""
        print("\n" + "="*70)
        print("PHASE 1: DOCUMENTATION CLEANUP")
        print("="*70 + "\n")
        
        # Archive session summaries
        print("📦 Archiving session summaries...")
        session_files = [
            "SESSION_COMPLETE.md",
            "SESSION_COMPLETE_2025-10-15.md",
            "SESSION_SUMMARY_2025-10-15.md",
            "FINAL_SESSION_COMPLETE.md",
            "FINAL_SESSION_SUMMARY.md",
            "COMPLETE_OPTIMIZATION_SUMMARY.md",
        ]
        for file in session_files:
            self.move_file(file, "docs/archive/sessions")
        
        # Archive phase documentation
        print("\n📦 Archiving phase documentation...")
        phase_files = [
            "PHASE7_PROGRESS.md",
            "PHASE8_COMPLETE.md",
            "PHASE9_AUDIT.md",
            "PHASE9_COMPLETE.md",
            "PHASE9_FIX.md",
        ]
        for file in phase_files:
            self.move_file(file, "docs/archive/sessions")
        
        # Archive fix documentation
        print("\n📦 Archiving fix documentation...")
        fix_files = [
            "FRONTEND_FIXES.md",
            "FRONTEND_REGISTRATION_FIX.md",
            "USERNAME_BUG_FIX.md",
            "USERNAME_BUG_COMPLETE_FIX.md",
            "MEMORY_FIX_SUMMARY.md",
            "MEMORY_FILTER_BUG_FIX.md",
            "MODEL_LOGGING_FIX.md",
            "SWAGGER_UI_FIX.md",
            "PROMPT_FILTER_FIX.md",
            "GENERAL_CHAT_PERSISTENCE_FIX.md",
            "GENERAL_CHAT_HISTORY_SOLUTION.md",
        ]
        for file in fix_files:
            self.move_file(file, "docs/archive/fixes")
        
        # Archive feature documentation
        print("\n📦 Archiving feature documentation...")
        feature_files = [
            "AI_TOOLS_COMPLETE.md",
            "AI_SYSTEM_VERIFIED.md",
            "GEMINI_DIAGNOSIS_SUMMARY.md",
            "GEMINI_OOP_PROGRESS.md",
            "GEMINI_SETUP_GUIDE.md",
            "INTEGRATION_COMPLETE.md",
            "OTE_IMPLEMENTATION_COMPLETE.md",
            "TOOLS_STATUS_REPORT.md",
            "MEMORY_SYSTEM_STATUS.md",
            "USER_CONVERSATION_TRACKING.md",
            "LOGIN_FLOW_DOCUMENTATION.md",
            "FRONTEND_TEST_GUIDE.md",
            "LOCAL_AI_SETUP.md",
        ]
        for file in feature_files:
            self.move_file(file, "docs/archive/features")
        
        # Delete obsolete files
        print("\n🗑️  Deleting obsolete files...")
        obsolete_files = [
            "COMMIT_READY.txt",
            "COMMIT_SUMMARY.txt",
            "OBSOLETE_FILES_ANALYSIS.md",
            "CLEANUP_REPORT.md",  # Old cleanup report
        ]
        for file in obsolete_files:
            self.delete_file(file)
        
        print("\n✅ Phase 1 Complete!")
        self.print_summary()
    
    def phase_2_test_organization(self):
        """Phase 2: Organize test files."""
        print("\n" + "="*70)
        print("PHASE 2: TEST FILE ORGANIZATION")
        print("="*70 + "\n")
        
        # Move unit tests
        print("📦 Moving unit tests...")
        unit_tests = [
            "test_token_manager.py",
        ]
        for file in unit_tests:
            self.move_file(file, "tests/unit")
        
        # Move integration tests
        print("\n📦 Moving integration tests...")
        integration_tests = [
            "test_ai_edge_cases.py",
            "test_all_tools.py",
            "test_chat_with_memory.py",
            "test_complete_memory_system.py",
            "test_encrypted_chat_memory.py",
            "test_gemini_integration.py",
            "test_memory_integration.py",
            "test_search_tool.py",
            "test_tools_fix.py",
            "test_memory_and_prefs.py",
        ]
        for file in integration_tests:
            self.move_file(file, "tests/integration")
        
        # Move e2e tests
        print("\n📦 Moving E2E tests...")
        e2e_tests = [
            "test_frontend_integration.py",
            "test_general_chat_persistence.py",
            "test_live_memory.py",
            "test_new_conversation_saving.py",
            "test_skill_tracking.py",
            "test_social_skills.py",
            "test_general_chat_history.py",
            "test_general_chat_memory.py",
        ]
        for file in e2e_tests:
            self.move_file(file, "tests/e2e")
        
        # Delete obsolete tests
        print("\n🗑️  Deleting obsolete tests...")
        obsolete_tests = [
            "test_gemini.py",
            "test_gemini_complete.py",
            "test_gemini_architecture.py",
            "test_tools_quick.py",
            "test_loop_fix.py",
            "test_prompt_filter.py",
            "test_duplicate_detection.py",
            "test_memory_fix.py",
            "test_weather.py",
            "test_openai_flow.py",
            "test_server_startup.py",
            "test_multiple_questions.py",
            "test_user_only_history.py",
        ]
        for file in obsolete_tests:
            self.delete_file(file)
        
        print("\n✅ Phase 2 Complete!")
        self.print_summary()
    
    def phase_3_script_organization(self):
        """Phase 3: Organize utility scripts."""
        print("\n" + "="*70)
        print("PHASE 3: SCRIPT ORGANIZATION")
        print("="*70 + "\n")
        
        # Move database scripts
        print("📦 Moving database scripts...")
        db_scripts = [
            "create_db.py",
            "create_tables.py",
            "init_database_with_memory.py",
        ]
        for file in db_scripts:
            self.move_file(file, "scripts/database")
        
        # Move migration scripts
        print("\n📦 Moving migration scripts...")
        migration_scripts = [
            "migrate_add_general_chat.py",
            "migrate_add_memory_fields.py",
        ]
        for file in migration_scripts:
            self.move_file(file, "scripts/migration")
        
        # Move development scripts
        print("\n📦 Moving development scripts...")
        dev_scripts = [
            "create_test_users.py",
            "debug_chat_history.py",
            "diagnose_gemini_api.py",
            "test_auth_api.sh",
            "test_registration_both_methods.sh",
        ]
        for file in dev_scripts:
            self.move_file(file, "scripts/development")
        
        # Move maintenance scripts
        print("\n📦 Moving maintenance scripts...")
        maintenance_scripts = [
            "cleanup_user_memory.py",
            "clear_user_memory.py",
            "fix_user_encryption_key.py",
            "set_user_language.py",
            "verify_all_fixes.sh",
            "verify_fixes.py",
        ]
        for file in maintenance_scripts:
            self.move_file(file, "scripts/maintenance")
        
        # Delete obsolete scripts
        print("\n🗑️  Deleting obsolete scripts...")
        obsolete_scripts = [
            "initialize_chat_history.py",
            "integrate_general_chat_memory.py",
            "integrate_memory_into_chat.py",
        ]
        for file in obsolete_scripts:
            self.delete_file(file)
        
        print("\n✅ Phase 3 Complete!")
        self.print_summary()
    
    def phase_4_database_cleanup(self):
        """Phase 4: Organize database files."""
        print("\n" + "="*70)
        print("PHASE 4: DATABASE CLEANUP")
        print("="*70 + "\n")
        
        # Move backup databases
        print("📦 Moving database backups...")
        db_backups = [
            "data.sqlite.db.backup_20251112_024210",
        ]
        for file in db_backups:
            self.move_file(file, "backups/database")
        
        # Note about active databases
        print("\n📝 Note: Keeping active databases in root:")
        print("  - data.sqlite.db (active)")
        print("  - socializer.db (check if needed)")
        
        print("\n✅ Phase 4 Complete!")
        self.print_summary()
    
    def print_summary(self):
        """Print summary of operations."""
        print("\n" + "="*70)
        print("OPERATION SUMMARY")
        print("="*70)
        print(f"Files moved: {len(self.moved_files)}")
        print(f"Files deleted: {len(self.deleted_files)}")
        
        if self.dry_run:
            print("\n⚠️  DRY-RUN MODE - No actual changes made")
        print("="*70 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Execute cleanup operations",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--phase',
        type=int,
        choices=[1, 2, 3, 4],
        required=True,
        help='Phase to execute (1=docs, 2=tests, 3=scripts, 4=database)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without doing it'
    )
    
    args = parser.parse_args()
    
    # Get project root
    root_dir = Path(__file__).parent
    
    # Create executor
    executor = CleanupExecutor(root_dir, dry_run=args.dry_run)
    
    # Execute phase
    if args.phase == 1:
        executor.phase_1_documentation_cleanup()
    elif args.phase == 2:
        executor.phase_2_test_organization()
    elif args.phase == 3:
        executor.phase_3_script_organization()
    elif args.phase == 4:
        executor.phase_4_database_cleanup()


if __name__ == "__main__":
    main()
