#!/usr/bin/env python

#
# MansOS web server - main file
#

import os, sys, platform, datetime, cookielib, random
import threading, time, serial, select, socket, cgi, subprocess, struct, signal
import json
from settings import *
from mote import *
from sensor_data import *
from config import *

def isPython3():
    return sys.version_info[0] >= 3

if isPython3():
    from http.server import *
    from socketserver import *
    from urllib.parse import *
else:
    from BaseHTTPServer import *
    from SocketServer import *
    from urlparse import *

isListening = False
listenThread = None

lastUploadCode = ""
lastUploadConfig = ""
lastUploadFile = ""
lastJsonData = ""

isInSubprocess = False
uploadResult = ""

motes = MoteCollection()

htmlDirectory = "html"
sealBlocklyPath = "seal-blockly"

# TODO: this variable should set for each user
#hasWriteAccess = False
# --------------------------------------------
class Session():
    def __init__(self,sma):
        self._sma=sma
        self._end=datetime.datetime.now() + datetime.timedelta(minutes=1)
    def add_sid(self,sid,user):
        self._sid=sid
        self._user=user
    def get_all_data(self):
        temp = {}
        temp["sma"] = self._sma
        temp["end"] = self._end
        try:
            temp["sid"] = self._sid
        except:
            pass
        try:
            temp["user"] = self._user
        except:
            pass
        return temp
    def del_sid(self):
        try:
            del self._sid
            del self._user
        except:
            pass

class Sessions():
    def __init__(self):
        self._sessionList = []
    def is_session(self,sma):
        i=0
        while self._sessionList.__len__() > i:
            if self._sessionList[i]._sma == sma:
                return True
            i +=1
        return False
    def add_session(self,sma):
        self.delete_old()
        self._sessionList.append(Session(sma))
    def get_session(self,sma):
        i=0
        while self._sessionList.__len__() > i:
            if self._sessionList[i]._sma == sma:
                return self._sessionList[i]
            i +=1
        #print("Nav tada sesijas")
        return False
    def delete_old(self):
        i=0
        while self._sessionList.__len__() > i:
            if self._sessionList[i]._end < datetime.datetime.now():
                self._sessionList.pop(i)
            else:
                i+=1
    def set_sma(self,osma,nsma):
        temp = self.get_session(osma)
        if temp:
            if nsma[-1:] == "1":
                temp._end=datetime.datetime.now() + datetime.timedelta(minutes=15)
            else:
                temp._end=datetime.datetime.now() + datetime.timedelta(minutes=1)
            temp._sma=nsma
            return True
        else:
            nsma=nsma[:-1]+"0"
            self.add_session(nsma)
            return False
    def add_sid(self,sma,sid,user):
        i=0
        while self._sessionList.__len__() > i:
            if self._sessionList[i]._sma == sma:
                self._sessionList[i].add_sid(sid,user)
                return
            i+=1
    def get_sid(self,sma):
        pass
    def del_sid(self,sma):
        i=0
        while self._sessionList.__len__() > i:
            if self._sessionList[i]._sma == sma:
                self._sessionList[i].del_sid()
                return
            i+=1
    def get_sessions(self):
        temp = {}
        i=0
        while self._sessionList.__len__() > i:
            temp[i] = self._sessionList[i].get_all_data()
            i+=1
        return temp
        
# --------------------------------------------
class User():
    def __init__(self, userAttributes, data):
        self._attributes = {}
        i=0
        while data.__len__() > i:
            self._attributes[userAttributes[i]] = data[i]
            i+=1
    def set_attributes(self, key, value):
        self._attributes[key] = value
    def get_data(self, key):
        return self._attributes.get(key, None)
    def get_all_data(self):
        return self._attributes
    
