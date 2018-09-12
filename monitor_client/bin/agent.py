import sys, os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from core import switch


if __name__ == "__main__":
    contr = switch.Control()
    if len(sys.argv) == 2:
        param = sys.argv[1]
        if 'start' == param:
            contr.start()
        elif 'stop' == param:
            contr.stop()
        elif 'check' == param:
            contr.check()
        elif 'help' == param:
            contr.helpInfo()
        else:
            print("not yes cmd")
            sys.exit(2)
    else:
        print("usage: %s start|stop|check|help" % sys.argv[0])
