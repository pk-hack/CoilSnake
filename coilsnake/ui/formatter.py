from logging import Formatter, ERROR, DEBUG, INFO, WARN


class CoilSnakeFormatter(Formatter):
    FORMATS = {ERROR: "ERROR: %(msg)s",
               DEBUG: "- %(msg)s",
               INFO: "%(msg)s",
               WARN: "! %(msg)s"}

    def format(self, record):
        self._fmt = self.FORMATS.get(record.levelno, self.FORMATS[INFO])
        return super(CoilSnakeFormatter, self).format(record)