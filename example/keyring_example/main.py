# Adds the local skeletonkey source code to path, so that version is imported
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

import skeletonkey

class MyModel:
    def __init__(self, layer_size: int, activation: str) -> None:
        self.layer_size = layer_size
        self.activation = activation

@skeletonkey.unlock("config.yaml")
def main(args):
    model1 = skeletonkey.instantiate(args.models.model1)
    model2 = skeletonkey.instantiate(args.models.model2)
    print("Number of MNIST targets: ", args.datasets.iris.num_targets)
    print("Number of iris targets: ", args.datasets.mnist.num_targets)

if __name__ == "__main__":  
    main()
