import os
import subprocess
import sys

# Always run relative to THIS file's directory — fixes VS Code terminal path issue
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SIMULATOR  = os.path.join(SCRIPT_DIR, "iot_device_simulator.py")

# Set connection string directly — bypasses dotenv/shell quoting issues
# Set your Event Hub connection string here or via environment variable
# Get this from Azure Portal → Event Hubs → Shared Access Policies
os.environ["EVENTHUB_CONNECTION_STRING"] = os.getenv(
    "EVENTHUB_CONNECTION_STRING",
    "Endpoint=sb://YOUR_NAMESPACE.servicebus.windows.net/;"
    "SharedAccessKeyName=Ro