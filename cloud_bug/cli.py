"""Console script for cloud_bug."""
import argparse
import sys

import cloud_bug


def main():
    """Console script for cloud_bug."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--update', default=False)
    parser.add_argument('--task-role', default=False)
    parser.add_argument('--cluster', default=False)
    parser.add_argument('--security-groups', default=False)
    parser.add_argument('--subnets', default=False)
    parser.add_argument('--image', default=False)
    args = parser.parse_args()

    print("Arguments: " + str(args._))
    print("Replace this message by putting your code into "
          "cloud_bug.cli.main")
    cb = cloud_bug.CloudDebug().setup(args.update)
    cb.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
