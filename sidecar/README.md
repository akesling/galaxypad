For using an existing wheel, the `pyproject.toml` should be configured.  By default it's set up for MacOS, but just replace the wheel present with a Linux wheel and `poetry update` should work for you.

The process for building new wheels:

0) Make sure you have Rust nightly installed -- last tested on 1.46.0-nightly
1) Install https://github.com/PyO3/maturin.
2) Run `maturin build` for local architecture or `docker run --rm -v $(pwd):/io konstin2/maturin build` for cross-compiling for linux.
3) Copy new wheels to `sidecar/artifacts/wheels` and delete old wheels.
4) Update `pyproject.toml` with the new wheel and run `poetry update` from the
project root to install the wheel for local use.