class Users():
    def __init__(self, userAttr):
        self._userAttributes = userAttr
        self._userList = []
    def is_attribute(self, attrName):
        i=0
        while self._userAttributes.__len__() > i:
            if self._userAttributes[i] == attrName:
                return True
            i +=1
        return False
    def get_user(self, key, value):
        if not self.is_attribute(key):
            #print("Nav tada pazime")
            return False
        i=0
        while self._userList.__len__() > i:
            if self._userList[i].get_data(key) == value:
                return self._userList[i].get_all_data()
            i +=1
        #print("Nav tada persona")
        return False
    def add_user(self, userData):
        # vajadziga parbaude vai nav jau tads vards
        self._userList.append(User(self._userAttributes, userData))
        return True
    def get_users(self):
        temp = {}
        i=0
        while self._userList.__len__() > i:
            temp[i] = self._userList[i].get_all_data()
            i+=1
        return temp
    def add_attribute(self, attrName, defaultVal):
        if self.is_attribute(attrName):
            return False
        self._userAttributes.append(attrName)
        i=0
        while self._userList.__len__() > i:
            self._userList[i].set_attributes(attrName, defaultVal)
            i+=1
        return True
    def set_attribute(self, user, attrName, value):
        if not self.is_attribute(attrName):
            return False
        tuser = self.get_user("name", user)
        if type(tuser) == dict:
            tuser[attrName] = value
            return True
        return False
    def make_copy(self):
        tstr = "/" + userFile + str(datetime.datetime.now())[:22]
        tstr = tstr.replace(' ','_')
        tstr = tstr.replace(':','-')
        tstr = tstr.replace('.dat','')
        tstr += ".dat"
        #os.rename(userDirectory + "/test.dat",userDirectory + tstr)
        os.rename(userDirectory + "/" + userFile,userDirectory+ "/archives" + tstr)
    def write_in_file(self):
        self.make_copy()
        #f = open(userDirectory + "/test.dat","w")
        f = open(userDirectory + "/" + userFile,"w")
        tstr = ""
        i=0
        while self._userAttributes.__len__() > i:
            tstr += self._userAttributes[i] + " "
            i+=1
        tstr +="\n"
        f.write(tstr)
        i=0
        while self._userList.__len__() > i:
            j=0
            tstr = ""
            while self._userAttributes.__len__() > j:
                tstr += str(self._userList[i].get_data(self._userAttributes[j])) + " "
                j += 1
            tstr +="\n"
            f.write(tstr)
            i += 1
        f.close()

# -------------------------------------
def listenSerial():
    while isListening:
        for m in motes.getMotes():

            length = m.tryRead(binaryToo = configInstance.configMode)
            if length == 0:
                continue

            if configInstance.configMode:
                for c in m.buffer:
                    configInstance.byteRead(c)
                m.buffer = ""
                continue

            while '\n' in m.buffer:
                pos = m.buffer.find('\n')
                if pos != 0:
                    newString = m.buffer[:pos].strip()
                    # print "got", newString
                    moteData.addNewData(newString, m.port.portstr)
                m.buffer = m.buffer[pos + 1:]

        moteData.fixSizes()
        # pause for a bit
        time.sleep(0.01)


def closeAllSerial():
    global listenThread
    global isListening
    isListening = False
    if listenThread:
        listenThread.join()
        listenThread = None
    for m in motes.getMotes():
        m.closeSerial()


def openAllSerial():
    global listenThread
    global isListening
    moteData.reset()
    if isListening: return
    isListening = True
    listenThread = threading.Thread(target = listenSerial)
    listenThread.start()
    for m in motes.getMotes():
        m.tryToOpenSerial(False)


def getMansOSVersion():
    path = settingsInstance.getCfgValue("mansosDirectory")
    result = ""
    try:
        with open(os.path.join(path, "doc/VERSION")) as versionFile:
            result = versionFile.readline().strip()
    except Exception as e:
        print(e)
    return result

# --------------------------------------------

