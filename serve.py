#!/usr/bin/env python3

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import time


class WatchdogTimer(FileSystemEventHandler):

    proc = None
    cmd = ["python", "hbi/server.py"]

    def __init__(self):
        self.restart()
        self.last = 0

    def restart(self):
        print("Restarting...")
        if self.proc:
            self.proc.kill()
            self.proc.wait()
        self.proc = subprocess.Popen(self.cmd)

    def dispatch(self, event):
        now = time.time()
        if now > (self.last + 5):
            self.restart()
            self.last = now


w = WatchdogTimer()
o = Observer()
o.schedule(w, "hbi")
o.start()

try:
    while True:
        time.sleep(15000)
except KeyboardInterrupt:
    w.proc.kill()
    print("Killed")
