import subprocess
import sys
import os

def main():
    print("=" * 60)
    print("BuyWise - Smart Shopping Intelligence Platform")
    print("=" * 60)
    
    dashboard_path = os.path.join("src", "dashboard", "app.py")
    if os.path.exists(dashboard_path):
        subprocess.run([sys.executable, "-m", "streamlit", "run", dashboard_path])
    else:
        print("Error: Could not find the dashboard file.")

if __name__ == "__main__":
    main()