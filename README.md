# bones: A Bare-bones Configuration Management Tool

Bones is a simple, lightweight, and flexible configuration management tool that allows you to manage complex configurations for your applications using YAML files. It dynamically loads classes and their arguments at runtime, making it easy to set up and modify your projects.

### Usage

Below is an example of how to use Bones in your project:

```python
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../bones')))
import bones

class MyModel:
    def __init__(self, layer_size: int, activation: str) -> None:
        self.layer_size = layer_size
        self.activation = activation

@bones.skeleton_key("config.yaml")
def main(args):
    model = bones.instantiate(args.model)
    print("Model layer size: ", model.layer_size)
    print("Model activation: ", model.activation)

if __name__ == "__main__":  
    main()
```

To run the example above, create a config.yaml file with the following content:
```yaml
model:
  _target_: MyModel
  layer_size: 128
  activation: relu
```
To run the script and overwrite default arguments, use the command:
```
python project.py --model.layer_size 256
```
