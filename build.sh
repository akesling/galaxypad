#!/bin/sh

_wheel="sidecar/artifacts/wheels/$(ls sidecar/artifacts/wheels/ | grep 38 | grep linux | tail -n 1)"
pip install "${_wheel}"
