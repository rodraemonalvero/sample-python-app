#!/usr/bin/env python3
"""
AI code review step for the CSE636 Week 2 lab.
Reads recently changed Python files and asks Claude for a code review.
"""
import os
import subprocess
import anthropic

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def get_changed_files():
    """Get Python files changed in the last commit."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
        capture_output=True,
        text=True
    )
    return [
        f for f in result.stdout.strip().split("\n")
        if f.endswith(".py")
    ]


def read_file(path):
    try:
        with open(path) as fh:
            return fh.read()
    except FileNotFoundError:
        return None


def review_code(filename, content):
    """Ask Claude to review a single file."""
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Please review the following Python file for correctness, "
                    f"style issues, and potential bugs. Be concise.\n\n"
                    f"Filename: {filename}\n\n"
                    f"```python\n{content}\n```"
                )
            }
        ]
    )
    return message.content[0].text


def main():
    changed = get_changed_files()

    if not changed:
        print("No Python files changed. Skipping AI review.")
        with open("ai_review_report.txt", "w") as fh:
            fh.write("No Python files changed in this commit.\n")
        return

    report_lines = ["# AI Code Review Report\n"]

    for filepath in changed:
        content = read_file(filepath)

        if content is None:
            continue

        print(f"Reviewing {filepath}...")
        review = review_code(filepath, content)
        report_lines.append(f"\n## {filepath}\n\n{review}\n")
        print(f"Review for {filepath}:\n{review}\n")

    with open("ai_review_report.txt", "w") as fh:
        fh.write("\n".join(report_lines))

    print("AI review complete. Report saved to ai_review_report.txt")


if __name__ == "__main__":
    main()