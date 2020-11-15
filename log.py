# Imports
import logging
from datetime import datetime
import json


def get_today():
    return datetime.now().strftime("[%d/%m/%Y-%H:%M:%S]")

class Logger:
    def __init__(self, filename):
        self.headerFormat = get_today() + "-Middleware> "
        logging.basicConfig(level=logging.WARNING, filename=filename, filemode='w', format=self.headerFormat + '%(message)s')

    def log_warning(self, message):
        print(self.headerFormat + message)
        logging.warning(message)

    def log_request(self, id_, action, the_json = None):
        print(self.headerFormat + "From " + id_ + " requested /" + action +
            ("" if json == None else ("\nJSON received:\n" + json.dumps(the_json, indent=2))))
        logging.warning("From " + id_ + " requested /" + action +
            ("" if json == None else ("\nJSON received:\n" + json.dumps(the_json, indent=2))))

    def log_vd(self, hex_stream):
        print(self.headerFormat + "From VD hex stream is: " + hex_stream)
        logging.warning("From VD hex stream is: " + hex_stream)