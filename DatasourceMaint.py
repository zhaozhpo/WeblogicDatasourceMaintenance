#!/usr/bin/python
import sys,os,re
from weblogic.security.internal import *
from weblogic.security.internal.encryption import *
from NewGeneratePassword import *
from OracleDB import *

def changeDSPassword(cService, dsName, newPassword):
    try:
        print "-- Changing weblogic " + dsName + " password --"
        edit()
        startEdit()
        encryptedPassword = cService.encrypt(newPassword)
        cd('/JDBCSystemResources/' + dsName + '/JDBCResource/' + dsName + '/JDBCDriverParams/' + dsName)
        set('PasswordEncrypted',encryptedPassword)
        save()
        activate()
    except Exception, e:
        cancelEdit('y')
        print e

def getPassword(cService, dsname):
    passwordAES = ''
    passwordArrayEnc = get("/JDBCSystemResources/"+ dsname +"/Resource/" + dsname + "/JDBCDriverParams/" + dsname + "/PasswordEncrypted")
    for asciiCode in passwordArrayEnc:
        passwordAES += chr(asciiCode)
    return cService.decrypt(passwordAES)

def manageDS(dsName, allServers, command="testPool"):
    domainRuntime()
    status = []
    for server in allServers:
        serverName = server.getName()
        jdbcRuntime = server.getJDBCServiceRuntime()
        datasources = jdbcRuntime.getJDBCDataSourceRuntimeMBeans()
        if "Name="+dsName+"," in str(datasources):
            cd('/ServerRuntimes/'+ serverName +'/JDBCServiceRuntime/' + serverName +'/JDBCDataSourceRuntimeMBeans/' + dsName)
            state = cmo.getState()
            if command == "testPool":
                try:
                    if state in ("Shutdown","Suspended","Overloaded"):
                        status.append("[" + serverName + ":" + state + "]")
                    else:
                        test = cmo.testPool()
                        if test:
                            status.append("[" + serverName + ":" + str(test) + "]")
                        else:
                            status.append("[" + serverName + ":OK]")
                except Exception, e:
                    status.append("[" + serverName + ":" + str(e) + "]")
            elif command == "shutdown":
                if state != 'Shutdown':
                    print "-- Shutting down " + dsName + " on " + serverName + " --"
                    try:
                        cmo.shutdown()
                    except Exception, e:
                        print e
                    serverConfig()
                    return "offline"
                else:
                    serverConfig()
                    return state
            elif command == "start":
                print "-- Starting " + dsName + " on " + serverName + " --"
                try:
                    cmo.start()
                except Exception, e:
                    print e
                return state
            elif command == "reset":
                print "-- Restarting MBeans " + dsName + " on " + serverName + " --"
                try:
                    cmo.reset()
                except Exception, e:
                    print e
    serverConfig()
    return str(status)

def getOracleDB(dsURL):
    print "dsURL: " + str(dsURL)
    if len(dsURL.split('@')) == 2:
        dsn = dsURL.split('@')[1].lstrip('/')
    else:
        dsn = dsURL.split('/',2)[2]
    
    if len(dsn.split(':')) == 3:
        hostname = dsn.split(':')[0]
        sid = dsn.split(':')[2]
        port = dsn.split(':')[1]
        isSID = False
    elif len(dsn.split(':')) == 2:
        hostname = dsn.split(':')[0]
        sid = dsn.split('/')[1]
        port = dsn.split(':')[1].split('/')[0]
        isSID = True
    else:
        hostname = dsn.split('host=')[1].split(')')[0]
        port = dsn.split('port=')[1].split(')')[0]
        if 'service_name' in dsn:
            sid = dsn.split('service_name=')[1].split(')')[0]
            isSID = False
        else:
            sid = dsn.split('sid=')[1].split(')')[0]
            isSID = True
        
    return hostname, port, sid, isSID