class HttpServerHandler(BaseHTTPRequestHandler):
    server_version = 'MansOS/' + getMansOSVersion() + ' Web Server'
    protocol_version = 'HTTP/1.1' # 'HTTP/1.0' is the default, but we want chunked encoding

    def writeChunk(self, buffer):
        if self.wfile == None: return
        if self.wfile._sock == None: return
        self.wfile.write("{:x}\r\n".format(len(buffer)))
        self.wfile.write(buffer)
        self.wfile.write("\r\n")

    def writeFinalChunk(self):
        self.wfile.write("0\r\n")
        self.wfile.write("\r\n")

    def serveSession(self, qs):
        with open(htmlDirectory + "/session.html", "r") as f:
            contents = f.read()
            tsma=str(random.randint(100000, 999999))
            if "sma" in qs:
                tsma=tsma+qs["sma"][0][-1:]
                if "log" in qs:
                    if qs["log"] == "in":
                        tsid=str(random.randint(1000000000, 9999999999))
                        tsma=tsma[:-1]+"1"
                        allSessions.add_sid(qs["sma"][0],tsid,allUsers.get_user("name", qs["user"][0]))
                        contents = contents.replace("/*?LOGIN", "")
                        contents = contents.replace("%SID%", tsid)
                    elif qs["log"] == "out":
                        tsma=tsma[:-1]+"0"
                        contents = contents.replace("/*?DEL", "")
                        allSessions.del_sid(qs["sma"][0])
                if not allSessions.set_sma(qs["sma"][0],tsma):
                    tsma= tsma[:-1]+"0"
                    contents = contents.replace("/*?DEL", "")
                    allSessions.del_sid(qs["sma"][0])
            else:
                tsma=tsma+"0"
                allSessions.add_session(tsma)
                contents = contents.replace("/*?DEL", "")
                #delsid
            #nolasa vai nav Msma37
            #ja nav izveido jaunu
            #ja ir nomaina sma
            # Msma37
            contents = contents.replace("%RAND%", tsma)
            if not "sma" in qs:
                qs["sma"] = []
                qs["sma"].append(tsma)
            else:
                qs["sma"][0] = tsma
            print("allSessions = ")
            print(allSessions.get_sessions())
            self.writeChunk(contents)
            
    def haveAccess(self, qs):
        if "sma" in qs and "1" in qs["sma"][0][-1:]:
            try:
                if allSessions.get_session(qs["sma"][0])._user["hasWriteAccess"] == "True":
                    return True
            except:
                return False
        return False
    
    def serveHeader(self, name, qs, isGeneric = True, includeBodyStart = True, replaceValues = None):
        self.headerIsServed = True
        if name == "default":
            pagetitle = ""
        else:
            pagetitle = " &#8211; " + toTitleCase(name)

        with open(htmlDirectory + "/header.html", "r") as f:
            contents = f.read()
            contents = contents.replace("%PAGETITLE%", pagetitle)
            self.writeChunk(contents)
        try:
            with open(htmlDirectory + "/" + name + ".header.html", "r") as f:
                contents = f.read()
                if replaceValues:
                    for v in replaceValues:
                        contents = contents.replace("%" + v + "%", replaceValues[v])
                self.writeChunk(contents)
        except:
            pass
            
        if includeBodyStart:
            
            try:
                if not "no" in qs:
                     self.serveSession(qs)
            except Exception as e:
                print("Error Session not served!:")
                print(e)
                self.writeChunk('</head>\n<body>')
                
            suffix = "generic" if isGeneric else "mote"
            
            with open(htmlDirectory + "/bodystart-" + suffix + ".html", "r") as f:
                contents = f.read()
                if replaceValues:
                    for v in replaceValues:
                        contents = contents.replace("%" + v + "%", replaceValues[v])
                # page title
                contents = contents.replace("%PAGETITLE%", pagetitle)
                ###action = "Release" if hasWriteAccess else "Get"
                disabled = "" if self.haveAccess(qs) else 'disabled="disabled" '                '''
                if self.haveAccess(qs):
                    action = "Release" if hasWriteAccess else "Get"
                else:
                    action = "Get"
                # read / write access
                contents = contents.replace("%ACCESSACTION%", action)
                '''
                contents = contents.replace("%DISABLED%", disabled)
                # login/logout
                log = "Logout" if "sma" in qs and "1" in qs["sma"][0][-1:] else "Login"
                contents = contents.replace("%LOG%", log)
                # this page (for form)
                contents = contents.replace("%THISPAGE%", name)
                self.writeChunk(contents)

    def serveBody(self, name, qs = {'sma': ['0000000'],}, replaceValues = None):
        ###disabled = "" if hasWriteAccess else 'disabled="disabled" '
        if self.haveAccess(qs):
            disabled = ""# if hasWriteAccess else 'disabled="disabled" '
        else:
            disabled = 'disabled="disabled" '
        with open(htmlDirectory + "/" + name + ".html", "r") as f:
            contents = f.read()
            if replaceValues:
                for v in replaceValues:
                    contents = contents.replace("%" + v + "%", replaceValues[v])
            contents = contents.replace("%DISABLED%", disabled)
            self.writeChunk(contents)


    def serveMotes(self, action, qs, isPost):
        text = ''
        if isPost:
            text += '<form method="post" enctype="multipart/form-data" action="' + toCamelCase(action) + '">'
        else:
            text += '<form action="' + toCamelCase(action) + '">'
        self.writeChunk(text)

        if self.haveAccess(qs):
            disabled = "" #if hasWriteAccess else 'disabled="disabled" '
        else:
            disabled = 'disabled="disabled" '

        c = ""
        i = 0
        for m in motes.getMotes():
            name = "mote" + str(i)

            if name in qs:
                m.isSelected = qs[name][0] == 'on'
            elif "action" in qs:
                m.isSelected = False

            checked = ' checked="checked"' if m.isSelected else ""

            c += '<div class="mote"><strong>Mote: </strong>' + m.portName
            c += ' (<strong>Platform: </strong>' + m.platform + ') '
            c += ' <input type="checkbox" title="Select the mote" name="' + name + '"'
            c += checked + ' ' + disabled + '/>' + action + '</div>\n'
            i += 1

        # remember which motes were selected and which were not
        motes.storeSelected()

        if c:
            c = '<div class="motes1">\nDirectly attached motes:\n<br/>\n' + c + '</div>\n'
            self.writeChunk(c)

        self.writeChunk('<div class="form">\n')


    def serveMoteMotes(self, qs):
        if motes.isEmpty():
            self.serveError("No motes connected!")
            return

        text = '<form action="config"><div class="motes2">\n'
        text += 'Directly attached motes:<br/>\n'

        if self.haveAccess(qs):
            disabled = "" #if hasWriteAccess else 'disabled="disabled" '
        else:
            disabled = 'disabled="disabled" '

        i = 0
        for m in motes.getMotes():
            name = "mote" + str(i)
            text += '<div class="mote"><strong>Mote: </strong>' + m.portName
            text += ' <input type="hidden" name="sma" class="Msma37" value="0"> '
            text += ' <input type="submit" name="' + name + '_cfg" title="Get/set mote\'s configuration (e.g. sensor reading periods)" value="Configuration..." ' + disabled + '/>\n'
            text += ' <input type="submit" name="' + name + '_files" title="View files on mote\'s filesystem" value="Files..." ' + disabled + '/>\n'
            text += ' Platform: <select name="sel_' + name + '" ' + disabled + ' title="Select the mote\'s platform: determines the list of sensors the mote has. Also has effect on code compilation and uploading">\n'
            for platform in supportedPlatforms:
                selected = ' selected="selected"' if platform == m.platform else ''
                text += '  <option value="' + platform + '"' + selected + '>' + platform + '</option>\n'
            text += ' </select>\n'
            text += '</div>\n'

            i += 1

        text += '<input type="submit" name="platform_set" value="Update platforms" ' + disabled + '/><br/>\n'
        text += "</div></form>"
        self.writeChunk(text)


    def serveFooter(self):
        with open(htmlDirectory + "/footer.html", "r") as f:
            contents = f.read()
            self.writeChunk(contents)
        self.writeFinalChunk()

    def sendDefaultHeaders(self):
        self.send_header('Content-Type', 'text/html')
        # use chunked transfer encoding (to be able to send additional chunks 'later')
        self.send_header('Transfer-Encoding', 'chunked')
        # disable caching
        self.send_header('Cache-Control', 'no-store');

    def serveFile(self, filename):
        mimetype = 'text/html'
        if filename[-4:] == '.css': mimetype = 'text/css'
        elif filename[-3:] == '.js': mimetype = 'application/javascript'
        elif filename[-4:] == '.png': mimetype = 'image/png'
        elif filename[-4:] == '.gif': mimetype = 'image/gif'
        elif filename[-4:] == '.jpg': mimetype = 'image/jpg'
        elif filename[-4:] == '.tif': mimetype = 'image/tif'

        try:
            with open(filename, "rb") as f:
                contents = f.read()
                self.send_response(200)
                self.send_header('Content-Type', mimetype)
                self.send_header('Content-Length', str(len(contents)))
                self.end_headers()
                self.wfile.write(contents)
                f.close()
        except:
            print("problem with file " + filename + "\n")
            self.serve404Error(filename, {})
    def getCookie(self):
        for k, v in os.environ.items():
            print (k, "=", v)

    def serve404Error(self, path, qs):
        self.send_response(404)
        self.sendDefaultHeaders()
        self.end_headers()
        qs["no"] = "no"
        self.serveHeader("404", qs)
        self.writeChunk("<strong>Path " + path + " not found on the server</strong>\n")
        self.serveFooter()

    def serveError(self, message):
        if not self.headerIsServed:
            self.serveHeader("error",{})
        self.writeChunk("\n<strong>Error: " + message + "</strong></div>\n")
        self.serveFooter()

    def serveDefault(self, qs):
        self.send_response(200)
        self.sendDefaultHeaders()
        self.end_headers()
        self.serveHeader("default", qs)
        self.serveBody("default", qs)
        self.serveFooter()

    def serveLogin(self, qs):
        #self.getCookie()
        #print(qs)
        qs["log"] = ""
        changes = {}
        changes["FAIL"] = 'hidden'
        if "sma" in qs and "1" in qs["sma"][0][-1:]:
            qs["log"] = "out"
            self.serveDefault(qs)
            return
        elif "password" in qs and "user" in qs:
            tuser=allUsers.get_user("name", qs["user"][0])
            if tuser and tuser["password"] == qs["password"][0]:
                qs["log"] = "in"
                print(qs["user"][0])
                print("had loged in")
                self.serveDefault(qs)
                return
            else:
                changes["FAIL"]=""
        self.send_response(200)
        self.sendDefaultHeaders()
        self.end_headers()
        #if "accessType" in qs:
            #self.handleGenericQS(qs)
        self.serveHeader("login", qs)
        self.serveBody("login", qs, changes)
        self.serveFooter()

    def serveMoteSelect(self, qs):
        self.send_response(200)
        self.sendDefaultHeaders()
        self.end_headers()
        self.serveHeader("motes", qs)
        self.serveMoteMotes(qs)
        self.serveFooter()

    def serveConfig(self, qs):
        self.send_response(200)
        self.sendDefaultHeaders()
        self.end_headers()

        if not hasWriteAccess:
            self.serveError("You are not in write access mode!")
            return

        #self.handleGenericQS(qs)

        if "platform_set" in qs:
            i = 0
            for m in motes.getMotes():
                motename = "sel_mote" + str(i)
                if motename in qs:
                    m.platform = qs[motename][0]
                i += 1
            motes.storeSelected()

            text = '<strong>Mote platforms updated!</strong></div>\n'
            self.serveHeader("config", qs, isGeneric = True)
            self.writeChunk(text)
            self.serveFooter()
            return

        openAllSerial()

        moteIndex = None
        filesRequired = False
        for s in qs:
            if s[:4] == "mote":
                pair = s[4:].split('_')
                try:
                    moteIndex = int(pair[0])
                    filesRequired = pair[1] == "files"
                except:
                    pass
                break

        if moteIndex is None or moteIndex >= len(motes.getMotes()):
            self.serveError("Config page requested, but mote not specified!")
            return

        platform = None
        dropdownName = "sel_mote" + str(moteIndex)
        if dropdownName in qs:
            platform = qs[dropdownName][0]

        if platform not in supportedPlatforms:
            self.serveError("Config page requested, but platform not specified or unknown!")
            return

        moteidQS = "?sel_mote" + str(moteIndex) + "=" + platform + "&" + "mote" + str(moteIndex)
        self.serveHeader("config", qs, isGeneric = False,
                         replaceValues = {"MOTEID_CONFIG" : moteidQS + "_cfg=1",
                          "MOTEID_FILES" : moteidQS + "_files=1"})

        configInstance.setMote(motes.getMote(moteIndex), platform)

        (errmsg, ok) = configInstance.updateConfigValues(qs)
        if not ok:
            self.serveError(errmsg)
            return

        # fill config values from the mote / send new values to the mote
        if "get" in qs:
            reply = configInstance.getConfigValues()
            #self.writeChunk(reply)
        elif "set" in qs:
            reply = configInstance.setConfigValues()
            #self.writeChunk(reply)

        if filesRequired:
            if "filename" in qs:
                (text, ok) = configInstance.getFileContentsHTML(qs)
            else:
                (text, ok) = configInstance.getFileListHTML(moteIndex)
        else:
            (text, ok) = configInstance.getConfigHTML()
        if not ok:
            self.serveError(text)
            return
        self.writeChunk(text)
        self.serveFooter()

    def serveGraphs(self, qs):
        self.send_response(200)
        self.sendDefaultHeaders()
        self.end_headers()
        self.serveHeader("graph", qs)
        self.serveMotes("Listen", qs, False)

        if "action" in qs:
            if qs["action"][0] == "Start":
                if not motes.anySelected():
                    self.serveError("No motes selected!")
                    return
                if isListening:
                    self.serveError("Already listening!")
                    return
                openAllSerial()
            else:
                closeAllSerial()

        action = "Stop" if isListening else "Start"
        self.serveBody("graph", qs, {"MOTE_ACTION": action})
        self.serveFooter()

    def serveListen(self, qs):
        self.send_response(200)
        self.sendDefaultHeaders()
        self.end_headers()
        self.serveHeader("listen", qs)
        self.serveMotes("Listen", qs, False)

        if "action" in qs:
            if qs["action"][0] == "Start":
                if not motes.anySelected():
                    self.serveError("No motes selected!")
                    return
                if isListening:
                    self.serveError("Already listening!")
                    return
                openAllSerial()
            else:
                closeAllSerial()

        txt = ""
        for line in moteData.listenTxt:
            txt += line + "<br/>"

        action = "Stop" if isListening else "Start"

        if "dataFile" in qs:
            dataFilename = qs["dataFile"][0]
            if len(dataFilename) and dataFilename.find(".") == -1:
                dataFilename += ".csv"
        else:
            dataFilename = settingsInstance.getCfgValue("saveToFilename")

        saveMultipleFiles = settingsInstance.getCfgValueAsBool("saveMultipleFiles")
        saveProcessedData = settingsInstance.getCfgValueAsBool("saveProcessedData")
        if "dataType" in qs:
            saveProcessedData = not qs["dataType"][0] == "raw"
            saveMultipleFiles = qs["dataType"][0] == "mprocessed"

        rawdataChecked = not saveProcessedData
        sprocessedChecked = saveProcessedData and not saveMultipleFiles
        mprocessedChecked = saveProcessedData and saveMultipleFiles

        settingsInstance.setCfgValue("saveToFilename", dataFilename)
        settingsInstance.setCfgValue("saveProcessedData", bool(saveProcessedData))
        settingsInstance.setCfgValue("saveMultipleFiles", bool(saveMultipleFiles))
        settingsInstance.save()

        self.serveBody("listen", qs,
                       {"LISTEN_TXT" : txt,
                        "MOTE_ACTION": action,
                        "DATA_FILENAME" : dataFilename,
                        "RAWDATA_CHECKED" : 'checked="checked"' if rawdataChecked else "",
                        "SPROCDATA_CHECKED" : 'checked="checked"' if sprocessedChecked else "",
                        "MPROCDATA_CHECKED" : 'checked="checked"' if mprocessedChecked else ""})
        self.serveFooter()

    def serveUpload(self, qs):
        self.send_response(200)
        self.sendDefaultHeaders()
        self.end_headers()
        self.serveHeader("upload", qs)
        self.serveMotes("Upload", qs, True)
        isSealCode = settingsInstance.getCfgValueAsInt("isSealCode")
        isSlow = settingsInstance.getCfgValueAsInt("slowUpload")
        self.serveBody("upload", qs,
                       {"CCODE_CHECKED": 'checked="checked"' if not isSealCode else "",
                        "SEALCODE_CHECKED" : 'checked="checked"' if isSealCode else "",
                        "UPLOAD_CODE" : lastUploadCode,
                        "UPLOAD_CONFIG" : lastUploadConfig,
                        "UPLOAD_FILENAME": lastUploadFile,
                        "SLOW_CHECKED" : 'checked="checked"' if isSlow else ""})
        self.serveFooter()

    def uploadCallback(self, line):
        global uploadResult
        uploadResult += line
        return True

    def serveUploadResult(self, qs):
        global uploadResult
        global isInSubprocess
        isInSubprocess = True
        try:
            self.send_response(200)
            self.sendDefaultHeaders()
            self.end_headers()
            self.serveHeader("upload", qs)
            self.writeChunk("Upload result:<br/><pre>\n")
            while isInSubprocess or uploadResult:
                if uploadResult:
                    self.writeChunk(uploadResult)
                    uploadResult = ""
                else:
                    time.sleep(0.001)
            self.writeChunk("</pre>\n")
            self.writeChunk('<button type="button" onclick="window.open(\'\', \'_self\', \'\'); window.close();">OK</button>')
            self.serveFooter()
        except:
            raise
        finally:
            uploadResult = ""

    def serveBlockly(self, qs):
        self.send_response(200)
        self.sendDefaultHeaders()
        self.end_headers()
        self.serveHeader("blockly", qs)
        self.serveBody("blockly", qs)
        self.serveFooter()

    def serveSealFrame(self, qs):
        self.send_response(200)
        self.sendDefaultHeaders()
        self.end_headers()
        path = os.path.join(sealBlocklyPath, "index.html")
        with open(path) as f:
            self.writeChunk(f.read())
        self.writeFinalChunk()

    # Dummy, have to respond somehow, so javascript knows we are here
    def serveSync(self):
        self.send_response(200)
        self.sendDefaultHeaders()
        self.end_headers()
        if hasWriteAccess:
            self.writeChunk("writeAccess=True")
        self.writeFinalChunk()

    def serveGraphsData(self, qs):
        global lastJsonData

        self.send_response(200)
        self.sendDefaultHeaders()
        self.end_headers()

        self.end_headers()

        if lastJsonData and not isListening:
            self.writeChunk(lastJsonData)
            self.writeFinalChunk()
            return

