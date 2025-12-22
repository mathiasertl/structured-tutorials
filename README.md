# structured-tutorials

![image](https://github.com/mathiasertl/structured-tutorials/workflows/Tests/badge.svg)
![image](https://img.shields.io/pypi/v/structured-tutorials.svg)
![image](https://img.shields.io/pypi/dm/structured-tutorials.svg)
![image](https://img.shields.io/pypi/pyversions/structured-tutorials.svg)
![image](https://img.shields.io/github/license/mathiasertl/structured-tutorials)

`structured-tutorials` allows you to write tutorials that can be rendered as documentation and run on your
system to verify correctness.

With `structured-tutorials` you to specify steps in a configuration file. A Sphinx plugin allows you to
render those commands in your project documentation. A command-line tool can load the configuration file and
run it on your local system.

Please see the [official documentation](https://structured-tutorials.readthedocs.io/) for more detailed
information.

## Installation / Setup

Install `structured-tutorials`:

```
pip install structured-tutorials
```

and configure Sphinx:

```python
extensions = [
    # ... other extensions
    "structured_tutorials.sphinx",
]

# Optional: Root directory for tutorials (default: location of conf.py)
#structured_tutorials_root = DOC_ROOT / "tutorials"
```

## Your first (trivial) tutorial

To create your first tutorial, create it in `docs/tutorial.yaml` (or elsewhere, if you configured
`tutorial_root` in `conf.py`):

```yaml
parts:
  - commands:
      - command: structured-tutorial --help
        doc:
          output: |
            usage: structured-tutorial [-h] path
            ...
```

### Run the tutorial

Run the tutorial with:

```
$ structured-tutorial docs/tutorials/quickstart/tutorial.yaml
usage: structured-tutorial [-h] path
...
```

### Render tutorial in Sphinx:

Configure the tutorial that is being displayed - this will not show any output:

```
.. structured-tutorial:: quickstart/tutorial.yaml

.. structured-tutorial-part::
```

## TODO

* Ouptut test: lines/chars of output (exact or min/max)
* Test file existance or something like that
* Pre/post text for each part
* Running commands:

  * Clear env
  * Add env (value is template)

* Platform independent "echo" step (useful for debugging/testing)
* Run in vagrant

# License

This project is licensed under the MIT License. See LICENSE file for details.