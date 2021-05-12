import sys
import msgpack
from ciscocfg import CiscoCfg

ciscoCfg = CiscoCfg()

unp = msgpack.Unpacker(sys.stdin.buffer, raw=False)
for unpacker in unp:
    [type, msgid, method, params] = unpacker
    if type == 0:
        try:
            methodFunc = getattr(ciscoCfg, method)
            res = methodFunc(*params)
            sys.stdout.buffer.write(msgpack.packb([0, msgid, None, res], use_bin_type=True))
        except Exception as e:
            sys.stdout.buffer.write(msgpack.packb([0, msgid, str(e), None], use_bin_type=True))
