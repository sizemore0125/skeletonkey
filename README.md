# SkeletonKey: A Bare-bones Configuration Management Tool

<div align="center">
<picture>
    <source media="(prefers-color-scheme: dark)" srcset="./sklogo3.svg">
    <img alt="skeletonkey Logo" src="./sklogo_mono.svg" width="300">
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
  _instance_: main.MyModel
  layer_size: 128
  activation: relu
```

### Working with `Config`

Parsed arguments are returned as a `Config` object. It behaves like a standard namespace object.
- Attribute or item access: `args.model.layer_size`
- Reassign config values in code: `args.model.layer_size = 256`
- Convert to dict: `dict(args)` or `args.to_dict()`
- Deep copy: `args.copy()`
- Deep update with dotted keys: `args.update({"model.layer_size": 256})` or `args.update(model_subconfig_obj)`
- Save to YAML: `args.to_yaml("out.yaml")`
- Instantiate inline: any node can call `.instantiate()`

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


The config path argument in `@skeletonkey.unlock()` is optional, and you can point to a config at runtime using the CLI argument `--config`. For example: `python main.py --config /path/to/config.yaml`.

#### Defining Flags in Configuration

Flags can be defined in the configuration YAML file using the `?` prefix followed by the flag name. The value of the flag is set as `true` or `false`. Flags allow a user to switch to debug mode without having to modify the configuration file or temporarily enable/disable specific features for testing without changing the configuration.

For example:
```yaml
?debug: false
```
In the above example, a flag named `debug` is defined and set to `false`.

Once defined in the configuration, flags can be overridden using command-line arguments. To override a flag, simply pass the flag name prefixed with `--`.
```
python your_script.py --debug
```

Executing the above command will flip the value of the `debug` flag. If it was initially set to `false` in the configuration YAML, it will be changed to `true`, and vice versa.

#### Using Environment Variables in Configuration

Environment variables can be incorporated in the configuration YAML file by using the `$` prefix followed by the name of the environment variable. This feature allows the user to store sensitive information, like API keys or database credentials, outside of the configuration file for security reasons. Additionally, a user can use different configurations for development, staging, and production environments by merely setting environment variables.

For example: 
```yaml
$DATABASE_URL: "default_database_url"
```
In the above example, the configuration will look for an environment variable named `DATABASE_URL`. If the environment variable exists, its value will be used; if not, the fallback value `"default_database_url"` will be utilized.


### Instantiating Objects

`skeletonkey.instantiate` builds objects described in YAML. Within your YAML config, you use one of these three keywords:

- `_instance_`: import and fully construct a class.
- `_partial_`: return `functools.partial` with provided kwargs bound for later completion.
- `_fetch_`: return a function without calling it.

Instantiation recurses through nested configs, so subcomponents are built automatically. To instatiate an object in skeletonkey, you can either use the function (`skeletonkey.instantiate(args.model)`) or the method on any `Config` node (`args.model.instantiate()`).

### Default Configuration Files

`skeletonkey` can merge other YAML files into your main config using a `profiles` section. The selected profile points to one or more YAML files that are merged before argument parsing.

Example:

```yaml
profiles:
  ~train:
    default: defaults/train.yaml
    model:
      head: models/train/head.yaml
      backbone: models/train/backbone.yaml
    dataset: datasets/train_dataset.yaml
  debug:
    default: defaults/debug.yaml
    model:
      head: models/debug/head.yaml
      backbone: models/debug/backbone.yaml
    dataset: datasets/debug_dataset.yaml
```

Select a profile via positional `profile` argument or `--profile`; entries prefixed with `~` are treated as the default when no profile is provided.


### Using Modular Subconfigurations

`skeletonkey` introduces the `keyring` feature, allowing users to modularize their configurations using arbitrary subconfigurations.

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
