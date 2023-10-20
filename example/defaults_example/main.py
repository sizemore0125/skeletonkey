import skeletonkey

@skeletonkey.unlock("config.yaml")
def main(args):
    print("Learning rate: ", args.learning_rate)
    print("Batch size: ", args.batch_size)
    print("Dropout: ", args.dropout)
    print("Optimizer: ", args.optimizer)

if __name__ == "__main__":  
    main()
