from abc import abstractmethod


class AbstractProgressBar(object):
    def __init__(self):
        self.progress = 0

    def set(self, progress):
        """
        Set progress to a specific value and redraw.

        :param progress: Fraction of the bar to fill. Clamped to [0, 1].
        """
        self.progress = min(max(progress, 0.0), 1.0)

        # Restore cursor position and redraw
        self.redraw()

    def tick(self, amount):
        """
        Increment progress by the specified fraction and redraw.
        """
        self.set(self.progress + amount)
    
    @abstractmethod
    def redraw(self):
        pass

    @abstractmethod
    def cycle_animation(self):
        pass

    @abstractmethod
    def stop_cycle_animation(self):
        pass


class GuiProgressBar(AbstractProgressBar):
    def __init__(self, progressbar):
        super(GuiProgressBar, self).__init__()
        self.progressbar = progressbar

    def redraw(self):
        self.progressbar["value"] = self.progress * 100.0

    def cycle_animation(self):
        self.progressbar["mode"] = "indeterminate"
        self.progressbar.start()

    def stop_cycle_animation(self):
        self.progressbar.stop()
        self.progressbar["mode"] = "determinate"
        self.set(0)