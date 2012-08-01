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

import wx
from os.path import exists, join

from wx.lib.agw import aui

from globals import * #@UnusedWildImports
from editor_manager import EditorManager

class TabManager(aui.AuiNotebook):
    def __init__(self, parent, API):
        aui.AuiNotebook.__init__(self, parent, style = aui.AUI_NB_CLOSE_ON_ACTIVE_TAB | aui.AUI_NB_SMART_TABS)

        self.API = API
        self.API.tabManager = self
        # Just a shorter name
        self.tr = self.API.tr

        # Need to set because next statement uses it
        self.nextPageNr = 1
        self.AddPage(EditorManager(self, self.API),
                self.tr("Untitled document"))

        self.Bind(aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.onPageChanged)
        self.Bind(aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.doPopupClose)
        #self.Bind(aui.EVT_AUINOTEBOOK_BUTTON, self.onCloseCheck)
        self.Bind(aui.EVT_AUINOTEBOOK_TAB_RIGHT_DOWN, self.showPopupMenu)

    def onPageChanged(self, event):
        if event != None:
            event.Skip()
        if self.getPageObject().projectType == SEAL_PROJECT:
            self.API.frame.enableAdders()
        else:
            self.API.frame.disableAdders()

        # Clear last dialog line, otherwise same line can't trigger new dialog
        # until other line triggers it.
        self.getPageObject().code.lastLine = -1

        # Remove any Helper windows
        self.API.checkForDeletedEditors()
        wx.YieldIfNeeded()

    def showPopupMenu(self, event):
        # Make clicked tab active, so all actions target this tab.
        self.SetSelection(event.GetSelection(), True)

        self._rmenu = wx.Menu()
        self.popupReload = self._rmenu.Append(wx.ID_REPLACE, '&' + self.tr("Reload") +
                                       '\tCtrl+R', self.tr("Reload"))
        self.popupSave = self._rmenu.Append(wx.ID_SAVE, '&' + self.tr('Save') +
                                     '\tCtrl+S', self.tr("Save"))
        self.popupSaveAs = self._rmenu.Append(wx.ID_SAVEAS, '&' + self.tr("Save as") +
                                       '\tCtrl+A', self.tr("Save as"))
        self.popupClose = self._rmenu.Append(wx.ID_CLOSE, '&' + self.tr('Close') +
                                      '\tCtrl+W', self.tr("Close"))
        self.Bind(wx.EVT_MENU, self.doPopupReload, self.popupReload)
        self.Bind(wx.EVT_MENU, self.doPopupSave, self.popupSave)
        self.Bind(wx.EVT_MENU, self.doPopupSaveAs, self.popupSaveAs)
        self.Bind(wx.EVT_MENU, self.doPopupClose, self.popupClose)
        #Disable control if needed
        if self.getPageObject().saveState == True:
            self.popupSave.Enable(False)

        # Popup the menu. If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.PopupMenu(self._rmenu)
        self._rmenu.Destroy()

    def doPopupReload(self, event):
        self.getPageObject().update()
        self.onPageChanged(None)

    def doPopupSave(self, event):
        if self.getPageObject() == None:
            return
        if self.getPageObject().hasAFile == True:
            self.getPageObject().save()
        else:
            save = wx.FileDialog(self,
                self.tr("Save") + " \"" +
                    str(self.GetPageText(self.GetSelection())) + '"',
                wildcard = 'Seal ' + self.tr('files') + ' (*.sl)|*.sl|' +
                    self.tr('All files') + '|*',
                style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
                defaultFile = self.getPageObject().fileName)
            if save.ShowModal() == wx.ID_OK:
                self.getPageObject().updateInfo(path = save.GetPath())
                self.getPageObject().save()
                self.getPageObject().hasAFile = True
            save.Destroy()
        return self.getPageObject().hasAFile == True

    def doPopupSaveAs(self, event):
        save = wx.FileDialog(self,
            self.tr("Save as") + " \"" +
            str(self.GetPageText(self.GetSelection())) + '"',
            wildcard = 'Seal ' + self.tr('files') + ' (*.sl)|*.sl|' +
                    self.tr('All files') + '|*',
            style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
            defaultFile = self.getPageObject().fileName)
        if save.ShowModal() == wx.ID_OK:
            if save.GetPath()[-3:] != '.sl':
                self.getPageObject().updateInfo(path = save.GetPath() + '.sl')
            else:
                self.getPageObject().updateInfo(path = save.GetPath())
            self.getPageObject().save()
        save.Destroy()

    def doPopupClose(self, event, checkConsequences = True):
        if self.onCloseCheck() == False:
            return False
        # Remove selected page.
        self.DeletePage(self.GetSelection())

        if self.GetPageCount() == 0:
            self.API.frame.activateNoEditorMode()
        self.API.checkForDeletedEditors()
        if event:
            event.Veto()
        self.Layout()
        return True

    def titleChange(self, newName):
        self.SetPageText(self.GetSelection(), newName)

    def markAsUnsaved(self):
        self.titleChange('* ' + self.getPageObject().fileName)


    def markAsSaved(self):
        if self.getPageObject() != None:
            self.titleChange(self.getPageObject().fileName)

    def getPageObject(self):
        if self.GetSelection() != -1:
            return self.GetPage(self.GetSelection())
        else:
            return None

    def addPage(self, newFile = ''):
        if newFile == '':
            self.AddPage(EditorManager(self, self.API),
                self.tr("Untitled document") + ' ' + str(self.nextPageNr))
        else:
            self.AddPage(EditorManager(self, self.API), newFile)
        self.nextPageNr += 1
        self.SetSelection(self.GetPageCount() - 1)
        # Add any file associated with it
        self.getPageObject().update(newFile)
        self.Layout()
        self.API.frame.deactivateNoEditorMode()
        self.onPageChanged(None)


    def GetCurrentPage(self):
        return self.getPageObject()

    def onCloseCheck(self, event = None):
        if self.getPageObject() == None:
            # Nothing to check
            return True
        if self.getPageObject().saveState == False:
            # Initiate DialogBox
            dialog = wx.MessageDialog(self,
                self.tr('Save changes to') + ' "' +
                    self.getPageObject().fileName + '" ' +
                    self.tr('before close it?'),
                self.tr('Unsaved document') + ' "' +
                    self.getPageObject().fileName + '"',
                wx.YES_NO | wx.CANCEL | wx.ICON_EXCLAMATION)

            retVal = dialog.ShowModal()
            if retVal == wx.ID_YES:
                # Create save dialog
                self.doPopupSave(None)
                # Recursion to make sure it's really saved.
                return self.onCloseCheck()
            elif retVal == wx.ID_CANCEL:
                # Stop action if there is any
                if event:
                    event.Veto()
                return False
        # It's ok to close
        return True

    def onQuitCheck(self):
        while self.GetPageCount() > 0:
            # Select first page and try to close it
            self.SetSelection(0)
            if self.doPopupClose(None, False) == False:
                return False
        return True

    def rememberOpenedTabs(self):
        result = ''
        for x in self.API.editors:
            if type(x) is EditorManager:
                result += x.filePath + ";"
        self.API.setSetting('openedTabs', result.strip(";"))

    def loadRememberedTabs(self):
        tabs = self.API.getSetting('openedTabs').split(';')

        # Remove automatically created first page
        self.DeletePage(0)

        if tabs != ['']:
            # Add all Tabs
            for x in tabs:
                self.addPage(x)
            return

        # Open default files if no tabs were saved
        path = join(self.API.path, "../../apps/seal/Blink/")
        if exists(path):
            filename = self.API.frame.findFirstSourceFile(path)
            if filename:
                self.addPage(filename)
                return

        self.addPage('sampleCode.sl')
