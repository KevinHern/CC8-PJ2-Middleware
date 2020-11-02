# Imports
import logging
from datetime import datetime


def get_today():
    return datetime.now().strftime("[%d/%m/%Y-%H:%M:%S]")

class Logger:
    def __init__(self, filename):
        self.headerFormat = get_today() + "-Middleware> "
        logging.basicConfig(level=logging.WARNING, filename=filename, filemode='w', format=self.headerFormat + '%(message)s')

    def log_warning(self, message):
        print(self.headerFormat + message)
        logging.warning(message)

    def log_request(self, id_, action):
        print(self.headerFormat + "From " + id_ + " requested /" + action)
        logging.warning("From " + id_ + " requested /" + action)

    def log_vd(self, hex_stream):
        print(self.headerFormat + "From VD hex stream is: " + hex_stream)
        logging.warning("From VD hex stream is: " + hex_stream)