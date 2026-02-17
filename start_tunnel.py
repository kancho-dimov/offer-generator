"""Start Streamlit with an ngrok tunnel for iPhone access."""

import subprocess
import sys
import time
from pathlib import Path

def main():
    # Start Streamlit in background
    app_path = Path(__file__).parent / "app.py"
    streamlit_exe = Path(__file__).parent / "venv" / "Scripts" / "streamlit.exe"

    proc = subprocess.Popen(
        [str(streamlit_exe), "run", str(app_path), "--server.headless", "true"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    # Wait for Streamlit to start
    print("Waiting for Streamlit to start...")
    time.sleep(5)

    # Start ngrok tunnel with basic auth protection
    try:
        from pyngrok import ngrok
        import os
        from dotenv import load_dotenv
        load_dotenv()

        # Require NGROK_AUTH env var for basic auth (user:password)
        ngrok_basic_auth = os.getenv("NGROK_BASIC_AUTH", "")
        if not ngrok_basic_auth:
            print("WARNING: No NGROK_BASIC_AUTH set in .env!")
            print("  Add NGROK_BASIC_AUTH=user:password to .env for security.")
            print("  Anyone with the URL can access the app without auth.")
            print()

        connect_kwargs = {"addr": 8501}
        if ngrok_basic_auth:
            connect_kwargs["auth"] = ngrok_basic_auth
        tunnel = ngrok.connect(**connect_kwargs)
        print()
        print("=" * 50)
        print(f"  iPhone URL: {tunnel.public_url}")
        print("=" * 50)
        print()
        print(f"  Local URL:  http://localhost:8501")
        print()
        print("  Open the iPhone URL in Safari.")
        print("  Press Ctrl+C to stop.")
        print()

        # Keep running
        proc.wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
        ngrok.kill()
        proc.terminate()
    except Exception as e:
        print(f"\nngrok error: {e}")
        print("Tip: Sign up at https://ngrok.com (free) and run:")
        print("  venv\\Scripts\\ngrok.exe config add-authtoken YOUR_TOKEN")
        print()
        print(f"Streamlit is still running at http://localhost:8501")
        proc.wait()


if __name__ == "__main__":
    main()
