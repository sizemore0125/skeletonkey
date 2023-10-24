# Adds the local skeletonkey source code to path, so that version is imported
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

import skeletonkey

@skeletonkey.unlock("config.yaml")
def main(args):
    print("Learning rate: ", args.learning_rate)
    print("Batch size: ", args.batch_size)
    print("Dropout: ", args.dropout)
    print("Optimizer: ", args.optimizer)

if __name__ == "__main__":  
    main()