def printDatasourceInfo(dsName, dsUser, dsPassword, dsStatus, host, port, sid, stringArray, newPassword="",isSID=True):
    #update: make this into an array
    linebreak = '=' * 230
    prName = "|%s" % dsName.ljust(25)
    prUser = "|%s" % dsUser.center(30)
    prPassword = "|%s" % dsPassword.center(30)
    #prPassword = "|%s" % "<redacted>".center(30)
    prHost = "|%s" % host.center(30)
    prPort = "|%s" % port.center(6)
    prStatus = "|%s" % dsStatus.center(50)
    prSID = "|%s" % sid.center(20)
    prNewPassword = "|%s" % newPassword.center(30)

    stringArray.append(prName + prUser + prPassword + prHost + prPort + prSID + prNewPassword + prStatus + '|')
    stringArray.append(linebreak)
    return stringArray

def getDatasourceInfo(allServers, cService, passwordChangeList, dumpPasswords):
    host, port, sid, newPassword = "", "", "", ""
    isSID = True
    linebreak = "=" * 230
    stringArray = []
    stringArray.append(linebreak)
    stringArray.append('|%s' % "Datasource".ljust(25) +
                        '|%s' % "Username".center(30) +
                        '|%s' % "Password".center(30) +
                        '|%s' % "Host".center(30) +
                        '|%s' % "Port".center(6) +
                        '|%s' % "SID/Service Name".center(20) +
                        '|%s' % "NewPassword".center(30) +
                        '|%s' % "Status".center(50)  + '|'
    )
    stringArray.append(linebreak)

    allJDBCResources = cmo.getJDBCSystemResources()
    for ds in allJDBCResources:
        dsName = ds.getName()
        print "="*20 + " " + dsName + " " + "="*20
        dsUser = get("/JDBCSystemResources/"+ dsName +"/Resource/" + dsName + "/JDBCDriverParams/" + dsName + "/Properties/" + dsName + "/Properties/user/Value")
        dsPassword = ''
        dsURL = ds.getJDBCResource().getJDBCDriverParams().getUrl().lower()
        dsDriver = ds.getJDBCResource().getJDBCDriverParams().getDriverName()
        #dsJNDI = dsResource.getJDBCDataSourceParams().getJNDINames()[0]

        # Change Password if in passChangeList
        if (dsName in passwordChangeList) or dumpPasswords:
            dsPassword = getPassword(cService, dsName)
            newPassword = NewGeneratePassword().generate_pass()
            state = manageDS(dsName, allServers, "shutdown")
            if ("oracle" in dsURL) and ("oracle" in dsDriver.lower()):
                host, port, sid, isSID = getOracleDB(dsURL)
                db = OracleDB(dsURL,dsUser,dsPassword,dsDriver)
                db.changePassword(newPassword)
                changeDSPassword(cService, dsName, newPassword)
            if state == "offline":
                manageDS(dsName,allServers,"start")
        dsStatus = manageDS(dsName, allServers)

        stringArray = printDatasourceInfo(dsName, dsUser, dsPassword, dsStatus, host, port, sid, stringArray, newPassword, isSID)
    for string in stringArray:
        print string

def main():
    environment = sys.argv[1]
    domain = sys.argv[2]
    hostUser = 'weblogic'
    hostPass = 'welcome1'
    domain_path = '/u01/fmw/soa/user_projects/domains/'
    passwordChangeList = ['rntest']
    dumpPasswords = False

    # you need to provide two parameters, environment and domain
    if environment == '' or domain == '' :
            print 'Please enter two parameters for environment and domain'

    # if the environment is QAM
    if environment == 'DEV' :
            hostIP = '172.x.x.x'
            if domain == 'SYNC':
                    hostPort = '8001'
            if domain == 'ASYNC':
                    hostPort = '8002'
            if domain == 'RSYNC':
                    hostPort = '8003'

    # If my environment is Production
    if environment == 'PROD' :
            hostIP = '192.168.254.134'
            if domain == 'compact_domain':
                    hostPort = '7001'
            if domain == 'soadomain':
                    hostPort = '7010'
            if domain == 'osbdomain':
                    hostPort = '8010'

    path = domain_path + domain 
    security_path = path + "/security"

    connect( hostUser , hostPass , 't3://' + hostIP + ':' + hostPort )

    if passwordChangeList or listPasswords:
        encryptionService = SerializedSystemIni.getEncryptionService(security_path)
        cService = ClearOrEncryptedService(encryptionService)

    allServers=domainRuntimeService.getServerRuntimes()
    getDatasourceInfo(allServers, cService, passwordChangeList, dumpPasswords)
        
if __name__ == 'main':
    main()
