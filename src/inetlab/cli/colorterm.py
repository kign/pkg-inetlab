import os,sys,logging

def add_coloring_to_emit_ansi(fn):
    # http://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output
    def new(*args):
        levelno = args[1].levelno
        if(levelno >= 50):
            color = '\x1b[31;1m'  # red
        elif(levelno >= 40):
            color = '\x1b[31;1m'  # red
        elif(levelno >= 30):
            color = '\x1b[33m'  # yellow
        elif(levelno >= 20):
            color = '\x1b[32m'  # green
        elif(levelno >= 10):
            color = '\x1b[35m'  # pink
        else:
            color = '\x1b[0m'  # normal
        args[1].msg = color + args[1].msg + '\x1b[0m'  # normal
        return fn(*args)
    return new

class ColorTerminal(object) :
    def __init__ (self,nocolor=False) :
        self.term = None
        if not nocolor :
            try :
                # https://pypi.python.org/pypi/blessings/
                from blessings import Terminal
                self.term = Terminal ()
            except ModuleNotFoundError :
                print("blessings module isn't available thus no color", file=sys.stderr)

    def __getattr__(self, attr) :
        if self.term and attr != 'default':
            return getattr(self.term,attr)
        else :
            return self._nocolorterm

    def clear_sceeen(self) :
        if self.term :
            sys.stdout.write(self.term.clear())
        else :
            os.system('clear')

    @staticmethod
    def screen_size() :
        rows, columns = os.popen('stty size', 'r').read().split()
        return int(rows), int(columns)

    @staticmethod
    def _nocolorterm(*pars) :
        if len(pars) == 1 :
            return pars[0]


if __name__ == "__main__" :
    from genformatter import GenericFormatter

    log_level = "debug"
    logging.basicConfig(format="%(asctime)s [%(levelname)-8s] %(message)s",
                            level=getattr(logging, log_level.upper(), None))

    term = ColorTerminal()

    out = GenericFormatter("aligned,width=80")
    out.writeheader(['Name', 'Regular', 'Bright', 'Bold', 'Reverse', 'Underline'])
    for c in ['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'] :
        out.writerow([c, getattr(term, c)(c),
                      getattr(term, 'bright_' + c)('bright_' + c),
                      getattr(term, 'bold_' + c)('bold_' + c),
                      getattr(term, 'reverse_' + c)('reverse_' + c),
                      getattr(term, 'underline_' + c)('underline_' + c)
                    ])

    out.close ()
