"""Console script for cloud_bug."""
import argparse
import sys

import cloud_bug


def main():
    """Console script for cloud_bug."""
    parser = argparse.ArgumentParser()
    parser.add_argument('_', nargs='*')
    args = parser.parse_args()

    print("Arguments: " + str(args._))
    print("Replace this message by putting your code into "
          "cloud_bug.cli.main")
    cb = cloud_bug.CloudDebug()
    cb.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
