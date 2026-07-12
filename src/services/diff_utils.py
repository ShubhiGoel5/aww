"""
Diff utility for generating inline document comparisons.
Used by the legal agent to show edits in a VSCode-like diff view.
"""
import difflib
from typing import Dict, List, Tuple


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
            diff_lines.append({
                'type': 'add',
                'content': line[2:]
            })
            additions += 1
        elif line.startswith('- '):
            diff_lines.append({
                'type': 'del',
                'content': line[2:]
            })
            deletions += 1
        elif line.startswith('  '):
            diff_lines.append({
                'type': 'unchanged',
                'content': line[2:]
            })
        # Ignore lines starting with '?'
    
    # Generate HTML
    diff_html = _generate_html(diff_lines)
    
    changes_count = additions + deletions
    
    # Generate summary
    summary = []
    if additions > 0:
        summary.append(f"+{additions} dòng thêm")
    if deletions > 0:
        summary.append(f"-{deletions} dòng xóa")
    
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
    
    # Limit consecutive unchanged lines to avoid overwhelming display
    max_context = 3  # Show 3 lines of context around changes
    
    for i, line in enumerate(diff_lines):
        line_type = line['type']
        content = line['content']
        
        # Escape HTML
        content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        if line_type == 'add':
            html_parts.append(f'<div class="diff-line diff-add">{content}</div>')
        elif line_type == 'del':
            html_parts.append(f'<div class="diff-line diff-del">{content}</div>')
        else:
            # Check if we should show this unchanged line (context around changes)
            show = False
            
            # Show if near a change
            for j in range(max(0, i - max_context), min(len(diff_lines), i + max_context + 1)):
                if diff_lines[j]['type'] in ['add', 'del']:
                    show = True
                    break
            
            if show:
                html_parts.append(f'<div class="diff-line diff-unchanged">{content}</div>')
            elif i > 0 and diff_lines[i-1]['type'] == 'unchanged' and not any(
                diff_lines[j]['type'] in ['add', 'del'] 
                for j in range(max(0, i - max_context - 1), i)
            ):
                # This is part of a long unchanged section, show ellipsis once
                html_parts.append('<div class="diff-line diff-ellipsis">...</div>')
    
    return '\n'.join(html_parts)


def generate_side_by_side_diff(original: str, edited: str) -> Dict:
    """
    Generate side-by-side diff (not used in mobile view, but available).
    
    Returns similar structure to generate_inline_diff but with left/right columns.
    """
    original_lines = original.splitlines()
    edited_lines = edited.splitlines()
    
    # Use unified diff for side-by-side
    diff = difflib.unified_diff(
        original_lines, 
        edited_lines, 
        lineterm='',
        n=1000  # Show all context
    )
    
    left_lines = []
    right_lines = []
    
    for line in diff:
        if line.startswith('---') or line.startswith('+++') or line.startswith('@@'):
            continue
        elif line.startswith('-'):
            left_lines.append({'type': 'del', 'content': line[1:]})
            right_lines.append({'type': 'empty', 'content': ''})
        elif line.startswith('+'):
            left_lines.append({'type': 'empty', 'content': ''})
            right_lines.append({'type': 'add', 'content': line[1:]})
        else:
            left_lines.append({'type': 'unchanged', 'content': line})
            right_lines.append({'type': 'unchanged', 'content': line})
    
    return {
        'left': left_lines,
        'right': right_lines,
        'changes_count': sum(1 for l in left_lines if l['type'] == 'del') + sum(1 for r in right_lines if r['type'] == 'add')
    }
