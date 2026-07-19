"""
Diff utility for generating inline document comparisons.
Used by the legal agent to show edits in a VSCode-like diff view.
"""
import difflib
from typing import Dict, List


def generate_inline_diff(original: str, edited: str) -> Dict:
    """
    Generate inline diff with HTML markup for display in chat.

    Args:
        original: Original document text
        edited: Edited document text

    Returns:
        Dict with:
        - diff_html: HTML formatted diff
        - diff_lines: List of diff line objects
        - additions: Number of lines added
        - deletions: Number of lines deleted
        - changes_count: Total changes
        - summary: Human readable summary
    """
    # Split into lines
    original_lines = original.splitlines()
    edited_lines = edited.splitlines()

    # Generate diff using difflib
    differ = difflib.Differ()
    diff = list(differ.compare(original_lines, edited_lines))

    # Parse diff into structured format
    diff_lines = []
    additions = 0
    deletions = 0

    for line in diff:
        if line.startswith('+ '):
            diff_lines.append({'type': 'add', 'content': line[2:]})
            additions += 1
        elif line.startswith('- '):
            diff_lines.append({'type': 'del', 'content': line[2:]})
            deletions += 1
        elif line.startswith('  '):
            diff_lines.append({'type': 'unchanged', 'content': line[2:]})
        # Ignore lines starting with '?'

    # Generate HTML
    diff_html = _generate_html(diff_lines)

    changes_count = additions + deletions

    # Generate summary
    summary = []
    if additions > 0:
        summary.append(f"+{additions} lines added")
    if deletions > 0:
        summary.append(f"-{deletions} lines deleted")

    summary_text = ", ".join(summary) if summary else "No changes"

    return {
        'diff_html': diff_html,
        'diff_lines': diff_lines,
        'additions': additions,
        'deletions': deletions,
        'changes_count': changes_count,
        'summary': summary_text
    }


def _generate_html(diff_lines: List[Dict]) -> str:
    """Generate HTML markup for diff lines"""
    html_parts = []

    # Show 3 lines of context around each change
    max_context = 3
    # Track whether we already emitted an ellipsis for the current unchanged block
    ellipsis_emitted = False

    for i, line in enumerate(diff_lines):
        line_type = line['type']
        content = line['content']

        # Escape HTML
        content = (
            content
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
        )

        if line_type == 'add':
            html_parts.append(f'<div class="diff-line diff-add">{content}</div>')
            ellipsis_emitted = False
        elif line_type == 'del':
            html_parts.append(f'<div class="diff-line diff-del">{content}</div>')
            ellipsis_emitted = False
        else:
            # Check if this unchanged line is close enough to a change to show as context
            show = any(
                diff_lines[j]['type'] in ('add', 'del')
                for j in range(max(0, i - max_context), min(len(diff_lines), i + max_context + 1))
            )

            if show:
                html_parts.append(f'<div class="diff-line diff-unchanged">{content}</div>')
                ellipsis_emitted = False
            elif not ellipsis_emitted:
                # Emit a single ellipsis to represent the skipped unchanged block
                html_parts.append('<div class="diff-line diff-ellipsis">...</div>')
                ellipsis_emitted = True
            # else: already emitted ellipsis for this block — skip

    return '\n'.join(html_parts)

