# Adds the local skeletonkey source code to path, so that version is imported
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

import skeletonkey


@skeletonkey.unlock("config.yaml")
def main(args):
    print(args)

if __name__ == "__main__":  
    main()
