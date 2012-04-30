import sys
import time

class UpdatePrinter(object):
    def __init__(self, refreshrate=0.05):
        self.__last = 0
        self.__last_text_length = 0
        self.refreshrate = refreshrate

    def update(self, value, force=False, flush=True):
        if ((time.time() - self.__last) >= self.refreshrate) or force:
            print "\r%s%s" % (value, " " * (self.__last_text_length - len(value))),
            self.__last_text_length = len(value)
            if flush:
                sys.stdout.flush()
            self.__last = time.time()

if __name__ == "__main__":
    printer = UpdatePrinter()
    print "This is the NicePrinter."
    for i in range(50, 0, -1):
        printer.update("Printing a's from 50 to 1: %s" % ("a" * i))
        time.sleep(0.1)
    else:
        printer.update("Printing a's from 50 to 1: %s" % ("a" * i), force=True)
    print "\nAnd this is the next output!"
