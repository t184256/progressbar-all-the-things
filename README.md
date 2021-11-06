# progressbar-all-the-things

## What

A project to easily add progressbars to absolutely arbitrary processes
and then display a bunch of them together.

## Why

Ever wondered how much longer will some command take?
You sure ran it before, why couldn't your PC memorize that
and give you an estimate?

More specifically,
I'm absolutely not a fan of how `make -j` outputs a wall of text
with no chance for me to guessing the individual step progress from it.
No, `--output-sync` doesn't help in the slightest.

## How

`write`s are intercepted via eBPF and accounted,
the amount of written data is compared
to the past statistics for processes with the same command.

## Potential directions of evolution

* Package python bcc bindings in NixOS and use them
* Time-based guessing of the progress
* Estimate the last fail position separately from the last success position
