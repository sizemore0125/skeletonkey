# Adds the local skeletonkey source code to path, so that version is imported
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

import skeletonkey

class MyModel:
    def __init__(self, layer_size: int, activation: str) -> None:
        self.layer_size = layer_size
        self.activation = activation

@skeletonkey.unlock("config2.yaml", config_argument_keyword="config2")
def evaluate(args):
    print(args)
    print("Metric: ", args.eval.metric)
    print("Logging Path: ", args.eval.logging_path)
    # Note: All the args from main are inaccessable from this args object and vice versa. 

@skeletonkey.unlock("config1.yaml", config_argument_keyword="config1")
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

    evaluate()

if __name__ == "__main__":  
    main()
