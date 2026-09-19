import json
from mcp_server import get_context

# Replace this with the path to a script in your project that 
# you know extends another class or is used in a scene.
test_path = "res://Machines/Scripts/wafer_slicer.gd" 

try:
    result = get_context(test_path)
    print(json.dumps(result, indent=2))
except Exception as e:
    print(f"Error: {e}")