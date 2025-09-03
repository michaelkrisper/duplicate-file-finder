import sys
import time

class UpdatePrinter(object):
    """Class for printing nice status output on the console."""
    def __init__(self, refreshrate=0.05):
        self.__last = 0
        self.__last_text_length = 0
        self.refreshrate = refreshrate

    def update(self, value, force=False, flush=True):
        """Updates the last line on the console. Overwrites previous output made with 
        this method. Has a mechanism which prevents flickering. Use the force parameter to enforce output."""
        if ((time.time() - self.__last) >= self.refreshrate) or force:
            print >> sys.stderr, "\r%s%s" % (value, " " * (self.__last_text_length - len(value))),
            self.__last_text_length = len(value)
            if flush:
                sys.stderr.flush()
            self.__last = time.time()

if __name__ == "__main__":
    PRINTER = UpdatePrinter()
    print "This is the NicePrinter."
    i = 1
    for i in range(50, 0, -1):
        PRINTER.update("Printing a's from 50 to 1: %s" % ("a" * i))
        time.sleep(0.1)
    else:
        PRINTER.update("Printing a's from 50 to 1: %s" % ("a" * i), force=True)
    print "\nAnd this is the next output!"