# FIXME:
#        if sensorData.hasData():
#            jsonData = json.JSONEncoder().encode(sensorData.getData())
#        else:
#            jsonData = ""
        jsonData = ""

        lastJsonData = jsonData
        self.writeChunk(jsonData)
        self.writeFinalChunk()

    def serveListenData(self, qs):
        self.send_response(200)
        self.sendDefaultHeaders()
        self.end_headers()
        text = ""
        for line in moteData.listenTxt:
            text += line + "<br/>"
        if text:
            self.writeChunk(text)
        self.writeFinalChunk()

    def do_GET(self):
        self.headerIsServed = False

        o = urlparse(self.path)
        qs = parse_qs(o.query)

        if o.path == "/" or o.path == "/default":
            self.serveDefault(qs)
        elif o.path == "/motes":
            self.serveMoteSelect(qs)
        elif o.path == "/config":
            self.serveConfig(qs)
        elif o.path == "/graph":
            self.serveGraphs(qs)
        elif o.path == "/graph-data":
            self.serveGraphsData(qs)
        elif o.path == "/upload":
            self.serveUpload(qs)
        elif o.path == "/login":
            self.serveLogin(qs)
        elif o.path == "/upload-result":
            self.serveUploadResult(qs)
        elif o.path == "/listen":
            self.serveListen(qs)
        elif o.path == "/listen-data":
            self.serveListenData(qs)
        elif o.path == "/blockly":
            self.serveBlockly(qs)
        elif o.path == "/seal-frame":
            self.serveSealFrame(qs)
        elif o.path[:13] == "/seal-blockly":
            self.serveFile(os.path.join(sealBlocklyPath, o.path[13:]))
        elif o.path == "/sync":
            self.serveSync()
        elif o.path == "/code":
            # qs['src'] contains SEAL-Blockly code
            code = qs.get('src')[0] if "src" in qs else ""
            config = qs.get('config')[0] if "config" in qs else ""
            self.compileAndUpload(code, config, None, True)
            self.serveSync()
        elif o.path[-4:] == ".css":
            self.serveFile(htmlDirectory + o.path)
        elif o.path[-4:] == ".png" or o.path[-4:] == ".jpg" or o.path[-4:] == ".gif" or o.path[-4:] == ".tif":
            self.serveFile(htmlDirectory + "/img/" + o.path)
        else:
            self.serve404Error(o.path, qs)

    def compileAndUpload(self, code, config, fileContents, isSEAL):
        global lastUploadCode
        global lastUploadConfig
        global lastUploadFile

        print "code=", code

        retcode = 0
        if not os.path.exists("build"):
            os.mkdir("build")
        # TODO FIXME: should do this in a new thread!
        isInSubprocess = True
        os.chdir("build")

        if fileContents:
            lastUploadFile = form["file"].filename

            filename = "tmp-file.ihex"
            with open(filename, "w") as outFile:
                outFile.write(fileContents)
                outFile.close()

            closeAllSerial()
            for m in motes.getMotes():
                r = m.tryToUpload(self, filename)
                if r != 0: retcode = r

        elif code:
            lastUploadCode = code

            filename = "main."
            filename += "sl" if isSEAL else "c"
            with open(filename, "w") as outFile:
                outFile.write(code)
                outFile.close()

            with open("config", "w") as outFile:
                if config is None:
                    config = ""
                outFile.write(config)
                outFile.close()

            with open("Makefile", "w") as outFile:
                if isSEAL:
                    outFile.write("SEAL_SOURCES = main.sl\n")
                else:
                    outFile.write("SOURCES = main.c\n")
                outFile.write("APPMOD = App\n")
                outFile.write("PROJDIR = $(CURDIR)\n")
                outFile.write("ifndef MOSROOT\n")
                mansosPath = settingsInstance.getCfgValue("mansosDirectory")
                if not os.path.isabs(mansosPath):
                    # one level up - because we are in build directory
                    mansosPath = os.path.join(mansosPath, "..")
                outFile.write("  MOSROOT = " + mansosPath + "\n")
                outFile.write("endif\n")
                outFile.write("include ${MOSROOT}/mos/make/Makefile\n")
                outFile.close()

            closeAllSerial()
            for m in motes.getMotes():
                r = m.tryToCompileAndUpload(self, filename)
                if r != 0 and m.port:
                    retcode = r

        os.chdir("..")
        isInSubprocess = False
        return retcode

    def do_POST(self):
        global lastUploadCode
        global lastUploadConfig
        global lastUploadFile
        global isInSubprocess
        self.headerIsServed = False

        if not hasWriteAccess:
            self.serveError("You are not in write access mode!")
            return

        # Parse the form data posted
        form = cgi.FieldStorage(
            fp = self.rfile,
            headers = self.headers,
            environ = {'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
                     })

        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Transfer-Encoding', 'chunked')
        self.end_headers()

        file_data = None

        isSEAL = False
        if "compile" in form:
            if "language" in form:
                isSEAL = form["language"].value.strip() == "SEAL"
            settingsInstance.setCfgValue("isSealCode", isSEAL)

        if "slow" in form:
            slow = form["slow"].value == "on"
        else:
            slow = False
        settingsInstance.setCfgValue("slowUpload", slow)
        settingsInstance.save()

        if "code" in form.keys():
            code = form["code"].value
        else:
            code = None

        if "file" in form.keys():
            fileContents = form["file"].file.read()
        else:
            fileContents = None

        # check if what to upload is provided
        if not fileContents and not code:
            self.serveHeader("upload", {})
            self.serveError("Neither filename nor code specified!")
            return

        i = 0
        for m in motes.getMotes():
            name = "mote" + str(i)
            if name in form:
                isChecked = form[name].value == "on"
            else:
                isChecked = False

            if isChecked:
                m.isSelected = True
            else:
                m.isSelected = False
            i += 1

        # remember which motes were selected and which not
        motes.storeSelected()
        # check if any motes are selected
        if not motes.anySelected():
            self.serveHeader("upload", {})
            self.serveError("No motes selected!")
            return

        config = ""
        if "config" in form.keys():
            lastUploadConfig = form["config"].value
            config = lastUploadConfig
            outFile.write(lastUploadConfig)
        if slow:
            config += "\nSLOW_UPLOAD=y\n"

        retcode = self.compileAndUpload(code, config, fileContents, isSEAL)

        self.serveHeader("upload", qs)
        self.serveMotes("Upload", {}, True)
        if retcode == 0:
            self.writeChunk("<strong>Upload done!</strong></div>")
        else:
            self.writeChunk("<strong>Upload failed!</strong></div>")
        self.serveFooter()
        motes.closeAll()


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    # Overrides BaseServer function to get better control over interrupts
    def serve_forever(self, poll_interval = 0.5):
        """Handle one request at a time until shutdown.

        Polls for shutdown every poll_interval seconds. Ignores
        self.timeout. If you need to do periodic tasks, do them in
        another thread.
        """
        self._BaseServer__is_shut_down.clear()
        try:
            while not self._BaseServer__shutdown_request:
                # XXX: Consider using another file descriptor or
                # connecting to the socket to wake this up instead of
                # polling. Polling reduces our responsiveness to a
                # shutdown request and wastes cpu at all other times.
                r, w, e = select.select([self], [], [], poll_interval)
                if self in r:
                    self._handle_request_noblock()
        finally:
            self._BaseServer__shutdown_request = False
            self._BaseServer__is_shut_down.set()
            # kill the process to make sure it exits
            os.kill(os.getpid(), signal.SIGKILL)

