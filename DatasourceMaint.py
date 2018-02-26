#!/usr/bin/python
#from OracleDB import *
#from GeneratePassword import *
import sys,os,re
from weblogic.security.internal import *
from weblogic.security.internal.encryption import *

def getPassword(cService, dsname):
    passwordAES = ''
    passwordArrayEnc = get("/JDBCSystemResources/"+ dsname +"/Resource/" + dsname + "/JDBCDriverParams/" + dsname + "/PasswordEncrypted")
    for asciiCode in passwordArrayEnc:
        passwordAES += chr(asciiCode)
    return cService.decrypt(passwordAES)

def getDatasourceState(dsName):
    serverRuntime()
    objArray = jarray.array([], java.lang.Object)
    strArray = jarray.array([], java.lang.String)
    cd('JDBCServiceRuntime/AdminServer/JDBCDataSourceRuntimeMBeans/' + dsName)
    checkDS = invoke('testPool',objArray,strArray)
    if (checkDS == None):
        status = "OK"
    else:
        status = "Failed - " + checkDS
    serverConfig()
    return status

def getOracleDB(dsURL):
    hostname = dsURL.split('/')[2].split(':')[0]
    port = dsURL.split('/')[2].split(':')[1]
    try:
        sid = dsURL.split('/')[3]
        isSID = True
    except:
        sid = dsURL.split('/')[2].split(':')[2]
        isSID = False
    return hostname, port, sid, isSID

def getDatasourceInfo(cService):
    allJDBCResources = cmo.getJDBCSystemResources()
    for ds in allJDBCResources:
        dsName = ds.getName()
        dsUser = get("/JDBCSystemResources/"+ dsName +"/Resource/" + dsName + "/JDBCDriverParams/" + dsName + "/Properties/" + dsName + "/Properties/user/Value")
        dsPassword = getPassword(cService, dsName)
        dsStatus = getDatasourceState(dsName)
        dsURL = ds.getJDBCResource().getJDBCDriverParams().getUrl().lower()
        dsDriver = ds.getJDBCResource().getJDBCDriverParams().getDriverName().lower()
        if ("oracle" in dsURL) and ("oracle" in dsDriver):
            host, port, sid, isSID = getOracleDB(dsURL)
        #dsJNDI = dsResource.getJDBCDataSourceParams().getJNDINames()[0]

        printDatasourceInfo(dsName, dsUser, dsPassword, dsStatus, host, port, sid, isSID)

def printDatasourceInfo(dsName, dsUser, dsPassword, dsStatus):
    print "Name:\t\t" + dsName
    print "User:\t\t" + dsUser
    print "Password:\t" + dsPassword
    print "Status:\t\t" + dsStatus
    print "\tHost:\t" + host
    print "\tPort:\t" + port
    if isSID:
        print "\tSID:\t" + sid
    else:
        print "\tService Name:\t" + sid
    print "\n"

def main():
    environment = sys.argv[1]
    domain = sys.argv[2]
    hostUser = 'weblogic'
    hostPass = 'welcome1'

    # you need to provide two parameters, environment and domain
    if environment == '' or domain == '' :
            print 'Please enter two parameters for environment and domain'

    path = "/u01/fmw/soa/user_projects/domains/" + domain + "/security"

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

    connect( hostUser , hostPass , 't3://' + hostIP + ':' + hostPort )

    encryptionService = SerializedSystemIni.getEncryptionService(path)
    cService = ClearOrEncryptedService(encryptionService)

    getDatasourceInfo(cService)
        
    """
        password1 = GeneratePassword()
        db = OracleDB("192.168.254.134",1521,"soadb","rn_test",'\8f(F%hL?y6Hh[BaT]o2Fw\aZ',1)
        db.changePassword(password1.generate_pass())
    """
main()