#!/bin/sh

if [ "$(uname)" = "Darwin" ]; then
    pip install "$(ls sidecar/artifacts/wheels/ | grep mac | tail -n 1)"
else
    pip install "$(ls sidecar/artifacts/wheels/ | grep linux | tail -n 1)"
fi
