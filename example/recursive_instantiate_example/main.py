# Adds the local skeletonkey source code to path, so that version is imported
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

import skeletonkey

class C:
    def __init__(self, arg: int):
        self.val: int = arg
        
class B:
    def __init__(self, arg: int, c_obj1: C, c_class: C):
        self.val: int = arg
        self.c1: C = c_obj1
        self.c2: C = c_class(40) # Instantiate C class


class A:
    def __init__(self, arg: int, b_obj: B):
        self.val: int = arg
        self.b: B = b_obj


@skeletonkey.unlock("config.yaml")
def main(args):
    a = skeletonkey.instantiate(args.a_obj)
    
    print("a_obj: ", "\n",
          "\targ: ", a.val, "\n",
          
          "\tb_obj: ", "\n",
          "\t\targ: ", a.b.val, "\n",
          
          "\t\tc_obj1: ",  "\n"
          "\t\t\targ: ", a.b.c1.val, "\n",
          
          "\t\tc_obj2: ", "\n",
          "\t\t\targ: ", a.b.c2.val, sep="")
          

if __name__ == "__main__":  
    main()
