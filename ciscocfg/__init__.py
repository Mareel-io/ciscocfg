import ciscoconfparse
import re
from .ciscoutil import *

nameregexp = re.compile('^[ ]*name (.*)')
switchportRegexp = re.compile('^[ ]*switchport (.*)')
portNumberRegexp = re.compile('^interface GigabitEthernet([0-9]*)')
vlanTagNoRegexp = re.compile('^interface vlan ([0-9]*)')
vlanRangeRegexp = re.compile('^vlan ([^a-zA-Z]*)')

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
