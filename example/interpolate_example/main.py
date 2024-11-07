# Adds the local skeletonkey source code to path, so that version is imported
import os, sys, pprint
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

import skeletonkey

class MyModel:
    def __init__(self, activation: str, debug: bool) -> None:
        self.activation = activation
        self.debug = debug

class MyDataloader:
    def __init__(self, batch_size: int, debug: bool) -> None:
        self.batch_size = batch_size
        self.debug = debug


@skeletonkey.unlock("config.yaml")
def main(args):
    print(args)

if __name__ == "__main__":  
    main()
