# -*- coding: utf-8 -*-


def bandwidth_interfaces(data):
  lines = data.splitlines()

  columnLine = lines[1]
  _, receiveCols , transmitCols = columnLine.split("|")

  receiveCols = list(map(lambda a:"recv_"+a, receiveCols.split()))
  transmitCols = list(map(lambda a:"trans_"+a, transmitCols.split()))

  cols = receiveCols+transmitCols

  faces = {}
  for line in lines[2:]:
    if line.find(":") < 0: continue
    face, data = line.split(":")
    face = face.strip()
    faceData = dict(zip(cols, data.split()))
    faces[face] = faceData
  return faces