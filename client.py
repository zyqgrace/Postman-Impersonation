import os
import socket
import sys


# Visit https://edstem.org/au/courses/8961/lessons/26522/slides/196175 to get
PERSONAL_ID = 'B03FFA'
PERSONAL_SECRET = '113619c855557bbe68464878e6aea7d3'


def main():
    # TODO
    try:
        conf_path = open(sys.argv[1],'r')
    except FileNotFoundError:
        sys.exit(1)
    print(conf_path.read())
    

    

if __name__ == '__main__':
    main()
