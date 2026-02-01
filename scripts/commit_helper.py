#!/usr/bin/env python3
"""
Commit Helper - Organize changes into logical commits

This script helps you:
1. See all uncommitted changes grouped by file/topic
2. Select which changes to commit together
3. Generate appropriate commit messages

Usage:
    python scripts/commit_helper.py
"""
import os
import subprocess
import sys
from collections import defaultdict


def run_git(cmd):
    """Run git command and return output"""
    try:
        result = subprocess.check_output(
            ['git'] + cmd,
            text=True,
            cwd=get_project_root()
        )
        return result.strip()
    except subprocess.CalledProcessError:
        return ""


def get_project_root():
    """Get project root directory"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_status():
    """Get git status of changed files"""
    output = run_git(['status', '--porcelain'])
    changes = []

    for line in output.split('\n'):
        if not line:
            continue
        status = line[:2]
        filepath = line[3:]
        changes.append((status, filepath))

    return changes


def categorize_file(filepath):
    """Categorize file by type/location"""
    if filepath.startswith('backend/'):
        if 'services/scrapers' in filepath:
            return 'scraper'
        elif 'routers/' in filepath:
            return 'api'
        elif 'models.py' in filepath or 'database.py' in filepath:
            return 'database'
        elif 'tests/' in filepath:
            return 'tests'
        else:
            return 'backend'
    elif filepath.startswith('frontend/'):
        if 'components/' in filepath:
            return 'frontend-components'
        elif 'app/' in filepath:
            return 'frontend-pages'
        elif 'lib/' in filepath:
            return 'frontend-lib'
        else:
            return 'frontend'
    elif filepath.startswith('scripts/'):
        return 'scripts'
    elif filepath.startswith('docs/'):
        return 'docs'
    elif filepath.endswith('.md'):
        return 'documentation'
    else:
        return 'other'


def get_diff_summary(filepath):
    """Get summary of changes for a file"""
    try:
        # Skip certain files
        if not os.path.exists(filepath) or filepath == 'nul':
            return ""

        output = run_git(['diff', filepath])
        if not output:
            return ""

        # Count added/removed lines (excluding diff headers)
        lines = [l for l in output.split('\n') if not l.startswith('+++')
                  and not l.startswith('---')
                  and not l.startswith('@@')
                  and not l.startswith('diff')]
        lines_added = len([l for l in lines if l.startswith('+')])
        lines_removed = len([l for l in lines if l.startswith('-')])

        if lines_added == 0 and lines_removed == 0:
            return ""

        return f"+{lines_added}/-{lines_removed}"
    except Exception:
        return ""


def suggest_commit_type(category, files):
    """Suggest commit type based on category and files"""
    # Check if it's mostly new files or modifications
    new_files = [f for s, f in files if s.startswith('??')]
    modified_files = [f for s, f in files if not s.startswith('??')]

    if category == 'scraper':
        return 'feat'
    elif category == 'api':
        return 'feat' if new_files else 'fix'
    elif category in ['frontend-components', 'frontend-pages']:
        return 'feat' if new_files else 'fix'
    elif category == 'tests':
        return 'test'
    elif category == 'documentation':
        return 'docs'
    elif category == 'scripts':
        return 'chore'
    else:
        return 'feat' if new_files else 'chore'


def generate_commit_message(category, files):
    """Generate a commit message for a group of files"""
    commit_type = suggest_commit_type(category, files)

    # Get scope and description
    scope_map = {
        'scraper': 'scrapers',
        'api': 'api',
        'database': 'database',
        'backend': 'backend',
        'frontend-components': 'frontend',
        'frontend-pages': 'frontend',
        'frontend-lib': 'frontend',
        'tests': 'tests',
        'scripts': 'scripts',
        'docs': 'docs',
        'documentation': 'docs'
    }

    scope = scope_map.get(category, category)

    # Generate description based on files
    filenames = [os.path.basename(f) for s, f in files]
    new_files = [f for s, f in files if s.startswith('??')]

    if category == 'scraper':
        if new_files:
            desc = f"add {len(new_files)} new scraper(s)"
        else:
            desc = f"update scraper(s)"
    elif category == 'api':
        desc = "update API endpoints"
    elif category == 'frontend-components':
        if new_files:
            desc = f"add {len(new_files)} new component(s)"
        else:
            desc = "update components"
    elif category == 'tests':
        desc = f"add/update tests"
    elif category == 'documentation':
        desc = "update documentation"
    elif category == 'scripts':
        desc = "update development scripts"
    else:
        if new_files:
            desc = f"add {len(new_files)} new file(s)"
        else:
            desc = f"update {scope}"

    return f"{commit_type}({scope}): {desc}"


def display_changes(groups):
    """Display grouped changes"""
    print("\n" + "=" * 70)
    print("UNCOMMITTED CHANGES")
    print("=" * 70)

    for category, files in groups.items():
        if not files:
            continue
        print(f"\n[{category.upper()}] ({len(files)} file{'s' if len(files) > 1 else ''})")
        print("-" * 70)
        for status, filepath in files:
            status_symbol = {
                'M ': 'modified',
                ' M': 'modified',
                'A ': 'staged',
                '??': 'untracked',
                'D ': 'deleted',
                'R ': 'renamed'
            }.get(status, status.strip())

            print(f"  [{status_symbol:10}] {filepath}")
            diff_summary = get_diff_summary(filepath)
            if diff_summary:
                print(f"              {diff_summary}")


def interactive_commit(groups):
    """Interactive commit session"""
    print("\n" + "=" * 70)
    print("INTERACTIVE COMMIT MODE")
    print("=" * 70)
    print("\nCommands:")
    print("  1-9       - Select a group to commit")
    print("  s         - Select specific files to commit")
    print("  a         - Commit all changes")
    print("  q         - Quit")
    print()

    # Flatten groups with indices
    indexed_groups = []
    for i, (category, files) in enumerate(groups.items(), 1):
        if files:
            indexed_groups.append((i, category, files))
            print(f"  [{i}] {category} ({len(files)} files)")

    print()

    while True:
        choice = input("Select option (or q to quit): ").strip().lower()

        if choice == 'q':
            print("Exiting without committing.")
            break
        elif choice == 'a':
            # Commit all
            commit_all(groups)
            break
        elif choice == 's':
            # Select specific files
            select_files(groups)
            break
        else:
            # Commit specific group
            try:
                idx = int(choice)
                for i, category, files in indexed_groups:
                    if i == idx:
                        commit_group(category, files)
                        break
                break
            except ValueError:
                print("Invalid option. Try again.")


def commit_group(category, files):
    """Commit a specific group of files"""
    print(f"\nCommitting {category} ({len(files)} files)...")

    # Stage files
    filepaths = [f for s, f in files]
    for filepath in filepaths:
        run_git(['add', filepath])

    # Generate commit message
    suggested_msg = generate_commit_message(category, files)
    print(f"\nSuggested commit message:")
    print(f"  {suggested_msg}")
    print()

    custom_msg = input("Enter custom message (or press Enter to use suggested): ").strip()
    final_msg = custom_msg if custom_msg else suggested_msg

    # Add Co-Authored-By
    add_coauthored = input("\nAdd Co-Authored-By header? (y/N): ").strip().lower()
    if add_coauthored == 'y':
        name = input("Your name: ").strip()
        email = input("Your email: ").strip()
        final_msg += f"\n\nCo-Authored-By: {name} <{email}>"

    # Commit
    result = run_git(['commit', '-m', final_msg])
    print(f"\n{result}")


def commit_all(groups):
    """Commit all changes, grouped by category"""
    print("\nCommitting all changes by group...")

    for category, files in groups.items():
        if not files:
            continue
        commit_group(category, files)


def select_files(groups):
    """Select specific files to commit"""
    print("\nSelect files to commit:")
    all_files = []

    for category, files in groups.items():
        if not files:
            continue
        print(f"\n[{category.upper()}]")
        for i, (status, filepath) in enumerate(files, len(all_files) + 1):
            print(f"  [{i}] {filepath}")
            all_files.append((category, status, filepath))

    print("\nEnter file numbers separated by commas (or 'a' for all):")
    choice = input("> ").strip()

    if choice.lower() == 'a':
        selected = all_files
    else:
        indices = [int(x.strip()) for x in choice.split(',')]
        selected = [all_files[i - 1] for i in indices if 0 < i <= len(all_files)]

    if selected:
        # Group selected files by category
        selected_groups = defaultdict(list)
        for category, status, filepath in selected:
            selected_groups[category].append((status, filepath))

        print(f"\nSelected {len(selected)} file(s) across {len(selected_groups)} group(s)")
        for category, files in selected_groups.items():
            print(f"  {category}: {len(files)} files")

        confirm = input("\nCommit these files? (Y/n): ").strip().lower()
        if confirm != 'n':
            for category, files in selected_groups.items():
                commit_group(category, files)


def main():
    """Main entry point"""
    os.chdir(get_project_root())

    # Check if we're in a git repo
    if not os.path.exists('.git'):
        print("Error: Not in a git repository")
        return 1

    # Get changes
    changes = get_status()

    if not changes:
        print("No uncommitted changes found.")
        return 0

    # Group by category
    groups = defaultdict(list)
    for status, filepath in changes:
        category = categorize_file(filepath)
        groups[category].append((status, filepath))

    # Display changes
    display_changes(groups)

    # Ask what to do
    print("\nWhat would you like to do?")
    print("  [c] Commit changes interactively")
    print("  [s] Show detailed diff")
    print("  [q] Quit")

    action = input("\nSelect option: ").strip().lower()

    if action == 'c':
        interactive_commit(groups)
    elif action == 's':
        # Show detailed diff
        for status, filepath in changes:
            print(f"\n{'=' * 70}")
            print(f"{filepath} ({status})")
            print('=' * 70)
            output = run_git(['diff', filepath])
            print(output[:500])  # Show first 500 chars
            if len(output) > 500:
                print("\n... (truncated)")
    else:
        print("Exiting.")

    return 0


if __name__ == '__main__':
    sys.exit(main())
