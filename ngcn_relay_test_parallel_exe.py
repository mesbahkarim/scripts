import paramiko
import time
## import cmdParser
import os
import subprocess
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.ticker
import datetime
from optparse import OptionParser
import argparse
import csv


start_time = time.time()



def ConnectNode(ipcsvfile, UserName, PrivKey):
    connection = dict()
    with open(ipcsvfile) as csvfile:
        readline = csv.DictReader(csvfile)
        for row in readline:
#            print"Ip Address= {}".format(row['Ip_address'])
            InHostIp = row['Ip_address']


            PvKey = paramiko.RSAKey.from_private_key_file(PrivKey)
            inconnection = paramiko.SSHClient()
#            print "inconnection", inconnection
            inconnection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            print "Connecting...Host={}\n".format(InHostIp)
            inconnection.connect(hostname=InHostIp, username=UserName, pkey=PvKey, timeout=10)
            paramiko.util.log_to_file("filename.log")
            print "Connected...Host={}\n".format(InHostIp)
            connection[InHostIp] = inconnection

    return (connection)


def ExecCliCommand(*args):
    for arg in args:

        if (len(args)) == 1:
            CliCmmd = args[0]
        elif (len(args)) == 2:
            CliCmmd = args[0]
            DimStartVal = args[1]
        elif (len(args)) == 3:
            CliCmmd = args[0]
            DimStartVal = args[1]
            DimEndVal = args[2]

    if (CliCmmd == 'x-dim'):
        CliCmmds = 'echo -e "x-dim ' + str(DimStartVal) + " " + str(
            DimEndVal) + '\r"' + ' | sudo microcom -t 2000 /dev/ttyACM0'
    elif (CliCmmd == 'x-pwr-dump'):
        CliCmmds = 'echo -e "x-pwr-dump\r" | sudo microcom -t 2000 /dev/ttyACM0'
    elif (CliCmmd == 'x-pwr-aux-enable'):
        CliCmmds = 'echo -e "x-pwr-aux-enable ' + str(DimStartVal) + '\r"' + ' | sudo microcom -t 2000 /dev/ttyACM0'


    return CliCmmds


def ExecCommdSequence(ExeCycle, DimStartVal, DimEndVal, Rtype, DEBUG):
    intcommands = list()
    RelayOnOffLst = list()
    TimeofCmdExec = dict()
    CExStart = None
    CapTime = 0.0
    StartCycle = 0

    for CmKey in range(StartCycle, ExeCycle):

        if (CmKey % 2 == 0):

            if (Rtype == 'main'):
                GDimCmmd = ExecCliCommand("x-dim", 0, DimStartVal)
            elif (Rtype == 'aux'):
                GDimCmmd = ExecCliCommand("x-pwr-aux-enable", 0)

            CRelayOff = 'COFF'
            GPwrCmmd = ExecCliCommand("x-pwr-dump")
            PRelayOff = 'POFF'
            if (DEBUG == 'True'):
                print "Running {} Relay {}".format(Rtype, PRelayOff)
            intcommands.append(GDimCmmd)
            RelayOnOffLst.append(CRelayOff)
            intcommands.append(GPwrCmmd)
            RelayOnOffLst.append(PRelayOff)

        # time.sleep(ExecDelay)
        else:


            if (Rtype == 'main'):
                GDimCmmd = ExecCliCommand("x-dim", 0, DimEndVal)
            elif (Rtype == 'aux'):
                GDimCmmd = ExecCliCommand("x-pwr-aux-enable", 1)

            CRelayOn = 'CON'
            GPwrCmmd = ExecCliCommand("x-pwr-dump")
            PRelayOn = 'PON'

            intcommands.append(GDimCmmd)
            RelayOnOffLst.append(CRelayOn)
            intcommands.append(GPwrCmmd)
            RelayOnOffLst.append(PRelayOn)
            if (DEBUG == 'True'):
                print "Running {} Relay {}".format(Rtype, PRelayOn)
            #            time.sleep(ExecDelay)

    return (intcommands, RelayOnOffLst)


#    print "test,,,", intcommands


def MeasureCurrent(connection, hostip, command, ROnOff, ExecDelay, ExStart, SwitchOnFirst, Rtype, DEBUG):
    PowerinfoDict = dict()
    CurrentVal = None
    CurrentLimit = None
    TimeCmdExec = None
    FailedCurrent = None
    FailedTime = None
    SwitchOnCurrent = None
    SwitchOnTime = None
    power_status = 0

    if (Rtype == 'main'):
        Current_Type = 'main current'
        CurrentLimit = 5
    elif (Rtype == 'aux'):
        Current_Type = 'aux  current'
        CurrentLimit = 100

    #    ExStart = time.time()
