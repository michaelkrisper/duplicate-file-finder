import sys
import time

class UpdatePrinter(object):
    """Class for printing nice status output on the console."""
    def __init__(self, refreshrate=0.05, stream=sys.stdout):
        self.__last = 0
        self.__last_text_length = 0
        self.refreshrate = refreshrate
        self.stream = stream

    def update(self, value, force=False, flush=True):
        """Updates the last line on the console. Overwrites previous output made with 
        this method. Has a mechanism which prevents flickering. Use the force parameter to enforce output."""
        if ((time.time() - self.__last) >= self.refreshrate) or force:
            print("\r%s%s" % (value, " " * (self.__last_text_length - len(value))), end=' ', file=self.stream)
            self.__last_text_length = len(value)
            if flush:
                self.stream.flush()
            self.__last = time.time()

if __name__ == "__main__":
    PRINTER = UpdatePrinter()
    print("This is the NicePrinter.")
    i = 1
    for i in range(50, 0, -1):
        PRINTER.update("Printing a's from 50 to 1: %s" % ("a" * i))
        time.sleep(0.1)
    else:
        PRINTER.update("Printing a's from 50 to 1: %s" % ("a" * i), force=True)
    print("\nAnd this is the next output!")
