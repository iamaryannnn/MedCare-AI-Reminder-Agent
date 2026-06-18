with open("/Users/aryanmahajan/Documents/Medcare.Ai/backend/static/index.html") as f:
    html = f.read()

start = html.find('<script type="text/babel">')
end = html.find('</script>', start)
script = html[start + len('<script type="text/babel">'):end]

stack = []
pairs = {')': '(', '}': '{', ']': '['}

for idx, char in enumerate(script):
    if char in '({[':
        stack.append((char, idx))
    elif char in ')}]':
        if not stack:
            print(f"Extra closing character '{char}' at index {idx}")
        else:
            top_char, top_idx = stack.pop()
            if top_char != pairs[char]:
                print(f"Mismatch: '{char}' at index {idx} does not match '{top_char}' from index {top_idx}")

if stack:
    print(f"Unbalanced characters left on stack: {len(stack)}")
    for char, idx in stack:
        # Get line number and snippet
        line_num = script[:idx].count("\n") + 148
        line_content = script.split("\n")[line_num - 148]
        print(f"Unclosed '{char}' at line {line_num}: {line_content.strip()}")
else:
    print("All brackets, parentheses, and braces are balanced!")
