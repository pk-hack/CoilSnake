import queue
from tkinter import *
from tkinter.ttk import *

from abc import abstractmethod


class ThreadSafeConsole(Text):
    def __init__(self, master, **options):
        Text.__init__(self, master, **options)
        self["bg"] = "white"
        self["fg"] = "black"
        self.queue = queue.Queue()
        self.check_queue()

    def write(self, line):
        self.queue.put(line)

    def clear(self):
        self.queue.put(None)

    def flush(self):
        pass

    def check_queue(self):
        lines = []
        while True:
            try:
                line = self.queue.get(block=False)
            except queue.Empty:
                break
            else:
                if line is None:
                    # Delete everything in the textbox
                    lines = []
                    self.delete(1.0, END)
                else:
                    lines += str(line)

        # Batch up all of the lines in the queue, then insert them all at once into the textbox
        if len(lines) > 0:
            self.insert(END, ''.join(lines))
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
    COMMAND_SET, COMMAND_TICK, COMMAND_CYCLE_START, COMMAND_CYCLE_STOP = range(4)

    def __init__(self, master, **options):
        Progressbar.__init__(self, master, **options)
        self.queue = queue.Queue()
        self.check_queue()

    def set(self, percentage):
        self.queue.put((CoilSnakeGuiProgressBar.COMMAND_SET, percentage))

    def tick(self, percentage):
        self.queue.put((CoilSnakeGuiProgressBar.COMMAND_TICK, percentage))

    def clear(self):
        self.set(0)

    def cycle_animation_start(self):
        self.queue.put((CoilSnakeGuiProgressBar.COMMAND_CYCLE_START, None))

    def cycle_animation_stop(self):
        self.queue.put((CoilSnakeGuiProgressBar.COMMAND_CYCLE_STOP, None))

    def check_queue(self):
        while True:
            try:
                command, argument = self.queue.get(block=False)
            except queue.Empty:
                break
            else:
                if command == CoilSnakeGuiProgressBar.COMMAND_SET:
                    percentage = min(max(argument, 0.0), 1.0)
                    self["value"] = percentage * 100
                elif command == CoilSnakeGuiProgressBar.COMMAND_TICK:
                    self["value"] += argument * 100
                elif command == CoilSnakeGuiProgressBar.COMMAND_CYCLE_START:
                    self["mode"] = "indeterminate"
                    self.start()
                elif command == CoilSnakeGuiProgressBar.COMMAND_CYCLE_STOP:
                    self.stop()
                    self["mode"] = "determinate"
                    self["value"] = 0

        self.after(50, self.check_queue)