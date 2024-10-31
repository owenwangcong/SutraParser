import os

def ensure_directory(path):
    """Ensures that the specified directory exists. If not, it creates the directory."""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")
