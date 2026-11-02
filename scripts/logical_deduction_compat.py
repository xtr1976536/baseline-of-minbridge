"""Surface-only CSP compatibility. Never selects a program or changes constraints."""
import re


def normalize_query_labels(program):
    """Normalize (A) -> A) only after the sole Query: heading.

    Multiple programs are returned unchanged for the author's parser to reject.
    No labels, variables, expressions or truth values are added or inferred.
    """
    if program.count('Query:') != 1:
        return program, 0
    prefix, query = program.split('Query:')
    query, count = re.subn(r'(?m)^(\s*)\(([A-Z])\)(?=\s)', r'\1\2)', query)
    return prefix + 'Query:' + query, count


def normalize_csp_layout(program):
    """Split inline headings; collapse repeated *inline* prefixes within one section.

    A repeated Domain or a backwards section is ambiguous and is not processed.
    Repeated empty headings are also rejected. No statement is dropped or reordered.
    """
    headings = ('Domain', 'Variables', 'Constraints', 'Query')
    lines = program.splitlines()
    found = []
    previous = -1
    for line in lines:
        match = re.match(r'^\s*(Domain|Variables|Constraints|Query):\s*(.*)$', line)
        if match:
            index = headings.index(match[1])
            if index < previous or (index == previous and (index == 0 or not match[2])):
                return program, 0
            if index == previous and not found[-1][1]:
                return program, 0
            found.append((index, match[2]))
            previous = index
    if {index for index, _ in found} != {0, 1, 2, 3}:
        return program, 0
    output, active, changes = [], None, 0
    for line in lines:
        match = re.match(r'^\s*(Domain|Variables|Constraints|Query):\s*(.*)$', line)
        if not match:
            output.append(line)
            continue
        if match[1] != active:
            output.append(match[1] + ':')
            active = match[1]
        else:
            changes += 1
        if match[2]:
            output.append(match[2])
            changes += 1
    return ('\n'.join(output), changes) if changes else (program, 0)


def normalize_csp_surface(program):
    layout, headings = normalize_csp_layout(program)
    normalized, labels = normalize_query_labels(layout)
    return normalized, {'heading_edits': headings, 'label_edits': labels}
