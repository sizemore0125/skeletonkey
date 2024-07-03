# Adds the local skeletonkey source code to path, so that version is imported
import os, sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

import skeletonkey


class SuperCoolNeuralNetwork:
    def __init__(
        self,
        input_size: int,
        output_size: int,
        hidden_size: int,
        activation: str = "relu",
        dropout: float = 0.5,
    ):
        self.input_size = input_size
        self.output_size = output_size
        self.hidden_size = hidden_size
        self.activation = activation
        self.dropout = dropout

    def __repr__(self):
        return f"SuperCoolNeuralNetwork(input_size={self.input_size}, output_size={self.output_size}, hidden_size={self.hidden_size}, activation={self.activation}, dropout={self.dropout})"

    def __call__(self, x):
        raise NotImplementedError("SuperCoolNeuralNetwork doesn't work :(")


@skeletonkey.unlock("config.yaml")
def main(config):
    partial_nn = skeletonkey.partial_instantiate(config.neural_network)
    print(f"Type of partial_nn: {type(partial_nn)}")
    # >>> Type of partial_nn: <class 'functools.partial'>

    epic_model = partial_nn(input_size=28**2, output_size=10)
    print(f"Type of epic_model: {type(epic_model)}")
    # >>> Type of partial_nn: <class 'functools.partial'>

    print(epic_model)


if __name__ == "__main__":
    main()
