'''
    Make amps negative if discharging?

    A battery's end of life is typically when the FullChargeCapacity property falls
    below 80% of the DesignCapacity property
'''

import wmi, time, pythoncom
from threading import Thread

'''
    Class for extracting battery data from windows WMI
'''
class sProbe(object):
    voltage = dischargerate = amps = chargerate = watts = hours = minutes = 0
    charging = ''
    going = True
    tracking = False

    win32bat = {}
    msbatt = {}

    @staticmethod
    def __init__() -> None:
        try:
            sProbe.initWin32Bat()
        except TypeError as e:
            raise TypeError('Win32Battery is null', e)
        #sProbe.getStaticData()
        sProbe.getRootWmi()
        sProbe.get_portable()
        sProbe.get_health()
        
        # win32batt is most likely empty
        sProbe.designedCapacity = sProbe.msbatt['BatteryStaticData']['DesignedCapacity'] or sProbe.win32bat['DesignCapacity']
        sProbe.charging = sProbe.msbatt['BatteryStatus']['Charging']
        


    '''
        Main sProbe refresh function
        Sets all data in the sProbe class
    '''
    @staticmethod
    def refresh():
        while(sProbe.going):
            pythoncom.CoInitialize()
            sProbe.getWin32Bat()
            sProbe.getRootWmi()

            sProbe.charging = sProbe.msbatt['BatteryStatus']['Charging']

            
            if not sProbe.msbatt['BatteryStatus']['Charging']:
                # Laptop is charging
                if sProbe.msbatt['BatteryStatus']['DischargeRate'] >= 0:
                    sProbe.dischargerate = sProbe.msbatt['BatteryStatus']['DischargeRate'] / 1000
                    sProbe.amps = round(sProbe.dischargerate / sProbe.voltage, 1)
                    sProbe.chargerate = 0
                else:
                    sProbe.dischargerate = 0
                    sProbe.amps = 0
                # May not exist
                ttf = sProbe.win32bat['TimeToFullCharge']
                if ttf:
                    sProbe.hours = int(ttf // 3600)
                    sProbe.minutes = int(ttf % 60)
            else:
                # Laptop is discharging
                # Might be negative
                if sProbe.msbatt['BatteryStatus']['ChargeRate'] >= 0:
                    sProbe.chargerate = sProbe.msbatt['BatteryStatus']['ChargeRate'] / 1000
                    sProbe.amps = round(sProbe.chargerate / sProbe.voltage, 1)
                else:
                    sProbe.chargerate = 0
                    sProbe.amps = 0
                # Possible to have neither estimated run times
                rwmi_est_rt = sProbe.msbatt['BatteryRuntime']['EstimatedRuntime']         # In seconds
                win32_est_rt = sProbe.win32bat['EstimatedRunTime']                        # In minutes
                # Reading could be large number, skip if longer than 24 hours
                if rwmi_est_rt and rwmi_est_rt < 34560 and rwmi_est_rt > 0:
                    sProbe.hours = int(rwmi_est_rt // 3600)
                    sProbe.minutes = int(rwmi_est_rt % 60)
                elif win32_est_rt and win32_est_rt < 1440 and win32_est_rt > 0:
                    sProbe.hours = int(win32_est_rt // 60)
                    sProbe.minutes = int(win32_est_rt % 60)

            sProbe.watts = round((sProbe.chargerate or sProbe.dischargerate), 3)
            
            # Set speed of sProbe data refresh
            time.sleep(1)
            

    '''

    '''
    @staticmethod
    def get_portable():
        if wmi.WMI().instances('win32_portablebattery'):
            sProbe.portable = wmi.WMI().instances('win32_portablebattery')[0]
            return wmi.WMI().instances('win32_portablebattery')[0]
        else:
            sProbe.portable = None
        

    '''
    
    '''
    @staticmethod
    def getRootWmi():
        mbc = wmi.WMI(moniker="//./root/wmi").instances('MSBatteryClass')
        
        # Decode MSBatteryClass into list of dicts
        for x in mbc:
            tmp = {}
            path_str = str(x.path())
            keyname = path_str[path_str.index(':')+1:path_str.index('.')]
            for prop in x.properties.keys():
                tmp[prop] = x.wmi_property(prop).value
            sProbe.msbatt[keyname] = tmp

        sProbe.voltage = sProbe.msbatt['BatteryStatus']['Voltage'] / 1000

    '''

    '''
    @staticmethod
    def getWin32Bat():
        w = wmi.WMI().instances('win32_battery')[0]
        for i in w.properties.keys():
            sProbe.win32bat[i] = w.wmi_property(i).value
        

    @staticmethod
    def initWin32Bat():
        pythoncom.CoInitialize()
        w = wmi.WMI().instances('win32_battery')[0]
        for i in w.properties.keys():
            sProbe.win32bat[i] = w.wmi_property(i).value
    

    @staticmethod
    def getw32bat_inst():
            return wmi.WMI().instances('win32_battery')[0]


    @staticmethod
    def get_health():
        if sProbe.msbatt['BatteryStaticData']['DesignedCapacity'] is not None:
            bathealth = (sProbe.msbatt['BatteryFullChargedCapacity']['FullChargedCapacity'] / sProbe.msbatt['BatteryStaticData']['DesignedCapacity']) * 100
        return f'{bathealth:.2f}'


    # Some instances might not exist
    @staticmethod
    def tryinstance(prop):
        # for root/wmi instances
        try:
            tmp = wmi.WMI(moniker="//./root/wmi").instances(prop)
            if prop == 'BatteryCycleCount':
                return tmp[0].cyclecount
            elif prop == 'BatteryFullChargedCapacity':                  # mWh
                return tmp[0].fullchargedcapacity
            elif prop == 'BatteryControl':
                return tmp[0]
            elif prop == 'BatteryRunTime':
                if tmp[0].estimatedruntime <= 0:
                    sProbe.hours = 0
                    sProbe.minutes = 0
                    return None
                else:
                    sProbe.hours = int(tmp[0].estimatedruntime / 3600)
                    sProbe.minutes = int(tmp[0].estimatedruntime % 60)
                    return tmp[0].estimatedruntime / 60
            elif prop == 'BatteryTemperature':
                return tmp[0].temperature
            else:
                return tmp[0]
        except Exception as e:
            #print(f'{prop} does not exist \n{e}')
            return 'N/A'


    @staticmethod
    def getStatus() -> str:
        statcode = sProbe.win32bat['BatteryStatus']
        if statcode == 1:
            statcode = 'Other'
        elif statcode == 2:
            statcode = 'Unknown'
        elif statcode == 3:
            statcode = 'Fully Charged'
        elif statcode == 4:
            statcode = 'Low'
        elif statcode == 5:
            statcode = 'Critical'
        elif statcode == 6:
            statcode = 'Charging'
        elif statcode == 7:
            statcode = 'Charging and High'
        elif statcode == 8:
            statcode = 'Charging and Low'
        elif statcode == 9:
            statcode = 'Charging and Critical'
        elif statcode == 10:
            statcode = 'Undefined'
        elif statcode == 11:
            statcode = 'Partially Charged'
        return statcode
    
    @staticmethod
    def getchemstr() -> str:
        ch = sProbe.msbatt['BatteryStaticData']['Chemistry']
        # only call from refresh
        if ch == 1:
            chem = 'Other'
        elif ch == 2:
            chem = 'Unknown'
        elif ch == 3:
            chem = 'Lead Acid'
        elif ch == 4:
            chem = 'Nickel Cadmium'
        elif ch == 5:
            chem = 'Nickel Metal Hydride'
        elif ch == 6:
            chem = 'Lithium-ion'
        elif ch == 7:
            chem = 'Zinc air'
        elif ch == 8:
            chem = 'Lithium Polymer'
        else:
            chem = 'N/A'
        return chem
    

    @staticmethod
    def getAvail() -> str:
        # only call from refresh
        avail = sProbe.win32bat['Availability']
        if avail == 1:
            avail = 'Other'
        elif avail == 2:
            avail = 'Unknown'
        elif avail == 3:
            avail = 'Running at full power'
        elif avail == 4:
            avail = 'Warning'
        elif avail == 5:
            avail = 'Test Mode'
        elif avail == 6:
            avail = 'N/A'
        elif avail == 7:
            avail = 'Power Off'
        elif avail == 8:
            avail = 'Off Line'
        elif avail == 9:
            avail = 'Off Duty'
        elif avail == 10:
            avail = 'Degraded'
        elif avail == 11:
            avail = 'Not Installed'
        elif avail == 12:
            avail = 'Install Error'
        elif avail == 13:
            avail = 'Power Save'
        elif avail == 14:
            avail = 'Power Save (Low Power Mode)'
        elif avail == 15:
            avail = 'Power Save (Standby)'
        elif avail == 16:
            avail = 'Power Cycle'
        elif avail == 17:
            avail = 'Power Save (Warning)'
        elif avail == 18:
            avail = 'Paused'
        elif avail == 19:
            avail = 'Not Ready'
        elif avail == 20:
            avail = 'Not Configured'
        elif avail == 21:
            avail = 'Quiesced'
        else:
            avail = 'Unknown'
        return avail
    

    @staticmethod
    def on_close():
        sProbe.going = False

