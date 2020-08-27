import argparse


def cl_args():
    parser = argparse.ArgumentParser(
        description="insert description here")
    parser.add_argument(
        "-n", nargs=1, required=True, help="The startnumber")
    parser.add_argument(
        "-f", nargs=1, required=True, help="The pdf to number")
    # parser.add_argument(
    #     "-t", action="store_true", help="No argument required... just a flag")
    return parser.parse_args()
