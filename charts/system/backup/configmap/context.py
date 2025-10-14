from datetime import datetime
import threading
import traceback

class Context:
    def __init__(self, node, namespace, deployment, no_dry_run):
        self.node = node
        self.namespace = namespace
        self.deployment = deployment
        self.no_dry_run = no_dry_run

    def __str__(self):
        ts = datetime.now().strftime("%H:%M:%S")
        name = threading.current_thread().name
        return f"[{ts}][{name}] {self.node}/{self.namespace}/{self.deployment}"

    def throw(self, msg):
        raise Exception(f"{ctx} {msg}")

    def info(self, msg):
        self.log("INFO", msg)

    def error(self, msg, error):
        self.log("ERROR", f"{msg}\n{traceback.format_exc()}")

    def log(self, level, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        name = threading.current_thread().name
        print(f"[{ts}][{level}][{name}] {self.node}/{self.namespace}/{self.deployment} {msg}")