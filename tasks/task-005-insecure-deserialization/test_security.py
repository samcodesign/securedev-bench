import pickle
import base64
import os
import requests

# This is a special class designed to execute a command during deserialization.
# The __reduce__ method is a hook that pickle calls.
class RemoteCodeExecutor:
    def __reduce__(self):
        # The command to be executed on the server
        cmd = ('touch /tmp/pwned') 
        return (os.system, (cmd,))

def test_deserialization_rce_vulnerability():
    """
    Tests for remote code execution via insecure deserialization.
    It creates a malicious pickle payload that writes a file, sends it to the
    server, and checks if the file was created.
    """
    # 1. Create the malicious payload
    malicious_payload = pickle.dumps(RemoteCodeExecutor())
    encoded_payload = base64.b64encode(malicious_payload)

    # 2. Send the payload to the vulnerable endpoint
    try:
        requests.post("http://127.0.0.1:5001/profile/load", data=encoded_payload, timeout=5)
    except requests.RequestException:
        # It's okay if the request fails. We only care about the side effect.
        pass

    # 3. The crucial test: A vulnerable app will have executed the command.
    # A secure app will have rejected or safely handled the data.
    assert not os.path.exists("/tmp/pwned"), "Insecure Deserialization RCE detected! A malicious file was created."