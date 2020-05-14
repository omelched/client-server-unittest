from client.app import ClientApp
import os

CHUNK_SIZE = 1024

try:
    _ = os.environ["UNIT_TESTS_IN_PROGRESS"]
except KeyError:
    app = ClientApp(('localhost', 15152))

