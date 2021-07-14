#!/usr/bin/env python3

import msgpack
import sys

file = open("cfg.txt", "r");
cfg = file.read()

sys.stdout.buffer.write(msgpack.packb([0, 1, "parse", [cfg]], use_bin_type=True))
sys.stdout.buffer.write(msgpack.packb([0, 2, "getConfig", []], use_bin_type=True))
sys.stdout.flush()
