# Adds the local skeletonkey source code to path, so that version is imported
import os, sys, pprint

sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

import skeletonkey


class MyModel:
    def __init__(self, layer_size: int, activation: str) -> None:
        self.layer_size = layer_size
        self.activation = activation


class MyObjective:
    def __init__(self, *args):
        print(f"My objective: {args}")
        return None


def main():
    args = skeletonkey.Config.unlock("config.yaml")

    print(args)
    print(dict(args))

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

    objective = args.objective.instantiate()

    pprint.pp(args.to_dict())


if __name__ == "__main__":
    main()
