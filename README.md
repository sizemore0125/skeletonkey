# SkeletonKey: A Bare-bones Configuration Management Tool

<div align="center">
<picture>
    <source media="(prefers-color-scheme: dark)" srcset="./sklogo3.svg">
    <img alt="SK Logo" src="./sklogo_mono.svg" width="300">
</picture>
</div>


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
  _target_: main.MyModel
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

The resulting Config object will contain nested Config objects that can be accessed using dot notation, such as args.model.parameters.layer_size.


#### Defining Flags in Configuration

Flags can be defined in the configuration YAML file using the `?` prefix followed by the flag name. The value of the flag is set as `true` or `false`. Flags allow a user to switch to debug mode without having to modify the configuration file or temporarily enable/disable specific features for testing without changing the configuration.

For example:
```yaml
?debug: true
```
In the above example, a flag named `debug` is defined and set to `true`.

Once defined in the configuration, flags can be overridden using command-line arguments. To override a flag, simply pass the flag name prefixed with `--`.
```
python your_script.py --debug
```

Executing the above command will flip the value of the `debug` flag. If it was initially set to `true` in the configuration YAML, it will be changed to `false`, and vice versa.

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

3. When you run your project, `skeletonkey` will merge the default configuration files with the main configuration file, making the values from the default configuration files available in the `args` Config object:

```python
print("Learning rate: ", args.learning_rate)
print("Batch size: ", args.batch_size)
print("Dropout: ", args.dropout)
print("Optimizer: ", args.optimizer)
```


### Using Modular Subconfigurations

`skeletonkey` introduces the `keyring` feature, allowing users to modularize their configurations using arbitrary subconfigurations. This feature promotes reusability of common configurations and enhances readability by segregating configurations into logical sub-units.

The `keyring` feature requires users to define a `keyring` section in their main configuration file. Within this section, users can reference various subconfigurations that reside in separate files.

For example:
```yaml
keyring:
  models: 
    model1: subconfigs/model.yaml
    model2: subconfigs/model.yaml
  datasets:
    mnist: subconfigs/mnist.yaml
    iris: subconfigs/iris.yaml
```

In the above configuration, `model1`, `model2`, `mnist`, and `iris` are references to separate subconfigurations that are stored in their respective YAML files under the `subconfigs` directory. Using the `skeletonkey.instantiate` method, users can create instances of the `MyModel` class with the specified parameters from the subconfiguration.

Given this setup, here's how you can access values from these subconfigurations in your Python code:

```python
@skeletonkey.unlock("config.yaml")
def main(args):
    model1_config = args.models.model1
    model2_config = args.models.model2
    mnist_targets = args.datasets.mnist.num_targets
    iris_targets = args.datasets.iris.num_targets
```
Note: This assumes that num_targets is defined in both the mnist and the iris subconfigs.

### **Using Environment Variables in Configuration**

Environment variables can be incorporated in the configuration YAML file by using the `$` prefix followed by the name of the environment variable. This feature allows the user to store sensitive information, like API keys or database credentials, outside of the configuration file for security reasons. Additionally, a user can use different configurations for development, staging, and production environments by merely setting environment variables.

For example: 
```yaml
$DATABASE_URL: "default_database_url"
```
In the above example, the configuration will look for an environment variable named `DATABASE_URL`. If the environment variable exists, its value will be used; if not, the fallback value `"default_database_url"` will be utilized.
