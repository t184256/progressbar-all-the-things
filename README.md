# progressbar-all-the-things

## What

A client-server project to easily add progressbars to custom commands
and then display a bunch of them together.

Launch a command with `progressbar-it`, get a progressbar.

If a command inside it also launches others with `progressbar-it`,
grow separate progressbars for them as well.

## Why

I'm absolutely not a fan of how `make -j` outputs a wall of text
with no chance for me to guessing the individual step progress from it.
No, `--output-sync` doesn't help in the slightest.

## How

`write`s are intercepted via eBPF and accounted on the server.
There the amount of written data
is compared to the past statistics for similar processes.

## Potential directions of evolution

* Package python bcc bindings in NixOS and use them
* Separate server from displaying
  (to monitor your progressbars on a separate monitor, phone...)
* Time-based guessing of the progress
* Estimate the last fail position separately from the last success position
