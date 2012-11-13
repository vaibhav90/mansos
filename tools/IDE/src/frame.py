#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2008-2012 the MansOS team. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#  * Redistributions of source code must retain the above copyright notice,
#    this list of  conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

import os
import wx
from stat import S_ISDIR
from wx.lib.agw import aui
from time import time
from subprocess import Popen
import webbrowser

from upload_module import UploadModule
from globals import * #@UnusedWildImport

class Frame(wx.Frame):
    def __init__(self, parent, title, size, pos, API):
        super(Frame, self).__init__(parent, wx.ID_ANY, title, size = size, pos = pos)
        # Get path, here must use only file name, __file__ sometimes contains more than that
        self.path = os.path.dirname(os.path.realpath(os.path.split(__file__)[1]))
        self.API = API
        self.API.path = self.path
        self.lastPanel = None
        self.auiManager = aui.AuiManager()
        self.loadPositioning()
        self.exitCalled = False
        self.blocklyToolVisible = False

        # Just a shorter name
        self.tr = self.API.tr
        self.toolbar = None
        self.menubar = None
        self.examples = dict()
        self.initUI()
        self.SetBackgroundColour("white")
        flag = aui.AUI_MGR_ALLOW_ACTIVE_PANE | \
        aui.AUI_MGR_AUTONB_NO_CAPTION | aui.AUI_MGR_SMOOTH_DOCKING | \
        aui.AUI_MGR_TRANSPARENT_HINT | aui.AUI_NB_CLOSE_ON_TAB_LEFT | \
        aui.AUI_MGR_AERO_DOCKING_GUIDES | aui.AUI_MGR_TRANSPARENT_DRAG
        self.auiManager.SetAGWFlags(self.auiManager.GetAGWFlags() ^ flag)
        self.auiManager.SetAutoNotebookStyle(aui.AUI_NB_TOP | aui.AUI_NB_SMART_TABS | aui.AUI_NB_CLOSE_ON_ALL_TABS)
        self.auiManager.SetManagedWindow(self)

        self.API.onExit.append(self.Close)

        self.API.tabManager.Reparent(self)
        self.API.editPanel.Reparent(self)
        self.API.blockly.Reparent(self)
        self.API.listenModules[0].Reparent(self)
        self.API.infoArea.Reparent(self)

        mainPane = (aui.AuiPaneInfo().CenterPane().Name("mainPane").
                Caption("Editors").CaptionVisible(False).
                BestSize(wx.Size(600, 400)))
        self.auiManager.AddPane(self.API.tabManager, mainPane)

        self.infoPane = (aui.AuiPaneInfo().CaptionVisible(True).
                BestSize(wx.Size(500, 150)).Bottom().
                CloseButton(False).MaximizeButton(True).MinimizeButton(True))

        self.auiManager.AddPane(self.API.infoArea, self.infoPane.Caption("Info").Name("infoPane"))

        self.layoutListenPane(self.API.listenModules[0], "Listen module 1", False)
        self.layoutEditPane()
        self.layoutBlocklyPane()

        self.auiManager.Update()
        self.Bind(wx.EVT_CLOSE, self.OnQuit)
        self.auiManager.ShowPane(self.API.infoArea, True)

    def initUI(self):
        self.generateMenu()
        # Check if we need to update existing toolbar(for rerun)
        if self.toolbar == None:
            self.toolbar = self.CreateToolBar()
            self.toolbar.SetToolBitmapSize((32, 32))
        else:
            self.toolbar.ClearTools()

        # Note that all icons must be 32x32, so they look good :)
        self.toolbar.AddLabelTool(wx.ID_NEW, self.tr('New'),
                                wx.Bitmap(self.path + '/src/Icons/new.png'),
                                shortHelp = self.tr('New'))
        self.toolbar.AddSeparator()
        self.toolbar.AddLabelTool(wx.ID_OPEN, self.tr('Open'),
                                wx.Bitmap(self.path + '/src/Icons/open.png'),
                                shortHelp = self.tr('Open'))
        self.toolbar.AddLabelTool(wx.ID_SAVE, self.tr('Save'),
                                wx.Bitmap(self.path + '/src/Icons/save.png'),
                                shortHelp = self.tr('Save'))
        self.toolbar.AddSeparator()
        addStatementTool = self.toolbar.AddLabelTool(wx.ID_ADD, self.tr('Add statement'),
                                wx.Bitmap(self.path + '/src/Icons/add_statement.png'),
                                shortHelp = self.tr('Add statement'))
        # Used ID_APPLY for identification, hope nothing else uses it
        addConditionTool = self.toolbar.AddLabelTool(wx.ID_APPLY, self.tr('Add condition'),
                                wx.Bitmap(self.path + '/src/Icons/add_condition.png'),
                                shortHelp = self.tr('Add condition'))
        #self.toolbar.AddSeparator()
        #addBlocklyTool = self.toolbar.AddLabelTool(wx.ID_MORE, self.tr('Open Seal-Blockly editor'),
        #                        wx.Bitmap(self.path + '/src/Icons/Seal_blockly.png'),
        #                        shortHelp = self.tr('Open Seal-Blockly editor'))
        self.toolbar.AddSeparator()
        compileTool = self.toolbar.AddLabelTool(wx.ID_PREVIEW, self.tr('Compile'),
                                wx.Bitmap(self.path + '/src/Icons/compile.png'),
                                shortHelp = self.tr('Compile'))
        uplTool = self.toolbar.AddLabelTool(wx.ID_PREVIEW_GOTO, self.tr('Upload'),
                                wx.Bitmap(self.path + '/src/Icons/upload.png'),
                                shortHelp = self.tr('Upload'))
        outputTool = self.toolbar.AddLabelTool(wx.ID_PREVIEW_ZOOM, self.tr('Configure upload and compile'),
                                wx.Bitmap(self.path + '/src/Icons/read.png'),
                                shortHelp = self.tr('Configure upload and compile'))
        listenTool = self.toolbar.AddCheckLabelTool(wx.ID_HOME, self.tr('Listen node\'s output'),
                                wx.Bitmap(self.path + '/src/Icons/listen.png'),
                                shortHelp = self.tr('Listen node\'s output'))
        self.toolbar.AddSeparator()
        self.toolbar.AddLabelTool(wx.ID_EXIT, self.tr('Exit'),
                                wx.Bitmap(self.path + '/src/Icons/exit.png'),
                                shortHelp = self.tr('Exit'))
        self.toolbar.Realize()

        # Second bind to toolbar, but only items with ID_ANY, because all
        # defined ID already binded from menu, weird side effect.
        self.Bind(wx.EVT_TOOL, self.OnCompile, compileTool)
        self.Bind(wx.EVT_TOOL, self.OnUpload, uplTool)
        self.Bind(wx.EVT_TOOL, self.OnOutput, outputTool)
        self.Bind(wx.EVT_TOOL, self.OnAddStatement, addStatementTool)
        self.Bind(wx.EVT_TOOL, self.OnAddCondition, addConditionTool)
        self.Bind(wx.EVT_TOOL, self.OnStartListening, listenTool)

    def addExampleMenuItems(self, subMenu, path, maxDepth):
        dirList = os.listdir(path)
        dirList.sort()
        hasAny = False
        for dirName in dirList:
            if dirName[0] == '.': continue
            pathName = os.path.join(path, dirName)
            mode = os.stat(pathName).st_mode
            if not S_ISDIR(mode): continue
            # it's a directory; process it
            dirMenu = wx.Menu()
            # test whether it has a Makefile in it
            if os.path.isfile(os.path.join(pathName, 'Makefile')):
                # append the name of this example
                ex = subMenu.Append(wx.ID_ANY, dirName, pathName)
                # save this id/path combination, to be used in callback code
                self.examples[ex.GetId()] = pathName
                self.Bind(wx.EVT_MENU, self.OnOpenExample, ex)
                hasAny = True
            elif maxDepth:
                # recursive call
                if self.addExampleMenuItems(dirMenu, pathName, maxDepth - 1):
                    hasAny = True
                    subMenu.AppendMenu(wx.ID_ANY, dirName, dirMenu)
        return hasAny

    def generateMenu(self):
        fileMenu = wx.Menu()
        new = fileMenu.Append(wx.ID_NEW, '&' + self.tr('New') + '\tCtrl+N',
                              self.tr('Create empty document'))
        open_ = fileMenu.Append(wx.ID_OPEN, '&' + self.tr('Open') + '\tCtrl+O',
                              self.tr('Open document'))
        save = fileMenu.Append(wx.ID_SAVE, '&' + self.tr('Save') + '\tCtrl+S',
                              self.tr('Save document'))
        saveAs = fileMenu.Append(wx.ID_SAVEAS, '&' + self.tr('Save as') + '\t',
                              self.tr('Save document as'))
        upload = fileMenu.Append(wx.ID_ANY, '&' + self.tr('Upload') + '\tCtrl+U',
                              self.tr('Open upload window'))
        recent = wx.Menu()
        fileMenu.AppendMenu(wx.ID_ANY, '&' + self.tr('Recently used files'),
                               recent, self.tr('Recently used files'))
        close = fileMenu.Append(wx.ID_EXIT, '&' + self.tr('Exit') + '\tCtrl+Q',
                              self.tr('Exit application'))

        self.fileHistory = wx.FileHistory(int(self.API.getSetting('recentlyOpenedMaxCount')))
        self.fileHistory.Load(self.API.config)
        self.fileHistory.UseMenu(recent)
        self.fileHistory.AddFilesToMenu()
        self.Bind(wx.EVT_MENU_RANGE, self.on_file_history, id = wx.ID_FILE1, id2 = wx.ID_FILE9)

        # show menu with mansos demo & test applications
        exampleMenu = wx.Menu()
        pathToMansosApps = self.API.path + os.path.normcase("/../../apps/")
        self.addExampleMenuItems(exampleMenu, pathToMansosApps, maxDepth = 2)

        optionMenu = wx.Menu()
        language = wx.Menu()
        self.langs = []
        for i in self.API.translater.translations.keys():
            self.langs.append(language.Append(wx.ID_ANY,
                    self.API.translater.translations[i]['langName'], i, kind = wx.ITEM_RADIO))
            if i == self.API.getSetting("activeLanguage"):
                language.Check(self.langs[-1].GetId(), True)
            self.Bind(wx.EVT_MENU, self.changeLanguage, self.langs[-1])

        optionMenu.AppendMenu(wx.ID_ANY, self.tr('Change language'), language)

        output = optionMenu.Append(wx.ID_ANY, '&' + self.tr('Configure upload and compile') + '\tCtrl+R',
                              self.tr('Open read output window'))
        windowMenu = wx.Menu()
        addMenu = wx.Menu()
        showMenu = wx.Menu()
        windowMenu.AppendMenu(wx.ID_ANY, self.tr('Add window'), addMenu)
        windowMenu.AppendMenu(wx.ID_ANY, self.tr('Show window'), showMenu)
        listen = addMenu.Append(wx.ID_ANY, '&' + self.tr('Add listen window'),
                              self.tr('Add listen window'))
        self.blocklyCheck = showMenu.AppendCheckItem(wx.ID_ANY, '&' + self.tr('Show blockly window'),
                              self.tr('Show blockly window'))
        self.editCheck = showMenu.AppendCheckItem(wx.ID_ANY, '&' + self.tr('Show edit window'),
                              self.tr('Show edit window'))

        helpMenu = wx.Menu()
        sealHelp = helpMenu.Append(wx.ID_ANY, '&' + self.tr('Seal documentation'),
                              self.tr('About'))
        mansosHelp = helpMenu.Append(wx.ID_ANY, '&' + self.tr('MansOS documentation'),
                              self.tr('About'))
        about = helpMenu.Append(wx.ID_ABOUT, '&' + self.tr('About') + '\tCtrl+H',
                              self.tr('About'))
        # Check if we need to update existing menubar(for translate)
        if self.menubar == None:
            self.menubar = wx.MenuBar()
        else:
            for i in range(0, self.menubar.GetMenuCount()):
                self.menubar.Remove(0)

        self.menubar.Append(fileMenu, '&' + self.tr('File'))
        self.menubar.Append(exampleMenu, '&' + self.tr('Examples'))
        self.menubar.Append(optionMenu, '&' + self.tr('Options'))
        self.menubar.Append(windowMenu, '&' + self.tr('Windows'))
        self.menubar.Append(helpMenu, '&' + self.tr('Help'))
        self.SetMenuBar(self.menubar)

        # First bind to menu
        self.Bind(wx.EVT_MENU, self.OnQuit, close)
        self.Bind(wx.EVT_MENU, self.OnOpen, open_)
        self.Bind(wx.EVT_MENU, self.OnSave, save)
        self.Bind(wx.EVT_MENU, self.OnSaveAs, saveAs)
        self.Bind(wx.EVT_MENU, self.OnUpload, upload)
        self.Bind(wx.EVT_MENU, self.OnOutput, output)
        self.Bind(wx.EVT_MENU, self.OnNew, new)
        self.Bind(wx.EVT_MENU, self.OnAbout, about)
        self.Bind(wx.EVT_MENU, self.OnSealHelp, sealHelp)
        self.Bind(wx.EVT_MENU, self.OnMansosHelp, mansosHelp)

        self.Bind(wx.EVT_MENU, self.API.addListenWindow, listen)
        self.Bind(wx.EVT_MENU, self.API.showBlocklyWindow, self.blocklyCheck)
        self.Bind(wx.EVT_MENU, self.API.showEditWindow, self.editCheck)

    def on_file_history(self, event):
            fileNum = event.GetId() - wx.ID_FILE1
            path = self.fileHistory.GetHistoryFile(fileNum)
            self.fileHistory.AddFileToHistory(path)  # move up the list
            self.API.tabManager.addPage(path)

    def OnQuit(self, event):
        # Workaround, because wx.exit calls wx.ON_CLOSE, which is binded to this 
        # function, result is recursive calling of this function.
        # Time used, because cancel on file save dialog makes exit unresponsive.
        if self.exitCalled + 0.5 > time():
            return
        self.API.tabManager.rememberOpenedTabs()
        self.rememberPositioning()
        if self.API.tabManager.onQuitCheck() == True:
            self.exitCalled = time()
            self.API.performExit()
            wx.Exit()

    def OnSave(self, event):
        self.API.tabManager.doPopupSave(None)

    def OnSaveAs(self, event):
        self.API.tabManager.doPopupSaveAs(None)

    def OnCompile(self, event):
        if self.API.tabManager.doPopupSave(None) == True:
            self.API.doCompile()

    def OnUpload(self, event):
        if self.API.tabManager.doPopupSave(None) == True:
            self.API.doUpload()

    def OnOutput(self, event):
        if self.API.tabManager.doPopupSave(None) == True:

            dialog = wx.Dialog(self, wx.ID_ANY, self.tr('Configure upload and compile'),
                style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

            UploadModule(dialog, self.API)
            dialog.Fit()
            dialog.ShowModal()
            dialog.Destroy()

    def OnStartListening(self, event):
        if not self.API.listenModules[0].listening:
            self.auiManager.ShowPane(self.API.listenModules[0], True)
            self.API.listenModules[0].doClear()
        else:
            self.API.listenModules[0].doClear("")

    def checkToggleState(self):
        if self.API.listenModules[0].listening:
            self.toolbar.ToggleTool(wx.ID_HOME, True)
        else:
            self.toolbar.ToggleTool(wx.ID_HOME, False)
        wx.CallLater(100, self.checkToggleState)

    def OnNew(self, event):
        self.API.tabManager.addPage()
        self.API.editWindow.update()

    def OnOpen(self, event):
        open_ = wx.FileDialog(self,
            self.tr("Open new document"),
            wildcard = 'Seal or MansOS ' + self.tr('files') + ' (*.sl, *.c, *.h)|*.sl;*.c;*.h;config|' +
                    self.tr('All files') + '(.*)|*',
            style = wx.FD_OPEN | wx.FD_MULTIPLE)
        if open_.ShowModal() == wx.ID_OK:
            for x in open_.GetPaths():
                if os.path.exists(x) and os.path.isfile(x):
                    self.API.tabManager.addPage(x)
        open_.Destroy()

    def findFirstSourceFile(self, path):
        # look for files in this order: first main.sl
        filename = os.path.join(path, "main.sl")
        if os.path.isfile(filename): return filename
        # then main.c
        filename = os.path.join(path, "main.c")
        if os.path.isfile(filename): return filename
        # then any other .sl file
        for _ in os.listdir(path):
            filename = os.path.join(path, filename)
            if filename[len(filename) - 3:] == '.sl': return filename
        # then any other .c file
        for _ in os.listdir(path):
            filename = os.path.join(path, filename)
            if filename[len(filename) - 2:] == '.c': return filename
        # then give up
        return None

    def OnOpenExample(self, event):
        path = self.examples.get(event.GetId())
        filename = self.findFirstSourceFile(path)
        if filename:
            self.API.tabManager.addPage(filename)
        else:
            self.API.logMsg(LOG_WARNING, "No source files in {}".format(path))

    def OnAddStatement(self, event):
        self.API.tabManager.getPageObject().code.addStatement()

    def OnAddCondition(self, event):
        self.API.tabManager.getPageObject().code.addCondition()

    def OnAbout(self, event):
        versionFile = os.path.join("../..", "doc/VERSION")
        f = open(versionFile, "r")
        lines = f.readlines()
        f.close()
        release = "Unknown"
        date = "Unknown"
        if len(lines) > 0:
            release = lines[0].strip()
        if len(lines) > 1:
            date = lines[1].strip()
        text = """
MansOS

Version: {}
Release date: {}

MansOS is an operating system for wireless sensor networks (WSN) and other resource-constrained embedded systems.

The emphasis is on easy use and fast adoption time. Therefore, MansOS supports code written in C, and UNIX-like concepts such as sockets for communication. MansOS is also designed to be modular for easy portability to new platforms and architectures.

Some of the supported target platforms are based on MSP430 and Atmega microcontrollers (Nordic MCU support is in development). Popular and supported platform names include Tmote Sky and other Telosb clones, Waspmote, Arduino.

Should you have questions or suggestions about the support, please contact info@mansos.net 

MansOS developed by: MansOS contributors, (c) 2008-2012, info@mansos.net
IDE developed by: Janis Judvaitis, (c) 2011-2012, janis.judvaitis@gmail.com
""".format(release, date)
        wx.MessageBox(text, 'Info',
            wx.OK | wx.ICON_INFORMATION)

    def OnSealHelp(self, event):
        filename = "http://mansos.net/wiki/index.php/SEAL"
        # Damn linux
        if os.name == 'posix':
            Popen(['xdg-open', filename])
        # other OS
        else:
            webbrowser.open_new_tab(filename)

    def OnMansosHelp(self, event):
        filename = "http://mansos.edi.lv/?page_id=5"
        # Damn linux
        if os.name == 'posix':
            Popen(['xdg-open', filename])
        # other OS
        else:
            webbrowser.open_new_tab(filename)

    def changeLanguage(self, event):
        for i in self.langs:
            if i.IsChecked() == True:
                self.API.setSetting("activeLanguage", i.GetHelp())
                self.initUI()

    def disableAdders(self):
        self.toolbar.EnableTool(wx.ID_ADD, False)
        self.toolbar.EnableTool(wx.ID_APPLY, False)
        if self.API.loaded:
            self.API.frame.auiManager.ShowPane(self.API.editPanel, False)

    def enableAdders(self):
        self.toolbar.EnableTool(wx.ID_ADD, True)
        self.toolbar.EnableTool(wx.ID_APPLY, True)
        if self.API.loaded:
            self.API.frame.auiManager.ShowPane(self.API.editPanel, True)

    def rememberPositioning(self):
        # This approach have a small bug.
        #    1. Maximize window
        #    2. Exit
        #    3. Reopen
        #    4. Re-maximize
        # Result is that window stays with maximized height and width, 
        # but is not maximized.
        # TODO: FIX: cache all sizes when resizing and not in maximized mode.
        self.API.setSetting("Width", self.GetSize()[0])
        self.API.setSetting("Height", self.GetSize()[1])
        self.API.setSetting("LocX", self.GetScreenPositionTuple()[0])
        self.API.setSetting("LocY", self.GetScreenPositionTuple()[1])
        self.API.setSetting("Maximized", self.IsMaximized())

    def loadPositioning(self):
        width = self.API.getSetting("Width")
        if width == '':
            width = 800
        else:
            width = int(width)

        height = self.API.getSetting("Height")
        if height == '':
            height = 600
        else:
            height = int(height)

        self.SetSize((width, height))

        locX = self.API.getSetting("LocX")
        if locX == '':
            # Center
            locX = (wx.GetDisplaySize()[0] - width) / 2
        else:
            locX = int(locX)

        locY = self.API.getSetting("LocY")
        if locY == '':
            # Center
            locY = (wx.GetDisplaySize()[1] - height) / 2
        else:
            locY = int(locY)

        self.SetPosition((locX, locY))

        maximized = self.API.getSetting("Maximized")
        if maximized == '':
            maximized = False
        else:
            maximized = bool(maximized == "True")

        self.Maximize(maximized)

    def deactivateNoEditorMode(self):
        self.toolbar.EnableTool(wx.ID_SAVE, True)
        self.toolbar.EnableTool(wx.ID_ADD, True)
        self.toolbar.EnableTool(wx.ID_APPLY, True)
        self.toolbar.EnableTool(wx.ID_PREVIEW, True)
        self.toolbar.EnableTool(wx.ID_PREVIEW_GOTO, True)
        self.toolbar.EnableTool(wx.ID_PREVIEW_ZOOM, True)

    def activateNoEditorMode(self):
        self.toolbar.EnableTool(wx.ID_SAVE, False)
        self.toolbar.EnableTool(wx.ID_ADD, False)
        self.toolbar.EnableTool(wx.ID_APPLY, False)
        self.toolbar.EnableTool(wx.ID_PREVIEW, False)
        self.toolbar.EnableTool(wx.ID_PREVIEW_GOTO, False)
        self.toolbar.EnableTool(wx.ID_PREVIEW_ZOOM, False)
        if self.API.loaded:
            self.API.frame.auiManager.ShowPane(self.API.editPanel, False)

    #def OnBlocklyTool(self, event):
    #    wx.YieldIfNeeded()
    #    self.auiManager.RestorePane(self.blocklyPane)
    #    self.blocklyToolVisible = not self.blocklyToolVisible

    def layoutBlocklyPane(self):
        blocklyPane = (aui.AuiPaneInfo().Caption("Seal-Blockly handler").
                Name("blocklyPane").BestSize(wx.Size(500, 150)))
        self.auiManager.AddPane(self.API.blockly, blocklyPane,
                                target = self.infoPane)

    def layoutListenPane(self, listenModule, name, floating = True):
        listenPane = (aui.AuiPaneInfo().BestSize(wx.Size(500, 150)).
                Caption(name).Name(name).MinimizeButton(True).
                MaximizeButton(True).CloseButton(True))
        if floating:
            listenPane.Float()
        self.auiManager.AddPane(listenModule, listenPane, target = self.infoPane)

    def layoutEditPane(self):
        self.rightPane = (aui.AuiPaneInfo().Floatable(True).
                Right().Name("editPane").MinimizeButton(True).
                MaximizeButton(True).CloseButton(True).Caption("Visual edit").
                BestSize(wx.Size(320, 400)))
        self.auiManager.AddPane(self.API.editPanel, self.rightPane)
