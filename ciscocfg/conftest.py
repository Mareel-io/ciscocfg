#!/usr/bin/env python3

import sys
import ciscoconfparse
import re

from ciscocfg import CiscoCfg

ciscoCfg = CiscoCfg()

f = open('./bar.txt', 'r')
ciscoCfg.loadCfg(f.read())

ciscoCfg.defineVLANRagne([1,100,'200-210'])
ciscoCfg.setVLANName(100, 'VLAN 100')
ciscoCfg.setVLANName(200, 'VLAN 200')

ciscoCfg.setPortVLAN(24, 100, None, [1, 200])

sys.stdout.write(ciscoCfg.extractCfg())
