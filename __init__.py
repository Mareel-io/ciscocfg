import sys
import msgpack
from ciscocfg import CiscoCfg

ciscoCfg = CiscoCfg()

class RPCHandler(object):
    @staticmethod
    def parse(configStr):
        ciscoCfg.loadCfg(configStr)
        return None

    @staticmethod
    def getVLANs():
        ciscoCfg.getVLANs()

    @staticmethod
    def setPortVLAN(portNo, pvid, taggedList, allowedList):
        ciscoCfg.setPortVLAN(portNo, pvid, taggedList, allowedList)

    @staticmethod
    def getConfig():
        return ciscoCfg.extractCfg()

unp = msgpack.Unpacker(sys.stdin.buffer, raw=False)
for unpacker in unp:
    [type, msgid, method, params] = unpacker
    if type == 0:
        try:
            methodFunc = getattr(RPCHandler, method)
            res = methodFunc(*params)
            sys.stdout.buffer.write(msgpack.packb([0, msgid, None, res], use_bin_type=True))
        except Exception as e:
            sys.stdout.buffer.write(msgpack.packb([0, msgid, str(e), None], use_bin_type=True))
