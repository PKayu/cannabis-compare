#!/usr/bin/env python3
"""
Commit message validation
Checks for conventional commit format and Co-Authored-By format
"""
import re
import sys


def read_commit_msg(filepath):
    """Read commit message from file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def check_conventional_format(msg):
    """Check for conventional commit format (warning only)"""
    # Ignore comment lines
    lines = [l for l in msg.split('\n') if not l.startswith('#')]
    if not lines:
        return True

    first_line = lines[0].strip()

    # Conventional commit pattern
    pattern = r'^(feat|fix|docs|test|refactor|chore|perf|style|build|ci)(\(.+\))?: .+'

    if not re.match(pattern, first_line):
        print("WARNING: Commit doesn't follow conventional format")
        print("  Expected: feat|fix|docs|test|refactor|chore|perf|style: description")
        print(f"  Got: {first_line[:60]}...")
        print("  Allowed to proceed, but consider using conventional format")
        return False
    return True


def check_co_authored_by(msg):
    """Validate Co-Authored-By format if present"""
    if 'Co-Authored-By:' not in msg:
        return True

    pattern = r'Co-Authored-By: .+ <[^@]+@[^@]+\.[^@]+>'
    matches = re.findall(pattern, msg)

    # Count how many Co-Authored-By lines exist
    co_authored_count = msg.count('Co-Authored-By:')

    if len(matches) != co_authored_count:
        print("ERROR: Co-Authored-By format is incorrect")
        print("  Expected: Co-Authored-By: Name <email@example.com>")
        return False

    return True


def check_message_length(msg):
    """Check subject line length"""
    lines = msg.split('\n')
    if not lines:
        return True

    subject = lines[0].strip()
    if len(subject) > 72:
        print(f"WARNING: Subject line is {len(subject)} chars (recommended: < 72)")
        return False
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: commit-msg <commit_msg_file>")
        return 1

    commit_file = sys.argv[1]
    msg = read_commit_msg(commit_file)

    # Skip empty messages (git will handle)
    if not msg.strip():
        return 0

    # Run checks (warnings don't fail, errors do)
    errors = []

    if not check_co_authored_by(msg):
        errors.append("Co-Authored-By format error")

    check_conventional_format(msg)  # Warning only
    check_message_length(msg)  # Warning only

    if errors:
        print("\nCommit message validation failed:")
        for error in errors:
            print(f"  ERROR: {error}")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
