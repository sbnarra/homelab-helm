from lib import log

class Context:
    def __init__(self, node, namespace="", deployment=""):
        self.node = node
        self.namespace = namespace
        self.deployment = deployment

    def __str__(self):
        return self.id()
    
    def id(self):
        return "/".join(filter(None, [self.node, self.namespace, self.deployment]))

    def throw(self, msg):
        raise Exception(f"{self} {msg}")

    def trace(self, msg):
        log.trace(self._log_msg(msg))

    def debug(self, msg):
        log.debug(self._log_msg(msg))

    def info(self, msg):
        log.info(self._log_msg(msg))

    def warn(self, msg, error=None):
        log.warn(self._log_msg(msg), error)

    def error(self, msg, error=None):
        log.error(self._log_msg(msg), error)

    def _log_msg(self, msg):
        return f"{self.id()}: {msg}"