import argparse
import logging

from sys import path
from os.path import dirname as dir

path.append(dir(path[0]))

from lib import icfp_interpreter

def parse_args():
    parser = argparse.ArgumentParser(
        description='Execute the provided ICFP script')
    parser.add_argument('--script', metavar='S', type=str, required=True,
                        help='the script to execute')
    parser.add_argument('--log_level', metavar='L', type=str,
                        help='the log level to print', default='debug')

    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    logging.basicConfig(level={
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
    }[args.log_level.lower()], format='%(message)s')

    print('Executing script %s:' % args.script)
    with open(args.script) as script:
        result = icfp_interpreter.compile(''.join(script.readlines()))()
        print('Result: %s' % result)
