from __future__ import print_function
from motifapi import MotifApi

if __name__ == "__main__":
    import argparse
    import logging

    parser = argparse.ArgumentParser()
    parser.add_argument('--ip', required=True)
    parser.add_argument('--api-key', required=True)
    parser.add_argument('--verbose', action='store_true', default=False)

    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    api = MotifApi(args.ip, args.api_key)
    print("version: %r" % (api.call('version'),))

