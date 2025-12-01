import json
import re

def extract_fd_data(html_content):
    # Find the start of the variable assignment
    # Pattern: initialState={
    start_pattern = r'initialState\s*=\s*\{'
    match = re.search(start_pattern, html_content)
    
    if not match:
        print("Could not find 'initialState ='")
        return None
    
    start_index = match.end() - 1 # Include the opening brace
    
    # Brace counting logic
    brace_count = 0
    json_str = ""
    
    for i in range(start_index, len(html_content)):
        char = html_content[i]
        json_str += char
        
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            
        if brace_count == 0:
            break
            
    try:
        # We can't use json.loads because keys aren't quoted.
        # But we can try to fix it or just print a snippet.
        # Since we are in python, we can't easily eval JS.
        # BUT, for the purpose of "proving value", we can just look at the string.
        
        print("Success! Extracted JS Object String.")
        print(f"Length: {len(json_str)} bytes")
        print(f"Snippet: {json_str[:200]}...")
        
        # Save to file for inspection
        with open('fanduel_extracted_debug.txt', 'w') as out:
            out.write(json_str)
            
        return json_str
    except Exception as e:
        print(f"Error: {e}")
        return None

# Load the raw HTML file
try:
    with open('fanduel_stealth.json', 'r') as f:
        file_data = json.load(f)
        raw_html = file_data['raw_html']
        print(f"Loaded raw HTML ({len(raw_html)} bytes)")
        extract_fd_data(raw_html)
except Exception as e:
    print(f"Error: {e}")
