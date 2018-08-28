#!/bin/sh

export PYTHONPATH=./python/

echo "Making!"
make py && echo "--------------------------------------------------------------------------------" && ./usercorn run --py ./asd.py ./bins/x86_64.linux.elf

