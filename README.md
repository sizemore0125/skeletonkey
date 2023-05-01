# SkeletonKey: A Bare-bones Configuration Management Tool

`skeletonkey` is a simple, lightweight, and flexible configuration management tool that allows you to manage complex configurations for your applications using YAML files. It dynamically loads classes and their arguments at runtime, making it easy to set up and modify your projects.

## Installation

To install skeletonkey via pip, run the following command:

```bash
pip install skeletonkey
```

## Usage

Below is an example of how to use `skeletonkey` in your project:

```python
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

if __name__ == "__main__":  
    main()
```

To run the example above, create a config.yaml file with the following content:
```yaml
epochs: 128
model:
  _target_: MyModel
  layer_size: 128
  activation: relu
```

### Overwriting Arguments

Overwriting default config arguments is easy with `skeletonkey`.

To execute the script and overwrite default arguments, use this command:

```bash
python project.py --epochs 256
````

Moreover, skeletonkey allows you to conveniently work with nested configurations. When dealing with nested arguments in a configuration file, skeletonkey enables you to overwrite default configuration values using dot-separated keys.

For instance, if your configuration file has a nested YAML, you can overwrite the default values like this:

```bash
python project.py --model.parameters.layer_size 256
```

The resulting Namespace object will contain nested Namespace objects that can be accessed using dot notation, such as args.model.parameters.layer_size.

### Default Configuration Files

`skeletonkey` also provides the functionality to specify multiple default configuration files at the beginning of the main configuration file. This feature allows you to easily manage and reuse common configurations across different projects or components.

Your main configuration file can include default configuration files using either of the following formats:

#### Format 1: Simple List

```yaml
defaults:
  - path\to\yaml_config1.yaml
  - path\to\yaml_config2.yaml
```

#### Format 2: Nested Dictionary

```yaml
defaults:
  path:
    to:
      - yaml_config1
      - yaml_config2
```

In both cases, `skeletonkey` will automatically merge the default configuration files with the main configuration file, prioritizing the settings in the main configuration file. This means that if there are any conflicts between the default configuration files and the main configuration file, the values in the main configuration file will take precedence.

Here's an example of how to use default configuration files in your project:

1. Create two default configuration files:

`default_config1.yaml`:
```yaml
learning_rate: 0.001
batch_size: 64
```

`default_config2.yaml`:
```yaml
dropout: 0.5
optimizer: adam
```

2. In your main `config.yaml` file, include the default configuration files:

```yaml
defaults:
  - default_config1.yaml
  - default_config2.yaml

epochs: 128
model:
  _target_: MyModel
  layer_size: 128
  activation: relu
```

3. When you run your project, `skeletonkey` will merge the default configuration files with the main configuration file, making the values from the default configuration files available in the `args` Namespace object:

```python
print("Learning rate: ", args.learning_rate)
print("Batch size: ", args.batch_size)
print("Dropout: ", args.dropout)
print("Optimizer: ", args.optimizer)
```
