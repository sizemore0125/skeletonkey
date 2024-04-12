# Adds the local skeletonkey source code to path, so that version is imported
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

import skeletonkey

class C:
    def __init__(self, c_arg: int):
        self.c_arg: int = c_arg
        
class B:
    def __init__(self, b_arg: int, c_obj1: C, c_obj2: C):
        self.b_arg: int = b_arg
        self.c_obj1: C = c_obj1
        self.c_obj2: C = c_obj2

class A:
    def __init__(self, a_arg: int, b_obj: B):
        self.a_arg: int = a_arg
        self.b_obj: B = b_obj


@skeletonkey.unlock("config.yaml")
def main(args):
    a_obj = skeletonkey.instantiate(args.a_obj)
    
    print("a_obj: ", "\n",
          "\targ: ", a_obj.a_arg, "\n",
          
          "\tb_obj: ", "\n",
          "\t\targ: ", a_obj.b_obj.b_arg, "\n",
          
          "\t\tc_obj1: ",  "\n"
          "\t\t\targ: ", a_obj.b_obj.c_obj1.c_arg, "\n",
          
          "\t\tc_obj2: ", "\n",
          "\t\t\targ: ", a_obj.b_obj.c_obj2.c_arg, sep="")
          

if __name__ == "__main__":  
    main()
