from server.app import ServerApp
import os

try:
    _ = os.environ["UNIT_TESTS_IN_PROGRESS"]
except KeyError:
    app = ServerApp()
