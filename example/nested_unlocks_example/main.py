# Adds the local skeletonkey source code to path, so that version is imported
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

import skeletonkey

class MyModel:
    def __init__(self, layer_size: int, activation: str) -> None:
        self.layer_size = layer_size
        self.activation = activation

# Note: The last decorator applied (config1) will overwriute any matching keys in any previous configs (config2).
@skeletonkey.unlock("config1.yaml")
@skeletonkey.unlock("config2.yaml")
def main(args):
    print(args)
    model = skeletonkey.instantiate(args.model)
    print("Instantiate Function:")
    print("Model layer size: ", model.layer_size)
    print("Model activation: ", model.activation)
    print("Number of Epochs: ", args.epochs)
    print("Debug Flag: ", args.debug)

    model2 = args.model.instantiate()
    print("Instantiate Method:")
    print("Model layer size: ", model2.layer_size)
    print("Model activation: ", model2.activation)
    print("Number of Epochs: ", args.epochs)
    print("Debug Flag: ", args.debug)

    print("Metric: ", args.eval.metric)
    print("Logging Path: ", args.eval.logging_path)

if __name__ == "__main__":  
    main()
