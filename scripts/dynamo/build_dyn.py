# -*- coding: utf-8 -*-
r"""Sinh file Dynamo .dyn tu file .py cua Python node (CPython3) + danh sach dau vao.

Graph sinh ra theo khuon cac graph ARV dang dung: cac node Input (dung duoc voi Dynamo Player) -> 1 Python node ->
1 Watch "Bao cao". Nhom: "Dau vao" / "Xu ly" / "Dau ra". Che do chay Manual.

Dung:
    python build_dyn.py <spec.json>
spec.json:
    {"ten": "ChongTham_KhaoSatModel", "mo_ta": "...", "py": "ChongTham_KhaoSatModel.py",
     "dau_vao": [{"ten": "Thu muc ket qua", "kieu": "string", "gia_tri": "D:\\AI\\_tmp\\revit_khaosat"},
                 {"ten": "Dry-run", "kieu": "bool", "gia_tri": true}]}
Kieu: string / bool / number. File .dyn ghi canh spec (khong ghi de: da co thi chep ban cu vao <goc>\_backup truoc).
"""
import json
import os
import shutil
import sys
import uuid
from datetime import datetime


def _id():
    return uuid.uuid4().hex


def _cong(mo_ta=""):
    return {"Id": _id(), "Name": "", "Description": mo_ta, "UsingDefaultValue": False, "Level": 2,
            "UseLevels": False, "KeepListStructure": False}


def node_input(dv):
    k = dv["kieu"]
    if k == "bool":
        n = {"ConcreteType": "CoreNodeModels.Input.BoolSelector, CoreNodeModels", "NodeType": "BooleanInputNode",
             "Description": "Enables selection between True and False", "InputValue": bool(dv["gia_tri"])}
        t = "boolean"
    elif k == "number":
        n = {"ConcreteType": "CoreNodeModels.Input.DoubleInput, CoreNodeModels", "NodeType": "NumberInputNode",
             "NumberType": "Double", "Description": "Creates a number", "InputValue": float(dv["gia_tri"])}
        t = "number"
    else:
        n = {"ConcreteType": "CoreNodeModels.Input.StringInput, CoreNodeModels", "NodeType": "StringInputNode",
             "Description": "Creates a string.", "InputValue": str(dv["gia_tri"])}
        t = "string"
    n.update({"Id": _id(), "Inputs": [], "Outputs": [_cong(t)], "Replication": "Disabled"})
    return n, t


