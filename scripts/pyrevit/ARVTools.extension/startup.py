# -*- coding: utf-8 -*-
"""Chạy khi pyRevit nạp extension ARVTools: đăng ký updater "ARV Vách kính" – vách kính do nút Vách kính dựng
(có dữ liệu ARV trong Extensible Storage) đổi chiều dài / chiều cao thì chia lại đố theo quy tắc VK ngay trong
lần sửa đó (cùng một bước Ctrl+Z). Cửa không còn vừa thì trả vách về kích thước cũ.
Updater đăng ký dạng "optional": máy không có công cụ mở mô hình vẫn không bị cảnh báo."""
from __future__ import unicode_literals

import os
import sys
import traceback

_lib = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib")
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import clr
clr.AddReference("RevitAPI")
import Autodesk.Revit.DB as DB
from Autodesk.Revit.DB.ExtensibleStorage import ExtensibleStorageFilter
from System import Guid

import arv_vach_kinh as vk

UPDATER_GUID = Guid("b7d4e1a2-5c3f-4e8b-9a61-2f0c7d9e4b18")
NHAT_KY = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), "pyRevit", "ARVTools", "VachKinh_updater.log")


def ghi_nhat_ky(s):
    try:
        import io
        import datetime
        d = os.path.dirname(NHAT_KY)
        if not os.path.isdir(d):
            os.makedirs(d)
        with io.open(NHAT_KY, "a", encoding="utf-8") as f:
            f.write("%s %s\n" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), s))
    except Exception:
        pass


class VachKinhUpdater(DB.IUpdater):
    def __init__(self, addin_id):
        self._id = DB.UpdaterId(addin_id, UPDATER_GUID)

    def Execute(self, data):
        try:
            doc = data.GetDocument()
            bao = []
            for eid in data.GetModifiedElementIds():
                w = doc.GetElement(eid)
                if w is not None:
                    vk.cap_nhat_vach(doc, w, None, bao)
            for b in bao:
                ghi_nhat_ky(b)
        except Exception:
            ghi_nhat_ky(traceback.format_exc())

    def GetUpdaterId(self):
        return self._id

    def GetUpdaterName(self):
        return "ARV Vach kinh"

    def GetAdditionalInformation(self):
        return "Chia lại đố vách kính ARV khi đổi chiều dài / chiều cao"

    def GetChangePriority(self):
        return DB.ChangePriority.FloorsRoofsStructuralWalls


def dang_ky(app):
    up = VachKinhUpdater(app.ActiveAddInId)
    uid = up.GetUpdaterId()
    if DB.UpdaterRegistry.IsUpdaterRegistered(uid):
        DB.UpdaterRegistry.UnregisterUpdater(uid)
    DB.UpdaterRegistry.RegisterUpdater(up, True)
    loc = ExtensibleStorageFilter(vk.SCHEMA_GUID)
    DB.UpdaterRegistry.AddTrigger(uid, loc, DB.Element.GetChangeTypeGeometry())
    DB.UpdaterRegistry.AddTrigger(uid, loc, DB.Element.GetChangeTypeParameter(
        DB.ElementId(DB.BuiltInParameter.WALL_USER_HEIGHT_PARAM)))
    return up


try:
    _UPDATER = dang_ky(__revit__.Application)
except Exception:
    ghi_nhat_ky("Không đăng ký được updater:\n" + traceback.format_exc())
