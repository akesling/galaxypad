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

def execute_with_identity_tx(coroutine):
    try:
        still_running = True
        tx_message = None
        while still_running:
            tx_message = coroutine.send(tx_message)
    except StopIteration as result:
        return result.value

if __name__ == '__main__':
    args = parse_args()
    logging.basicConfig(level={
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
    }[args.log_level.lower()], format='%(message)s')

    with open(args.script) as script:
        code = ''.join(script.readlines())

    print('Executing script %s:' % args.script)
    result = execute_with_identity_tx(icfp_interpreter.compile(code)())
    print('Result: %s' % result)
