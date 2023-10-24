import skeletonkey

class MyModel:
    def __init__(self, layer_size: int, activation: str) -> None:
        self.layer_size = layer_size
        self.activation = activation

@skeletonkey.unlock("config.yaml")
def main(args):
    model = skeletonkey.instantiate(args.model)
    print("Model layer size: ", model.layer_size)
    print("Model activation: ", model.activation)
    print("Number of Epochs: ", args.epochs)
    print("Debug Flag: ", args.debug)

if __name__ == "__main__":  
    main()
