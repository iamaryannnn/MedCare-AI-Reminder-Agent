import re

with open("/Users/aryanmahajan/Documents/Medcare.Ai/backend/static/index.html") as f:
    html = f.read()

start_pattern = r'<script\s+type="text/babel">'
match = re.search(start_pattern, html)
if match:
    start_idx = match.end()
    end_idx = html.find('</script>', start_idx)
    code = html[start_idx:end_idx]
    
    with open("/Users/aryanmahajan/Documents/Medcare.Ai/scratch/script_only.jsx", "w") as out:
        out.write(code)
    print("Extracted JS/JSX to /Users/aryanmahajan/Documents/Medcare.Ai/scratch/script_only.jsx")
else:
    print("Could not find script block")