#    print "ExStart={}".format(ExStart)
#    time.sleep(ExecDelay)

    stdin, stdout, stderr = connection.exec_command(command)
    AllTimeDelta = None
    lines = stdout.readlines()

    if ((ROnOff == "PON") or (ROnOff == "POFF")):

        for line in lines:
            pwrval = 0
            if "=" in line:

                pwrname, pwrval = line.split("=")
                pwrname = pwrname.rstrip()
                pwrval = pwrval.lstrip()
                PowerinfoDict[pwrname] = pwrval

                #                 print pwrname, pwrval

                if (pwrname == Current_Type):

                    if (DEBUG == 'True'):
                        print pwrname, pwrval
                    CurrentVal = pwrval.replace('mA', "").strip()
                    CurrentVal = int(CurrentVal)
                    AllExEnd = time.time()
                    AllTimeDelta = AllExEnd - ExStart

                if ((Rtype == 'main') and ( pwrname == 'power on')):
                    power_status = int(pwrval.lstrip())
#                    print "power_status_on", power_status
                elif ((Rtype == 'aux') and ( pwrname == 'aux on')):
#                    print "power_status_off", power_status
                    power_status = int(pwrval.lstrip())


        if (power_status == 1):

            TimeDelta = AllTimeDelta
            TimeCmdExec = AllExEnd
            SwitchOnCurrent = CurrentVal
            SwitchOnTime = TimeDelta
#            print "test....."
            time.sleep(ExecDelay)
            if ( SwitchOnFirst == None):
                print "Switch On First: Hostip = {} {}={}mA  at Time={} Delta_time={} power_status ={}".format(hostip,Current_Type,CurrentVal, AllExEnd, TimeDelta, power_status)
                SwitchOnFirst = 1

        elif ( (CurrentVal < CurrentLimit) and (power_status == 0) ):

            TimeDelta = AllTimeDelta
            TimeCmdExec = AllExEnd


            if (DEBUG == 'True'):
                 print "Pass: Hostip = {} {}={}mA  at Time={} Delta_time={} power_status={} ".format(hostip, Current_Type, CurrentVal, AllExEnd, TimeDelta, power_status)

        elif ((CurrentVal > CurrentLimit) and (power_status == 0) and ( SwitchOnFirst != None)):

            TimeDelta = AllTimeDelta
            TimeCmdExec = AllExEnd
            FailedCurrent = CurrentVal
            FailedTime = TimeDelta


            print "Fail: Hostip ={} {}={}ma at Time={} Delta_time={} power_status={}".format(hostip, Current_Type, CurrentVal, AllExEnd, TimeDelta, power_status)
    return (CurrentVal, TimeCmdExec, FailedCurrent, FailedTime, SwitchOnCurrent, SwitchOnTime, AllTimeDelta, SwitchOnFirst)


def PlotCurrent(CurrentLst, ExecTime, XaxisStart, FCList, FTList, OnCList, OnTList, TList):
    x = np.arange(3)
    MinCurrent = 5
    plt.xlabel("X-axis: Time Sec")
    plt.ylabel("Y-axis: Current mA")
    plt.title("Current Analysis Graph")
    ax = plt.gca()
    plt.ylim((0, 420))
    plt.xlim((5, 200))

    # ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(0.25))

    ## ax.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(5))

#    XaxisEnd = (XaxisStart + 4) * 6
#    print "XaxisEnd={}".format(XaxisEnd)
    ax.xaxis.set_ticks(np.arange(5, 200, 5))

    ##    ax.xaxis.set_ticks(np.arange(XaxisStart, XaxisEnd, 4))



    ax.yaxis.set_ticks(np.arange(0, 420, 20))

    # plt.plot(<X AXIS VALUES HERE>, <Y AXIS VALUES HERE>, 'line type', label='label here')



    labels, tbar = zip(*ExecTime)
    OnOff = np.arange(len(labels))
    width = .025

    xs = np.linspace(0, 200)
    #####horizontal line
    horiz_line_data = np.array([5 for i in xrange(len(xs))])
    plt.plot(xs, horiz_line_data, 'r--', label='MinCurrent')

    #    plt.bar(OnOff, tbar, width, align='center', color='blue')#

    #    plt.plot(CurrentLst, color='blue', label='Current')

    plt.plot(TList, CurrentLst)

    if (OnCList != None):
        plt.scatter(OnTList, OnCList, color='green')

    if (FCList != None):
        plt.scatter(FTList, FCList, color='red')

    plt.grid()
    plt.show()


def main():
#    PrivKey = "C:\Users\karimme\Documents\sensity_labtop\Documents\id_medianodeKey"
#    HostIp = "192.168.65.103"
#    HostIp = "68.140.244.72"
    HostIp = "68.140.245.168"
    UserName = "sensity"
    DimCh = 0
    DimOnVal = 1000
    DimOffVal = 0
    commands = list()
    main_current = "main current"
    CurrentList = list()
    TimeofCmdExec = dict()
    FailedTimeList = list()
    FailedCurrentList = list()
    SOnTimeList = list()
    SOnCurrentList = list()
    TimeList = list()
    StimeFlag = None
    SwitchOnFirst = None
    csvfile = None
    PrivKey = None
    xaxist = 0
    i = 0
