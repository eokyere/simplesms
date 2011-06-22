import time

from gsm import port



def main():
    p = port.ControlPort(port='/dev/cu.HUAWEIMobile-Pcui')
    p.connect()

    
if __name__ == "__main__":
    main()
