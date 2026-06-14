import os, json, tempfile

SESSION_FILE = os.path.join(tempfile.gettempdir(), "cangauge_session.json")

def save_session(username):
    with open(SESSION_FILE, "w") as f:
        json.dump({"username": username}, f)

def clear_session():
    with open(SESSION_FILE, "w") as f:
        json.dump({}, f)

def load_session():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE) as f:
            return json.load(f)
    return None