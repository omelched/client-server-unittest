from server.app import ServerApp
import os

try:
    _ = os.environ["UNIT_TESTS_IN_PROGRESS"]
    app = ServerApp(start_interface=False)
except KeyError:
    app = ServerApp(start_interface=True)
