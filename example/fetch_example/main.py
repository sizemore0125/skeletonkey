# Adds the local skeletonkey source code to path, so that version is imported
import os, sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

import skeletonkey


def func1():
    print("func1 called")


def func2():
    print("func2 called")


def func3(*args):
    print(f"func3 called: {args}")


@skeletonkey.unlock("config.yaml")
def main(args):
    func = skeletonkey.instantiate(args.func)

    func()

    func = skeletonkey.instantiate(args.func3)

    func("arg1", "arg2", "arg3")


if __name__ == "__main__":
    main()
