import os
import json

root = r"c:\Projects\InboxRadar2"
search_terms = ["mock_mode", "simulation_template", "poll", "sandbox", "smtp", "dataset", "offline"]
results = []
for dirpath, dirnames, filenames in os.walk(root):
    if "node_modules" in dirnames: dirnames.remove("node_modules")
    if ".git" in dirnames: dirnames.remove(".git")
    if ".next" in dirnames: dirnames.remove(".next")
    if "venv" in dirnames: dirnames.remove("venv")
    if ".venv" in dirnames: dirnames.remove(".venv")
    for file in filenames:
        if file.endswith((".py", ".js", ".ts", ".tsx", ".jsx", ".env", ".md", ".json")):
            filepath = os.path.join(dirpath, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f):
                        if any(term.lower() in line.lower() for term in search_terms):
                            results.append({"file": filepath, "line": i+1, "content": line.strip()[:100]})
            except Exception:
                pass

with open(r"c:\Projects\InboxRadar2\search_results.json", 'w') as f:
    json.dump(results, f, indent=2)
print("done")
