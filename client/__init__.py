from client.app import ClientApp
import os

CHUNK_SIZE = 1024

try:
    _ = os.environ["UNIT_TESTS_IN_PROGRESS"]
    app = ClientApp(('localhost', 15152), start_interface=False)
except KeyError:
    app = ClientApp(('localhost', 15152), start_interface=True)

