from lib import env
from enum import Enum, auto
from datetime import datetime
import threading
import traceback

class Level(Enum):
  OFF = auto()
  TRACE = auto()
  DEBUG = auto()
  INFO = auto()
  WARN = auto()
  ERROR = auto()

_print_lock = threading.Lock()

def _print(level, msg, error=None):
  if level.value < env.log_level.value: return
  ts = datetime.now().strftime("%H:%M:%S")
  level = f"[{level.name}]".ljust(7)
  with _print_lock:
    print(f"{ts} {level}{msg}", flush=True)

def trace(msg):
  _print(Level.TRACE, msg)

def debug(msg):
  _print(Level.DEBUG, msg)

def info(msg):
  _print(Level.INFO, msg)

def warn(msg, error=None):
  _print(Level.WARN, msg, error)

def error(msg, error=None):
  if error:
    _print(Level.ERROR, f"{msg}\n{traceback.format_exc()}", error)
  else:
    _print(Level.ERROR, msg)