def build(spec_path):
    goc = os.path.dirname(os.path.abspath(spec_path))
    spec = json.load(open(spec_path, encoding="utf-8"))
    code = open(os.path.join(goc, spec["py"]), encoding="utf-8").read()
    nodes, conns, views, inputs = [], [], [], []
    py_in = []
    for i, dv in enumerate(spec["dau_vao"]):
        n, t = node_input(dv)
        nodes.append(n)
        cong = _cong(dv["ten"])
        cong["Name"] = "IN[%d]" % i
        py_in.append(cong)
        conns.append({"Start": n["Outputs"][0]["Id"], "End": cong["Id"], "Id": _id(), "IsHidden": "False"})
        views.append({"Id": n["Id"], "Name": dv["ten"], "IsSetAsInput": True, "IsSetAsOutput": False,
                      "Excluded": False, "ShowGeometry": True, "X": 0.0, "Y": 130.0 * i})
        gt = dv["gia_tri"]
        inputs.append({"Id": n["Id"], "Name": dv["ten"], "Type": t, "Type2": t,
                       "Value": ("true" if gt else "false") if t == "boolean" else str(gt),
                       "Description": n["Description"]})
    py = {"ConcreteType": "PythonNodeModels.PythonNode, PythonNodeModels", "Code": code, "Engine": "CPython3",
          "VariableInputPorts": True, "Id": _id(), "NodeType": "PythonScriptNode", "Inputs": py_in,
          "Outputs": [_cong("Result of the python script")], "Replication": "Disabled",
          "Description": "Runs an embedded Python script."}
    py["Outputs"][0]["Name"] = "OUT"
    nodes.append(py)
    watch = {"ConcreteType": "CoreNodeModels.Watch, CoreNodeModels", "WatchWidth": 900.0, "WatchHeight": 500.0,
             "Id": _id(), "NodeType": "ExtensionNode", "Inputs": [_cong("Node to show output from")],
             "Outputs": [_cong("Node output")], "Replication": "Disabled", "Description": "Visualizes a node's output"}
    nodes.append(watch)
    conns.append({"Start": py["Outputs"][0]["Id"], "End": watch["Inputs"][0]["Id"], "Id": _id(), "IsHidden": "False"})
    h = 130.0 * max(len(spec["dau_vao"]), 1)
    views += [{"Id": py["Id"], "Name": spec["ten"], "IsSetAsInput": False, "IsSetAsOutput": False, "Excluded": False,
               "ShowGeometry": True, "X": 600.0, "Y": 0.0},
              {"Id": watch["Id"], "Name": "Báo cáo", "IsSetAsInput": False, "IsSetAsOutput": True, "Excluded": False,
               "ShowGeometry": True, "X": 1000.0, "Y": 0.0}]

    def nhom(ten, ids, x, y, w, hh, mau):
        return {"Id": _id(), "Title": ten, "DescriptionText": "", "IsExpanded": True, "WidthAdjustment": 0.0,
                "HeightAdjustment": 0.0, "Nodes": ids, "HasNestedGroups": False, "Left": x - 20, "Top": y - 60,
                "Width": w, "Height": hh, "FontSize": 36.0, "GroupStyleId": "00000000-0000-0000-0000-000000000000",
                "InitialTop": y, "InitialHeight": hh, "TextblockHeight": 50.0, "Background": mau}
    d = {"Uuid": str(uuid.uuid4()), "IsCustomNode": False, "Description": spec.get("mo_ta", ""), "Name": spec["ten"],
         "ElementResolver": {"ResolutionMap": {}}, "Inputs": inputs, "Outputs": [], "Nodes": nodes,
         "Connectors": conns, "Dependencies": [], "NodeLibraryDependencies": [],
         "EnableLegacyPolyCurveBehavior": True, "Thumbnail": "", "GraphDocumentationURL": None,
         "ExtensionWorkspaceData": [], "Author": "Archivina", "Linting": {"activeLinter": "None",
         "activeLinterId": "7b75fb44-43fd-4631-a878-29f4d5d8399a", "warningCount": 0, "errorCount": 0},
         "Bindings": [],
         "View": {"Dynamo": {"ScaleFactor": 1.0, "HasRunWithoutCrash": True, "IsVisibleInDynamoLibrary": True,
                             "Version": "3.6.2.11575", "RunType": "Manual", "RunPeriod": "1000"},
                  "Camera": {"Name": "_Background Preview", "EyeX": -17.0, "EyeY": 24.0, "EyeZ": 50.0, "LookX": 12.0,
                             "LookY": -13.0, "LookZ": -58.0, "UpX": 0.0, "UpY": 1.0, "UpZ": 0.0},
                  "ConnectorPins": [], "NodeViews": views,
                  "Annotations": [nhom("Đầu vào", [n["Id"] for n in nodes[:-2]], 0, 0, 420, h + 40, "#FFC1D676"),
                                  nhom("Xử lý", [py["Id"]], 600, 0, 300, 200, "#FFFFB8D8"),
                                  nhom("Đầu ra", [watch["Id"]], 1000, 0, 940, 560, "#FFB9F9E1")],
                  "X": 0.0, "Y": 0.0, "Zoom": 0.6}}
    out = os.path.join(goc, spec["ten"] + ".dyn")
    if os.path.exists(out):     # quy tac 2: ban cu vao _backup
        bk = os.path.join(goc, "..", "..", "_backup")
        if os.path.isdir(bk):
            shutil.copy2(out, os.path.join(bk, "%s_%s.dyn" % (spec["ten"], datetime.now().strftime("%Y%m%d_%H%M%S"))))
    with open(out, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print("Da ghi:", out)


if __name__ == "__main__":
    build(sys.argv[1])
