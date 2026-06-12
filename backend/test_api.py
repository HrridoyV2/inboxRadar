import urllib.request
import json
import os
from dotenv import load_dotenv

load_dotenv(r"c:\Projects\InboxRadar2\backend\.env")

def test_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    endpoint = f"{url}/rest/v1/simulation_templates?select=id,subject,body"
    
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Profile": "public" # default schema
    }
    
    req = urllib.request.Request(endpoint, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print("Supabase returned length:", len(data))
            if len(data) > 0:
                print("First item:", data[0])
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_supabase()
