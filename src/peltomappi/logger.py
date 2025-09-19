import logging

LOGGER = logging.getLogger("peltomappi")
LOGGER.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)


class PeltomappiFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    fmt = "%(asctime)s %(levelname)-4s [%(filename)s:%(lineno)d] %(message)s"
    datefmt = "%Y-%m-%dT%H:%M:%S"

    FORMATS = {
        logging.DEBUG: grey + fmt + reset,
        logging.INFO: grey + fmt + reset,
        logging.WARNING: yellow + fmt + reset,
        logging.ERROR: red + fmt + reset,
        logging.CRITICAL: bold_red + fmt + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


ch.setFormatter(PeltomappiFormatter())

LOGGER.addHandler(ch)

# disable pyogrio logging, makes logs more confusing
logging.getLogger("pyogrio").setLevel(logging.WARNING)
