import re

with open("/Users/aryanmahajan/Documents/Medcare.Ai/backend/static/index.html") as f:
    html = f.read()

start_idx = html.find('<script type="text/babel">')
end_idx = html.find('</script>', start_idx)
script = html[start_idx + len('<script type="text/babel">'):end_idx]

# Find all JSX tags
# A JSX tag is <tag ...> or </tag>
# We need to exclude self-closing tags like <img ... />, <input ... />, <br/>, <hr/>, <audio .../>, <canvas .../>, <i .../>
# And we need to exclude comparisons like x < y

# Regular expression to match tags
# <([a-zA-Z0-9_\-]+)([^>]*)/?> or </([a-zA-Z0-9_\-]+)>
tag_pattern = re.compile(r'</?([a-zA-Z0-9_\-]+)([^>]*)/?>')

stack = []
for line_num, line in enumerate(script.split('\n'), start=148):
    # Skip lines that are comments or strings (simplistic check)
    stripped = line.strip()
    if stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*'):
        continue
    
    # Find all matches in this line
    for match in tag_pattern.finditer(line):
        full_match = match.group(0)
        tag_name = match.group(1)
        
        # Skip standard HTML self-closing tags or self-closing JSX tags
        if full_match.endswith('/>') or tag_name.lower() in ['img', 'input', 'br', 'hr', 'meta', 'link']:
            continue
            
        # Skip tags inside quotes or js comments
        # For simplicity, if '<' is preceded by a quote on the same line, skip it
        left_side = line[:match.start()]
        if left_side.count('"') % 2 != 0 or left_side.count("'") % 2 != 0 or '`' in left_side:
            continue
            
        # Is it a closing tag?
        if full_match.startswith('</'):
            if not stack:
                print(f"[{line_num}] Extra closing tag: </{tag_name}> (no opening tag)")
            else:
                top_tag, top_line = stack.pop()
                if top_tag != tag_name:
                    print(f"[{line_num}] Mismatched tag: </{tag_name}> does not match <{top_tag}> from line {top_line}")
        else:
            # It's an opening tag
            stack.append((tag_name, line_num))

if stack:
    print(f"Unclosed tags left: {len(stack)}")
    for tag_name, line_num in stack:
        print(f"  Unclosed <{tag_name}> at line {line_num}")
else:
    print("All tags parsed are balanced!")
