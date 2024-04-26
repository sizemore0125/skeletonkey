# Adds the local skeletonkey source code to path, so that version is imported
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

import skeletonkey

def main():
    config_a = skeletonkey.Config({
        "a": {
            "one" : "a1",
            "two" : "a2"
        },
        "b" : {
            "one" : "b1",
            "two" : "b2"
        }
    })

    update_config = {
        "b.one" : "b1_u",
        "b.two" : "b2_u",
        "b.three.c" : "b3c_u",
        "c.one" : "c1_u"
    }

    print(config_a)
    print("\n")
    config_a.update(update_config)  
    print(config_a)


if __name__ == "__main__":
    main()