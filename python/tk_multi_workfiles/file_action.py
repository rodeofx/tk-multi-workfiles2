# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
"""

import sgtk

class FileAction(object):
    def __init__(self, name, label):
        """
        """
        self._app = sgtk.platform.current_bundle()
        self._name = name
        self._label = label
        
    @property
    def name(self):
        return self._name
    
    @property
    def label(self):
        return self._label
    
    def execute(self, file, file_versions, environment, parent_ui):
        raise NotImplementedError()


class SeparatorFileAction(FileAction):
    def __init__(self):
        FileAction.__init__(self, "separator", "Separator")
        
    def execute(self, file, file_versions, environment, parent_ui):
        pass


from sgtk.platform.qt import QtGui, QtCore

class ShowInShotgunAction(FileAction):
    """
    """
    def _open_url_for_published_file(self, file):
        """
        """
        # construct the url:
        published_file_entity_type = sgtk.util.get_published_file_entity_type(self._app.sgtk)
        url = "%s/detail/%s/%d" % (self._app.sgtk.shotgun.base_url, published_file_entity_type, file.published_file_id)
        
        # and open it:
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))


class ShowPublishInShotgunAction(ShowInShotgunAction):
    """
    """
    def __init__(self):
        ShowInShotgunAction.__init__(self, "jump_to_publish_in_shotgun", "Jump to Publish in Shotgun")
        
    def execute(self, file, file_versions, environment, parent_ui):
        """
        """
        if not file or not file.is_published:
            return

        self._open_url_for_published_file(file)

class ShowLatestPublishInShotgunAction(ShowInShotgunAction):
    """
    """
    def __init__(self):
        ShowInShotgunAction.__init__(self, "jump_to_latest_publish_in_shotgun", 
                                     "Jump to Latest Publish in Shotgun")
        
    def execute(self, file, file_versions, environment, parent_ui):
        """
        """
        publish_versions = [v for v, f in file_versions.iteritems() if f.is_published]
        if not publish_versions:
            return
        
        max_publish_version = max(publish_versions)
        self._open_url_for_published_file(file_versions[max_publish_version])



import os
import sys

class ShowInFileSystemAction(FileAction):
    """
    """
    def _show_in_fs(self, path):
        """
        """
        # find the deepest path that actually exists:
        while path and not os.path.exists(path):
            path = os.path.dirname(path)
        if not path:
            return
        
        # ensure the slashes are correct:
        path = path.replace("/", os.path.sep)
        
        # build the command:
        if sys.platform == "linux2":
            # TODO - figure out how to open the parent and select the file/path
            if os.path.isfile(path):
                path = os.path.dirname(path)
            cmd = "xdg-open \"%s\"" % path
        elif sys.platform.startswith("darwin"):
            cmd = "open -R \"%s\"" % path
        elif sys.platform == "win32":
            # TODO - figure out how to open the parent and select the file/path
            if os.path.isfile(path):
                path = os.path.dirname(path)
            cmd = "cmd.exe /C start \"Folder\" \"%s\"" % path
        else:
            raise TankError("Platform '%s' is not supported." % system)
        
        # run the command:
        exit_code = os.system(cmd)
        if exit_code != 0:
            self._app.log_error("Failed to launch '%s'!" % cmd)
    
class ShowPublishInFileSystemAction(ShowInFileSystemAction):
    """
    """
    def __init__(self):
        ShowInFileSystemAction.__init__(self, "show_publish_in_file_system", "Show Publish In File System")
        
    def execute(self, file, file_versions, environment, parent_ui):
        """
        """
        if file and file.is_published:
            self._show_in_fs(file.publish_path)
    
class ShowWorkFileInFileSystemAction(ShowInFileSystemAction):
    """
    """
    def __init__(self):
        ShowInFileSystemAction.__init__(self, "show_workfile_in_file_system", "Show Work File In File System")
        
    def execute(self, file, file_versions, environment, parent_ui):
        """
        """
        if file and file.is_local:
            self._show_in_fs(file.path)

from itertools import chain

class ShowAreaInFileSystemAction(ShowInFileSystemAction):
    def _show_area_in_fs(self, file, template):
        """
        """
        # build fields starting with the context:
        fields = environment.context.as_template_fields(template)
        if file:
            # add any additional fields that we can extract from the work or publish paths
            file_fields = {}
            if file.is_local and environment.work_template:
                try:
                    file_fields = environment.work_template.get_fields(file.path)
                except TankError, e:
                    pass
            elif file.is_published and environment.publish_template:
                try:
                    file_fields = environment.publish_template.get_fields(file.publish_path)
                except TankError, e:
                    pass
            # combine with the context fields, preferring the context
            fields = dict(chain(ctx_fields.iteritems(), file_fields.iteritems()))
            
        # try to build a path from the template with these fields:
        while template and template.missing_keys(fields):
            template = template.parent
        if not template:
            # failed to find a template with no missing keys!
            return
        path = template.apply_fields(fields)
        
        # finally, show the path:
        self._show_in_fs(path)



class ShowWorkAreaInFileSystemAction(ShowInFileSystemAction):
    """
    """
    def __init__(self):
        ShowInFileSystemAction.__init__(self, "show_work_area_in_file_system", "Show Work Area In File System")
        
    def execute(self, file, file_versions, environment, parent_ui):
        """
        """
        if not file:
            return
        
        if not environment or not environment.context or not environment.work_area_template:
            return

        self._show_area_in_fs(file, environment.work_area_template)



class ShowPublishAreaInFileSystemAction(ShowInFileSystemAction):
    """
    """
    def __init__(self):
        ShowInFileSystemAction.__init__(self, "show_publish_area_in_file_system", "Show Publish Area In File System")
        
    def execute(self, file, file_versions, environment, parent_ui):
        """
        """
        if not file:
            return
        
        if not environment or not environment.context or not environment.publish_area_template:
            return
        
        self._show_area_in_fs(file, environment.publish_area_template)


    
class CustomFileAction(FileAction):
    def __init__(self, name, label):
        """
        """
        custom_name = "custom_%s" % name
        FileAction.__init__(self, custom_name, label)
        self._orig_name = name
    
    def execute(self, file, file_versions, environment, parent_ui):
        """
        """
        # execute hook to perform the action
        # TODO
        pass