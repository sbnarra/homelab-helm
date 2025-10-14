from datetime import datetime
import threading
import traceback

class Context:
    def __init__(self, node, namespace, deployment):
        self.node = node
        self.namespace = namespace
        self.deployment = deployment

    def __str__(self):
        ts = datetime.now().strftime("%H:%M:%S")
        name = threading.current_thread().name
        return f"[{ts}][{name}] {self.node}/{self.namespace}/{self.deployment}"

    def throw(self, msg):
        raise Exception(f"{self} {msg}")

    def info(self, msg):
        self.log("INFO", msg)

    def error(self, msg, error):
        self.log("ERROR", f"{msg}\n{traceback.format_exc()}")

    def log(self, level, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        name = threading.current_thread().name
        print(f"[{ts}][{level}][{name}] {self.node}/{self.namespace}/{self.deployment} {msg}")