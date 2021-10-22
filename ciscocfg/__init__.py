import ciscoconfparse
import re
from .ciscoutil import *

nameregexp = re.compile('^[ ]*name (.*)')
switchportRegexp = re.compile('^[ ]*switchport (.*)')
portNumberRegexp = re.compile('^interface GigabitEthernet([0-9]*)')
vlanTagNoRegexp = re.compile('^interface vlan ([0-9]*)')
vlanRangeRegexp = re.compile('^vlan ([^a-zA-Z]*)')

shutdownRegexp = re.compile('^[ ]*shutdown')

# Interface RegExp
ifNameRegexp = re.compile('^([a-zA-Z]+)([0-9]+)')
ifNameTable = {
    'gi': 'GigabitEthernet',
}
confNameTable = { # TODO: Find way to automate this
    'GigabitEthernet': 'gi',
}

class CiscoCfg(object):
    def loadCfg(self, configStr):
        configs = configStr.split('\n')
        self.config = ciscoconfparse.CiscoConfParse(configs)

    def extractCfg(self):
        buf = "";
        for line in self.config.ioscfg:
            buf += line + '\n'
        return buf

    def getVLANRange(self):
        vlanRangeEntries = self.config.find_objects('^vlan [^a-zA-Z]+')
        if len(vlanRangeEntries) == 0:
            return ['1']
        res = vlanRangeRegexp.findall(vlanRangeEntries[0].text.strip())
        return (['1'] + res[0].split(','))

    def defineVLANRagne(self, vlanlist):
        vlandbstart = self.config.find_objects('^vlan database$')[0]
        # TODO: Handle None
        if vlandbstart == None:
            raise Exception('VLAN database is empty :(')

        vlanRangeEntries = self.config.find_objects('^vlan [^a-zA-Z]*$')
        for vlanRange in vlanRangeEntries:
            vlanRange.delete()
        self.config.commit()
        vlanRangeStr = ','.join(map(lambda e: str(e), vlanlist))
        self.config.insert_after('^vlan database$', 'vlan ' + vlanRangeStr, atomic=True)

    def setVLANName(self, tagNo, name):
        vlans = self.config.find_objects('^interface vlan ' + str(tagNo) + '$')
        if len(vlans) == 0:
            self.config.append_line
            return
        for vlan in vlans:
            vlan.delete_children_matching('^[ ]*name')
        self.config.commit()
        vlans = self.config.find_objects('^interface vlan ' + str(tagNo) + '$')
        for vlan in vlans:
            vlan.append_to_family('name ' + ciscoutil.escapeString(name), auto_indent=True)
        self.config.commit()

    def getVLANs(self):
        vlans = self.config.find_objects('^interface vlan')
        vlanList = []
        for vlan in vlans:
            tagMatchRes = vlanTagNoRegexp.findall(vlan.text.strip())
            vlanEntry = {'tagNo': int(tagMatchRes[0])}
            for elem in vlan.children:
                tokens = elem.text.strip().split(' ')
                if tokens[0] == 'name':
                    nameRes = nameregexp.findall(elem.text.strip())
                    vlanEntry['name'] = ciscoutil.unescapeString(nameRes[0])
            vlanList.append(vlanEntry)

        return vlanList

    def getPorts(self):
        ports = self.config.find_objects('^interface GigabitEthernet')
        if len(ports) == 0:
            return []
        portList = []
        for port in ports:
            portNumberMatch = portNumberRegexp.findall(port.text.strip())
            portMeta = {'portNo': int(portNumberMatch[0])}
            for elem in port.children:
                switchportCmdMatch = switchportRegexp.findall(elem.text.strip())
                if len(switchportCmdMatch) != 0:
                    tokens = switchportCmdMatch[0].split(' ')
                    if tokens[0] == 'trunk':
                        if tokens[1] == 'native':
                            portMeta['pvid'] = int(tokens[3])
                        elif tokens[1] == 'allowed':
                            portMeta['allowedList'] = tokens[3].split(',')
                    #elif tokens[0] == 'general':
                    #    portMeta['taggedList'] = 
                    elif tokens[0] == 'mode':
                        portMeta['mode'] = tokens[1]

            portList.append(portMeta)

        return portList

    def setPortVLAN(self, portNo, pvid, taggedList, allowedList):
        ports = self.config.find_objects('^interface GigabitEthernet' + str(portNo) + '$')
        if len(ports) == 0:
            self.config.append_line('interface GigabitEthernet' + str(portNo))
            self.config.append_line('!')
            self.config.commit()
            ports = self.config.find_objects('^interface GigabitEthernet' + str(portNo) + '$')
        for elem in ports[0].children:
            switchportCmdMatch = switchportRegexp.findall(elem.text.strip())
            if len(switchportCmdMatch) != 0:
                tokens = switchportCmdMatch[0].split(' ')
                if tokens[0] == 'trunk':
                    if tokens[1] == 'native':   
                        elem.delete()
                    elif tokens[1] == 'allowed':
                        elem.delete()
                elif tokens[0] == 'general':
                    # TODO: Is it right?
                    elem.delete()
                elif tokens[0] == 'mode':
                    elem.delete()
        self.config.commit()
        ports = self.config.find_objects('^interface GigabitEthernet' + str(portNo) + '$')
        ports[0].append_to_family('switchport mode trunk', auto_indent=True)
        if pvid != None:
            ports[0].append_to_family('switchport trunk native vlan ' + str(pvid), auto_indent=True)
        if allowedList != None:
            allowedListStr = ','.join(map(lambda x: str(x), allowedList))
            ports[0].append_to_family('switchport trunk allowed vlan ' + allowedListStr, auto_indent=True)
        if taggedList != None:
            taggedListStr = ','.join(map(lambda x: str(x), taggedList))
            ports[0].append_to_family('switchport general allowed vlan add ' + taggedListStr, auto_indent=True)
        self.config.commit()

    def getQueuePriority(self):
        wrr_prio = self.config.find_objects('^wrr-queue bandwidth')
        base_arr = [1, 2, 4, 8, 16, 32, 64, 128]

        if len(wrr_prio) == 0:
            # Default values are 1 2 4 8 16 32 64 128
            return base_arr
        
        wrr_prio = wrr_prio[0]
        tokens = wrr_prio.split(' ')[2:]
        for idx, v in enumerate(tokens):
            base_arr[idx] = int(v)
        
        return base_arr
        
    def setQueuePriority(self, wrr):
        data = wrr[:8]
        if len(wrr) < 1:
            return
        wrr_prio = self.config.find_objects('^wrr-queue bandwidth')
        if len(wrr_prio) > 0:
            wrr_prio.delete()
            self.config.commit()

        cmdstr = 'wrr-queue bandwidth '
        for v in data:
            cmdstr += str(v)
            cmdstr += ' '
        
        self.config.append_line(cmdstr)
        self.config.commit()

    def getStrictPriorityQ(self):
        num_of_q = self.config.find_objects('^priority-queue out num-of-queues')
        queue_num = num_of_q.split(' ')[4]
        return int(queue_num)

    def setStrictPriorityQ(self, queue_num):
        num_of_q = self.config.find_objects('^priority-queue out num-of-queues')

    def _getDefaultDSCPMap(self):
        return {
            0: 2, 1: 2, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1,
            8: 1, 9: 3, 10: 3, 11: 3, 12: 3, 13: 3, 14: 3, 15: 3,
            16: 7, 17: 4, 18: 4, 19: 4, 20: 4, 21: 4, 22: 4, 23: 4,
            24: 7, 25: 5, 26: 5, 27: 5, 28: 5, 29: 5, 30: 5, 31: 5,
            32: 8, 33: 6, 34: 6, 35: 6, 36: 6, 37: 6, 38: 6, 39: 6,
            40: 7, 41: 8, 42: 8, 43: 8, 44: 8, 45: 8, 46: 8, 47: 8,
            48: 7, 49: 7, 50: 7, 51: 7, 52: 7, 53: 7, 54: 7, 55: 7,
            56: 7, 57: 7, 58: 7, 59: 7, 60: 7, 61: 7, 62: 7, 63: 7
        }

    def setDSCPMap(self, map):
        newmap = {}
        for k, v in map.items():
            newmap[int(k)] = v

        # Remove all queuemap
        queuemap = self.config.find_objects('^qos map dscp-queue')
        for ent in queuemap:
            ent.delete()
        self.config.commit()

        for k, v in newmap.items():
            cmd = 'qos map dscp-queue ' + str(k) + ' to ' + str(v)
            self.config.append_line(cmd)

        self.config.commit()

    def getDSCPMap(self):
        defaultMap = self._getDefaultDSCPMap()
        queuemap = self.config.find_objects('^qos map dscp-queue')
        for map in queuemap:
            splt = map.split(' ')
            defaultMap[int(splt[3])] = int(splt[5])

        return defaultMap

    def _getDefaultCoSMap(self):
        return {
            0: 1, 1: 2, 2: 3, 3: 6, 4: 5, 5: 8, 6: 8, 7: 7,
        }

    def setCoSMap(self, map):
        queuemap = self.config.find_objects('^wrr-queue cos-map ')

        for cmd in queuemap:
            cmd.delete()
        self.config.commit()

        for k, v in map.items():
            cmd = 'wrr-queue cos-map ' + str(v) + ' ' + str(k)
            self.config.append_line(cmd)
        self.config.commit()

    def getCoSMap(self):
        defaultMap = self._getDefaultCoSMap()
        queuemap = self.config.find_objects('^wrr-queue cos-map ')

        for cmd in queuemap:
            splt = cmd.split(' ')
            defaultMap[int(splt[3])] = int(splt[2])
        
        return defaultMap

    def setPort(self, port):
        # TODO: Exact match?
        ifMatch = ifNameRegexp.findall(port['portName'])
        if len(ifMatch) == 0:
            return # TODO: Handle error
        ifTuple = ifMatch[0]
        ifType = ifNameTable[ifTuple[0]]
        ifNo = ifNameTable[ifTuple[1]]

        configPortName = ifType + ifNo
        ports = self.config.find_objects('^interface ' + configPortName)
        if len(ports) == 0:
            self.config.append_line('interface ' + configPortName)
            self.config.append_line('!')
            self.config.commit()
            ports = self.config.find_objects('^interface ' + configPortName)
        children = ports[0].children
        for child in children:
            shutdownMatch = shutdownRegexp.findall(child.text.strip())
            if (len(shutdownMatch) != 0):
                child.delete()

        self.config.commit()
        ports = self.config.find_objects('^interface ' + configPortName)
        if not port['isActive']:
            ports[0].append_to_family('shutdown')