#    CYCLE = 1
    connectionlist = dict()


    parser = argparse.ArgumentParser()

    parser.add_argument("--CycleCount", default = 10,  help="Specify Number of Counts to operate relay")
    parser.add_argument("--StartDimValue", default = '0', help="Specify Dimmer starting value")
    parser.add_argument("--EndDimValue", default = '500', help="Specify Dimmer Upper Dimmer high intesity value")
    parser.add_argument("--RelayOnOffDelay", default='0.01', help="Specify the relay On Off value")
#    parser.add_argument("--HostIp", default='92.168.65.103', help="Specify the HostIP")
    parser.add_argument("--RType", default='main', help="Specify Relay Type either main or aux")
    parser.add_argument("--Debug", action="store_true", help="Print detailed messages to stdout")
    parser.add_argument("--ipcsvfile", default='None', help="Specify CSV file with full path")
    parser.add_argument("--PrivKey", default='None', help="Specify the HostIP")



    args = parser.parse_args()
    CycleCount = int(args.CycleCount)
    StartDimValue = int(args.StartDimValue)
    EndDimValue = int(args.EndDimValue)
    RelayOnOffDelay = float(args.RelayOnOffDelay)
##    RelayOnOffDelay  = RelayOnOffDelay
    RType = str(args.RType)
    ipcsvfile = str(args.ipcsvfile)
    PrivKey  = str(args.PrivKey)

    Debug = str(args.Debug)
#    print "debug ....", Debug

#    ipcsvfile = "C:\Users\karimme\Documents\sensity_labtop\scripts\hostipaddress.csv"


    print "Cyclecount = {}, StartDimmerValue = {} EndDimmerValue = {} RelayOnOffDelay = {} ".format(CycleCount,StartDimValue,EndDimValue,RelayOnOffDelay)
    connectionlist = ConnectNode(ipcsvfile, UserName=UserName, PrivKey=PrivKey)
    (commands, ROnOff) = ExecCommdSequence(CycleCount, StartDimValue, EndDimValue, RType, Debug)

#    print "connectionlist = {}".format(connectionlist)
#    print "Ronoff", ROnOff

    #    print commands

    ExecStart = time.time()
    for command in commands:

        #        print "Executing\n"

        #        time.sleep(3)
        #        print "Executing {} \n".format(command)

        for key, value in connectionlist.items():
            hostip = key
            connection = value
            (CurrentVal, TimeExec, Fcurrent, FTime, SonCurrent, SonTime, AllTDelta, SwitchOnFirst) = MeasureCurrent(connection, hostip,
                                                                                                         command,
                                                                                                         ROnOff[i], RelayOnOffDelay,
                                                                                                         ExecStart, SwitchOnFirst, RType, Debug)

        if (AllTDelta != None):
            TimeList.append(AllTDelta)

        # print "Pass: with Current={}mA  at Time={} Delta_time={}".format(CurrentVal, ExecEnd, TimeDelta)

        if ((StimeFlag == None) and (ROnOff[i] == "POFF")):
            xaxist = TimeExec
#            print "xaxist===={}".format(xaxist)
            StimeFlag = 1300

#        TimeIncrement = TimeExec-xaxist
#        TimeIncrement = TimeExec
#        TimeofCmdExec[TimeIncrement] = ronoff

#        print "RonOff={}  Curentval={} Timeexe={} TimeIncrement={} relonoff={}".format(ROnOff[i], CurrentVal, TimeExec,
#                                                                                       TimeIncrement, ronoff)

        if (CurrentVal != None):
            CurrentList.append(CurrentVal)

        if (SonCurrent != None):
            SOnTimeList.append(SonTime)
            SOnCurrentList.append(SonCurrent)

        if (Fcurrent != None):
            FailedCurrentList.append(Fcurrent)
            FailedTimeList.append(FTime)

#            print "FailedCurrentList{}\n".format(FailedCurrentList)
#            print "FailedTimeList{}\n".format(FailedTimeList)

        i += 1

#    print "SOnTimeList{}\n".format(SOnTimeList)
#    print "SOnCurrentList{}\n".format(SOnCurrentList)
#    print "CurrentList{}".format(CurrentList)
#    print "TimeList{}".format(TimeList)

    #    print ROnOff

    #    print "FailedCurrentList{}\n".format(FailedCurrentList)

    #    print "FailedTimeList{}\n".format(FailedTimeList)

    TimeofCmdExecList = TimeofCmdExec.items()
#    PlotCurrent(CurrentList, TimeofCmdExecList, xaxist, FailedCurrentList, FailedTimeList, SOnCurrentList, SOnTimeList,
#                TimeList)


if __name__ == '__main__':
    main()

    timenow = datetime.datetime.now()
    print "--- Time Taken : {} Minutes ---  Date : {}".format(((time.time() - start_time) / 60.00), timenow)


