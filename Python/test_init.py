import sys
sys.stdout.reconfigure(encoding='utf-8', newline='\n')
import traceback

print("Starting native script test...")
try:
    from api_server import get_engines
    print("Calling get_engines()...")
    engines = get_engines()
    print("Got engines successfully!")
except Exception as e:
    print(f"Exception: {e}")
    traceback.print_exc()
