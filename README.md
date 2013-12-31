# mkdisc

Profile-based disc structure for simple backup tasks, with DVD image targets.

## Usage

```shell
python mkdisc.py <input_profile> <output_image>
```

Where:

* `<input_profile>` is a text file structured like [mkdisc.example.config]
* `<output_image>` will be an ISO file, preferably not yet existing.


mkdisc.py structures a temporary directory with symbolic links, and then deletes it.

# Platform support

This tool primarily runs on Linux. Future work might make abstract the ISO command process to work nicely on Mac OS X and other Unix.
No support for Windows environments is intended.
