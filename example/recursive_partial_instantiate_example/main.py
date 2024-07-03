# Adds the local skeletonkey source code to path, so that version is imported
import os, sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

import skeletonkey


class TransformerBlock:
    def __init__(self, d_model: int, nhead: int, dim_feedforward: int, dropout: float):
        self.d_model = d_model
        self.nhead = nhead
        self.dim_feedforward = dim_feedforward
        self.dropout = dropout

    def __repr__(self):
        return f"TransformerBlock(\n\td_model={self.d_model},\n\tnhead={self.nhead},\n\tdim_feedforward={self.dim_feedforward},\n\tdropout={self.dropout}\n)"


class SuperCoolNeuralNetwork:
    def __init__(
        self,
        input_size: int,
        output_size: int,
        hidden_size: int,
        encoder: TransformerBlock,
        activation: str = "relu",
        dropout: float = 0.5,
    ):
        self.input_size = input_size
        self.output_size = output_size
        self.hidden_size = hidden_size
        self.activation = activation
        self.dropout = dropout
        self.encoder = encoder

    def __repr__(self):
        return f"SuperCoolNeuralNetwork(\n\tinput_size={self.input_size}\n\toutput_size={self.output_size},\n\thidden_size={self.hidden_size},\n\tactivation={self.activation},\n\tdropout={self.dropout},\n\tencoder={self.encoder}\n)"

    def __call__(self, x):
        raise NotImplementedError("SuperCoolNeuralNetwork doesn't work :(")


@skeletonkey.unlock("config.yaml")
def main(config):
    partial_nn = skeletonkey.partial_instantiate(config.neural_network)
    print(f"Type of partial_nn: {type(partial_nn)}")
    # >>> Type of partial_nn: <class 'functools.partial'>

    nn = partial_nn(input_size=28**2, output_size=10)
    print(f"Type of nn: {type(nn)}")
    # >>> Type of nn: <class '__main__.SuperCoolNeuralNetwork'>
    print(nn)

    print(f"Type of nn.encoder before full instantiation: {type(nn.encoder)}")
    # >>> Type of nn.encoder: <class 'functools.partial'>
    nn.encoder = nn.encoder(dropout=0.3)
    print(f"Type of nn.encoder after full instantiation: {type(nn.encoder)}")
    # >>> Type of nn.encoder: <class '__main__.TransformerBlock'>
    print(nn.encoder)
    
    print(nn)

if __name__ == "__main__":
    main()
