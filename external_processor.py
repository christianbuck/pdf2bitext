import os
import subprocess
import threading


class ExternalProcessor(object):

    """ wraps an external script and does utf-8 conversions, is thread-safe """

    def __init__(self, cmd):
        self.cmd = cmd
        self.devnull = open(os.devnull, 'wb')
        if self.cmd is not None:
            self.proc = subprocess.Popen(cmd.split(), stdin=subprocess.PIPE,
                                         stdout=subprocess.PIPE,
                                         stderr=self.devnull)
            self._lock = threading.Lock()

    def process(self, line):
        if self.cmd is None or not line.strip():
            return line
        u_string = u"%s\n" % line
        u_string = u_string.encode("utf-8")
        result = u_string  # fallback: return input
        with self._lock:
            self.proc.stdin.write(u_string)
            self.proc.stdin.flush()
            result = self.proc.stdout.readline()
        return result.decode("utf-8").strip()
