'''
    Some machines update wmi very slowly (30+ seconds)
    Make amps negative if discharging?
'''

import time, os, subprocess
from threading import Thread

if os.name == 'nt': #win
    import wmi, pythoncom
else:
    os.system('clear')

'''
    Class for extracting battery data from windows WMI
'''
class sProbe(object):
    # Windows only vars
    win32bat = {}
    portable = {}
    msbatt = {}

    # Linux only vars
    path = ''
    # Charge = Ah, Energy = Wh, Power = W
    props = {'status': '', 'charge-type': '', 'authentic': '', 'health': '', 'voltage_now': '', 'voltage_ocv': '', 'voltage_max_design': '',
            'voltage_min_design': '', 'voltage_max': '', 'voltage_min': '', 'voltage_boot': '', 'current_boot': '', 'charge_full': '',
            'charge_empty': '','charge_full_design': '', 'charge_empty_design': '', 'energy_full_design': '', 'energy_empty_design': '',
            'energy_now': '', 'energy_full': '', 'charge_counter': '', 'precharge_current': '','charge_term_current': '', 'constant_charge_current': '',
            'constant_charge_current_max': '','constant_charge_voltage': '', 'constant_charge_voltage_max': '', 'input_current_limit': '',
            'charge_control_limit': '', 'charge_control_limit_max': '', 'charge_control_start_threshold': '', 'charge_control_end_threshold': '',
            'charge_type': '', 'present': '', 'charge_behavior': '', 'calibrate': '', 'capacity': '', 'capacity_alert_min': '', 'capacity_alert_max': '',
            'capacity_level': '', 'capacity_error_margin': '', 'temp': '', 'temp_alert_min': '', 'temp_alert_max': '', 'temp_ambient': '',
            'temp_ambient_alert_min': '', 'temp_ambient_alert_max': '', 'temp_min': '', 'temp_max': '','time_to_empty': '', 'time_to_full': '',
            'manufacturer': '', 'model_name': '', 'serial_number': '', 'type': '', 'current_avg': '','current_max': '', 'current_now': '',
            'technology': '', 'voltage_avg': '', 'input_voltage_limit': '', 'input_power_limit': '', 'online': '', 'usb_type': '', 'charge_now': '',
            'fast_charge_timer': '',  'top_off_threshold_current': '', 'top_off_timer': '', 'cycle_count': '', 'ovp_voltage': '', 'manufacture_year': '',
            'manufacture_month': '', 'manufacture_day': '', 'power_now': '', 'power_avg': '',}

    # Shared vars
    # Numeric
    voltage = dischargerate = amps = chargerate = watts = hours = minutes = chargeRemaining = fullChargeCap\
       = designCapacity = designVoltage = health = chemistry = status = cycleCount = capRemaining = 0
    # String
    charging = deviceName = manufName = serial_num = statusString = ''
    going = True
    tracking = False

    
    @staticmethod
    def activate() -> None:
        '''
            Starts s_probe for windows, put all static variables in here
            th.start() to run thread
        '''
        pythoncom.CoInitialize()
        try:
            sProbe.getWin32Bat()
        except TypeError as e:
            raise TypeError('Win32Battery is null', e)
        sProbe.getRootWmi()
        sProbe.get_portable()
        
        sProbe.charging = sProbe.msbatt['BatteryStatus']['Charging']
        # sProbe.portable may not be instantiated
        sProbe.designCapacity = sProbe.portable['DesignCapacity'] if sProbe.portable else 0
        
        if not sProbe.designCapacity:
            sProbe.designCapacity = sProbe.win32bat['DesignCapacity'] or sProbe.msbatt['BatteryStaticData']['DesignedCapacity']
        
        sProbe.designCapacity = sProbe.designCapacity / 1000
        sProbe.fullChargeCap = sProbe.msbatt['BatteryFullChargedCapacity']['FullChargedCapacity'] / 1000
        sProbe.deviceName = sProbe.msbatt['BatteryStaticData']['DeviceName']
        sProbe.manufName = sProbe.msbatt['BatteryStaticData']['ManufactureName']
        sProbe.serial_num = sProbe.msbatt['BatteryStaticData']['SerialNumber']
        sProbe.chemistry = sProbe.getchemstr()
        sProbe.designVoltage = sProbe.win32bat['DesignVoltage'] or sProbe.portable['DesignVoltage']
        sProbe.designVoltage = int(sProbe.designVoltage) / 1000
        sProbe.statusString = sProbe.win32bat['Status']

        # Tracker object
        #sProbe.track = tracker.Tracker()
        #sProbe.tth = Thread(target=sProbe.track_thread)

        # Start seperate thread for refreshing probe values
        sProbe.th = Thread(target=sProbe.refresh)


    @staticmethod    
    def activate_l() -> None:
        '''
            Starts s_probe for linux, put static variables 
        '''
        if os.path.exists('/sys/class/power_supply/BAT0'):
            sProbe.path = '/sys/class/power_supply/BAT0/'
        elif os.path.exists('/sys/class/power_supply/BAT1'):
            sProbe.path = '/sys/class/power_supply/BAT1/'
        else:
            print("No Batteries")
            raise Exception('No Batteries detected')
        
        sProbe.charging = True if sProbe.__catFile('status', i=False) == 'Charging' else False
        sProbe.designCapacity = sProbe.__catFile('charge_full_design') or sProbe.__catFile('energy_full_design')
        sProbe.deviceName = sProbe.__catFile('model_name', i=False)
        sProbe.manufName = sProbe.__catFile('manufacturer', i=False)
        sProbe.serialNum = sProbe.__catFile('serial_number', i=False)
        sProbe.chemistry = sProbe.__catFile('technology', i=False)
        sProbe.designVoltage = sProbe.__catFile('voltage_max_design') or sProbe.__catFile('voltage_min_design')
        sProbe.statusString = sProbe.__catFile('status', i=False)

        sProbe.track = tracker.Tracker()
        sProbe.tth = Thread(target=sProbe.track_thread)
        
        sProbe.th = Thread(target=sProbe.refresh_l)


    @staticmethod
    def refresh():
        '''
            Main sProbe refresh function
            Sets all data in the sProbe class
            Put all dynamic variables in here
        '''
        while(sProbe.going):
            pythoncom.CoInitialize()
            sProbe.getWin32Bat()
            sProbe.getRootWmi()
            sProbe.getAvail()

            sProbe.charging = sProbe.msbatt['BatteryStatus']['Charging']
            sProbe.chargeRemaining = sProbe.win32bat['EstimatedChargeRemaining'] or sProbe.portable['EstimatedChargeRemaining']
            sProbe.fullChargeCap = sProbe.msbatt['BatteryFullChargedCapacity']['FullChargedCapacity'] / 1000
            sProbe.health = (sProbe.fullChargeCap / sProbe.designCapacity) * 100
            sProbe.cycleCount = sProbe.msbatt['BatteryCycleCount']['CycleCount']
            sProbe.status = sProbe.win32bat['Status'] or sProbe.portable['Status']
            sProbe.capRemaining = sProbe.msbatt['BatteryStatus']['RemainingCapacity'] / 1000
            sProbe.statusString = sProbe.win32bat['Status']
            
            if not sProbe.msbatt['BatteryStatus']['Charging']:
                # Laptop is charging
                if sProbe.msbatt['BatteryStatus']['DischargeRate'] >= 0:
                    sProbe.dischargerate = sProbe.msbatt['BatteryStatus']['DischargeRate'] / 1000
                    sProbe.amps = round(sProbe.dischargerate / sProbe.voltage, 3)
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
                    sProbe.amps = round(sProbe.chargerate / sProbe.voltage, 3)
                else:
                    sProbe.chargerate = 0
                    sProbe.amps = 0
                # Possible to have neither estimated run times
                # In seconds
                rwmi_est_rt = sProbe.msbatt['BatteryRuntime']['EstimatedRuntime']
                # In minutes
                win32_est_rt = sProbe.win32bat['EstimatedRunTime'] or sProbe.portable['EstimatedRunTime']
                # Reading could be large number, skip if longer than 24 hours
                if rwmi_est_rt < 34560 and rwmi_est_rt > 0:
                    sProbe.hours = int(rwmi_est_rt // 3600)
                    sProbe.minutes = int(rwmi_est_rt % 60)
                elif win32_est_rt and win32_est_rt < 1440 and win32_est_rt > 0:
                    sProbe.hours = int(win32_est_rt // 60)
                    sProbe.minutes = int(win32_est_rt % 60)

            sProbe.watts = round((sProbe.chargerate or sProbe.dischargerate), 3)
            
            # Set speed of sProbe data refresh
            time.sleep(1)

    
    @staticmethod
    def refresh_l():
        while(sProbe.going):
            sProbe.charging = True if sProbe.__catFile('status', i=False) == 'Charging' else False
            sProbe.voltage = sProbe.__catFile('voltage_now')
            # Either have current_now or power_now
            sProbe.amps = sProbe.__catFile('current_now')
            if sProbe.amps == 0:
                sProbe.watts = sProbe.__catFile('power_now')
                sProbe.amps = round(sProbe.watts / sProbe.voltage, 3)
            else:
                sProbe.watts = sProbe.voltage * sProbe.amps

            sProbe.fullChargeCap = sProbe.__catFile('charge_full') or sProbe.__catFile('energy_full')
            sProbe.health = sProbe.__catFile('health') or (sProbe.fullChargeCap / sProbe.designCapacity) * 100
            sProbe.chargeRemaining = int(sProbe.__catFile('capacity', i=False))
            sProbe.cycleCount = sProbe.__catFile('cycle_count', i=False)
            sProbe.status = sProbe.__catFile('status', i=False)
            # TODO: Test charge_now value
            cn = sProbe.__catFile('charge_now')
            if cn:
                sProbe.capRemaining = sProbe.__catFile('charge_now') * sProbe.voltage
            else:
                sProbe.capRemaining = sProbe.__catFile('energy_now')
            # TODO: test value
            seconds_to_full = sProbe.__catFile('time_to_full', i=False)
            if seconds_to_full:
                sProbe.hours = int(seconds_to_full // 3600)
                sProbe.minutes = int(seconds_to_full % 60)
            
            time.sleep(1)

    @staticmethod
    def __catFile(fname: str, i=True):
        '''
            Read the value from a linux file
            Parameters:
            i (bool): True if value is an integer in micro units
            Returns:
            content (str) or (int): the contents of the given file
        '''
        try:
            with open(sProbe.path + fname, 'r') as f:
                content = f.read()
                return int(content) / 1000000 if i else content.rstrip()
        except FileNotFoundError as fnf:
            return 0
        except OSError as err:
            return 0
        #try:
            # Python 3.7>
            #sProbe.props[fname] = subprocess.run(['cat', sProbe.path + fname], capture_output=True).stdout.decode().replace('\n', '')
        #except KeyError as k:
        #    print('catfile error' + k)


    '''
        Run when menu is clicked, start track_thread Thread
    '''
    @staticmethod
    def activate_tracking():
        if not sProbe.tth.is_alive() and not sProbe.tracking:
            sProbe.tracking = True
            sProbe.tth.start()
        else:
            sProbe.stop_tracking()


    '''
        If enabled, runs tracker.track_man every second
        tracking and going must be True.
        time.sleep(1) is main loop time for this thread
    '''
    @staticmethod
    def track_thread():
        while(sProbe.tracking and sProbe.going):
            sProbe.track.track_man()
            time.sleep(1)
        
        
    '''
        Stops the tracking thread and creates a new one
    '''
    @staticmethod
    def stop_tracking():
        sProbe.tracking = False
        sProbe.tth.join()
        # Make a new thread since thread can only be started once
        sProbe.tth = Thread(target=sProbe.track_thread)
        # Make a new tracker to increment session number
        sProbe.track = tracker.Tracker()
    
    
    '''
        Deletes history file
    '''
    @staticmethod
    def del_history():
        sProbe.track.clear_history()


    '''
        Enumerates all classes in //root/wmi/MSBatteryClass and puts values in msbatt dict.
        //root/wmi/ has individual classes like "BatteryCycleCount" and "BatteryStsatus etc.
        but MSBatteryClass has all instances with populated values.
        Has the same properties as win32_Portable_Battery but values can be different
        Unique values to this class:
            CapacityMultiplier ExpectedLife Location  ManufactureDate  Manufacturer  MaxBatteryError
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


    @staticmethod
    def get_portable():
        '''
            //root/cimv2/win32_PortableBattery, has the same values as win32_Battery
            Populates sProbe.portable dict
            Unique values:
                BatteryRechargeTime ExpectedBatteryLife
        '''
        if wmi.WMI().instances('win32_portablebattery'):
            p = wmi.WMI().instances('win32_portablebattery')[0]
            for i in p.properties.keys():
                sProbe.portable[i] = p.wmi_property(i).value
        else:
            return None


    '''
        Creates a dict with all properties from //root/cimv2/win32_battery
    '''
    @staticmethod
    def getWin32Bat():
        w = wmi.WMI().instances('win32_battery')[0]
        for i in w.properties.keys():
            sProbe.win32bat[i] = w.wmi_property(i).value


    '''
        Returns the value of a given property, otherwise 'N/A' string
    '''
    @staticmethod
    def tryinstance(prop):
        # for root/wmi instances
        try:
            tmp = wmi.WMI(moniker="//./root/wmi").instances(prop)
            if prop == 'BatteryCycleCount':
                return tmp[0].cyclecount
            elif prop == 'BatteryFullChargedCapacity':
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


    '''
        Not used, possible not accurate, but keeping for status codes
    '''
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
    

    '''
        Returns chemistry string from either /cimv2/win32_battery or /wmi/MSBatteryClass
    '''
    @staticmethod
    def getchemstr() -> str:
        ch = sProbe.msbatt['BatteryStaticData']['Chemistry']
        if ch > 8 or ch < 0:
            ch = sProbe.win32bat['Chemistry']
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
    

    '''
        Returns availability string, not used either
    '''
    @staticmethod
    def getAvail() -> str:
        # only call from refresh
        avail = sProbe.win32bat['Availability'] or sProbe.portable['Availability']
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
            avail = 'N/A'
        return avail
    

    '''
        Stops while loop in refresh
    '''
    @staticmethod
    def on_close():
        sProbe.going = False

