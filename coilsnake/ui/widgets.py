import Queue
from Tkconstants import END
from Tkinter import Text
from abc import abstractmethod
from ttk import Progressbar


class ThreadSafeConsole(Text):
    def __init__(self, master, **options):
        Text.__init__(self, master, **options)
        self.queue = Queue.Queue()
        self.check_queue()

    def write(self, line):
        self.queue.put(line)

    def clear(self):
        self.queue.put(None)

    def flush(self):
        pass

    def check_queue(self):
        while True:
            try:
                line = self.queue.get(block=False)
            except Queue.Empty:
                break
            else:
                if line is None:
                    self.delete(1.0, END)
                else:
                    self.insert(END, str(line))
                self.see(END)

        self.after(50, self.check_queue)


class AbstractProgressBar(object):
    @abstractmethod
    def set(self, percentage):
        pass

    @abstractmethod
    def tick(self, percentage):
        pass

    @abstractmethod
    def cycle_animation_start(self):
        pass

    @abstractmethod
    def cycle_animation_stop(self):
        pass


class CoilSnakeGuiProgressBar(Progressbar):
    def __init__(self, master, **options):
        Progressbar.__init__(self, master, **options)

    def set(self, percentage):
        percentage = min(max(percentage, 0.0), 1.0)
        self["value"] = percentage * 100

    def tick(self, percentage):
        self["value"] += percentage * 100

    def clear(self):
        self.set(0)

    def cycle_animation_start(self):
        self["mode"] = "indeterminate"
        self.start()

    def cycle_animation_stop(self):
        self.stop()
        self["mode"] = "determinate"
        self.clear()