# --------------------------------------------

def initalizeConfig():
    global htmlDirectory
    global dataDirectory
    global sealBlocklyPath
    global allUsers
    global allSessions
    global userFile
    global userDirectory

    allSessions = Sessions()

    htmlDirectory = os.path.abspath(settingsInstance.getCfgValue("htmlDirectory"))
    dataDirectory = os.path.abspath(settingsInstance.getCfgValue("dataDirectory"))
    if not os.path.exists(dataDirectory):
        os.makedirs(dataDirectory)
    sealBlocklyPath = os.path.abspath(settingsInstance.getCfgValue("sealBlocklyDirectory"))

    userDirectory = "user" # Jaliek konfiga
    if not os.path.exists(userDirectory):
        os.makedirs(userDirectory)
    userFile = "user.dat" # Jaieliek konfiga
    if not os.path.exists(userDirectory + "/" + userFile):
        uf = open(userDirectory + "/" + userFile,"w")
        uf.write("name password email theme hasWriteAccess\n") #ari vajadzetu no konfiguracijas
        uf.write("admin admin none 0 True\n")
    uf = open(userDirectory + "/" + userFile,"r")
    i = False
    for line in uf:
         if not i:
             i = True
             allUsers = Users(line.split())
         else:
             allUsers.add_user(line.split())
    uf.close()

def main():
    try:
        initalizeConfig()
        port = settingsInstance.getCfgValueAsInt("port", HTTP_SERVER_PORT)
        server = ThreadingHTTPServer(('', port), HttpServerHandler)
        motes.addAll()
        time.sleep(1)
        print("<http-server>: started, listening to TCP port {}, serial baudrate {}".format(port,
              settingsInstance.getCfgValueAsInt("baudrate", SERIAL_BAUDRATE)))
        server.serve_forever()
    except Exception as e:
        print("<http-server>: exception occurred:")
        print(e)
        return 1

if __name__ == '__main__':
    main()
