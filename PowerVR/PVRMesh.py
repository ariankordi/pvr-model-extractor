from PowerVR.EPOD import *
import numpy as np
import logging
logger = logging.getLogger(__name__)

vertextdata2numpydata = {
  13: np.int8,  # EPVRMesh.VertexData.eByte
  10: np.uint8,  # EPVRMesh.VertexData.eUnsignedByte
  11: np.int16,  # EPVRMesh.VertexData.eShort
  3: np.uint16,   # EPVRMesh.VertexData.eUnsignedShort
  17: np.uint32,  # EPVRMesh.VertexData.eUnsignedInt
  1: np.float32    # EPVRMesh.VertexData.eFloat
}

class EPVRMesh:
  eTriangleList          = 0
  eIndexedTriangleList   = 1
  eTriangleStrips        = 2
  eIndexedTriangleStrips = 3
  eTriPatchList          = 4
  eQuadPatchList         = 5

  class VertexData:
    eNone               = 0
    eFloat              = 1
    eInt                = 2
    eUnsignedShort      = 3
    eRGBA               = 4
    eARGB               = 5
    eD3DCOLOR           = 6
    eUBYTE4             = 7
    eDEC3N              = 8
    eFixed16_16         = 9
    eUnsignedByte      = 10
    eShort             = 11
    eShortNorm         = 12
    eByte              = 13
    eByteNorm          = 14
    eUnsignedByteNorm  = 15
    eUnsignedShortNorm = 16
    eUnsignedInt       = 17
    eABGR              = 18
    eCustom            = 1000
  
  class FaceData:
    e16Bit = 3
    e32Bit = 17



def debuffer(data, stride, number, type, offset, vertices):
      dedata = np.frombuffer(data, dtype=vertextdata2numpydata[type])
      stridee = int(stride / dedata.itemsize)
      offset = int(offset / dedata.itemsize)
      assert dedata.size % stridee == 0, "data size not divisble by stride"
      tempdata = []
      tempvec = []
      index = offset
      extra = 0
      for x in dedata:
        if len(tempdata) == vertices:
          break
        tempvec.append(float(dedata[index + extra]))
        if len(tempvec) == number:
          tempdata.append(tempvec)
          tempvec = []
          extra += stridee - number
        index += 1
      dedata = tempdata
      logger.debug(dedata)
      return(dedata)


class PVRMesh:
  def __init__(self):
    self.unpackMatrix = []
    self.vertexElementData = []
    self.vertexElements = {}
    self.primitiveData = {
      "numVertices": 0,
      "numFaces": 0,
			"numStrips": 0,
			"numPatchesSubdivisions": 0,
			"numPatches": 0,
			"numControlPointsPerPatch": 0,
			"stripLengths": None,
		  "primitiveType": EPVRMesh.eIndexedTriangleList
    }
    self.boneBatches = {
			"boneMax": 0,
			"count": 0,
			"batches": None,
			"boneCounts": None,
			"offsets": None
		}
    self.faces = {
      "indexType": EPVRMesh.FaceData.e16Bit,
      "data": None
		}
  
  def AddData(self, data):
    self.vertexElementData.append(data)
    return len(self.vertexElementData) - 1
  
  def AddFaces(self, data, type):
    self.faces["indexType"] = type
    self.faces["data"] = data
    self.primitiveData["numFaces"] = len(data) // 3 if len(data) > 0 else 0
    return EPODErrorCodes.eNoError

  def AddElement(self, semantic, type, numComponents, stride, offset, dataIndex):
    fix = True
    if semantic in self.vertexElements:
      return EPODErrorCodes.eKeyAlreadyExists
    logger.debug(f"{semantic}:")
    elementdata = debuffer(self.vertexElementData[0], stride, numComponents, type, offset, self.primitiveData["numVertices"])
    logger.debug(elementdata)

    newdata = []

    if semantic == "TANGENT":
      index = 0
      for x in elementdata:
        newdata.append(np.array([x[0], x[1], x[2], 1], dtype=np.float32))
      index += 1

    elif semantic == "JOINTS_0":
      print(self.boneBatches["batches"])
      for x in elementdata:
        joints = []
        for y in x:
          if len(x) <= 4:
            checkmate = int(y)
            joints.append(checkmate)

        addZero = 4 - len(x)

        if addZero >= 1:
          for z in range(addZero):
            joints.append(0)

        newdata.append(np.array(joints, dtype=np.uint8))
    elif semantic == "WEIGHTS_0":
      for x in elementdata:
        joints = []
        for y in x:
          joints.append(y)

        if 4 - len(x) >= 1:
          for z in range(4 - len(x)):
            joints.append(0)

        newdata.append(np.array(joints, dtype=np.float32))
    else:
      index = 0
      for x in elementdata:
        newdata.append(np.array(x, dtype=np.float32))
      index += 1
    logger.debug(np.array(newdata))

    self.vertexElements[semantic] = {
      "semantic": semantic,
      "dataType": type,
      "numComponents": numComponents,
      "dataIndex": dataIndex,
      "stride": stride,
      "offset": offset,
      "buffer": np.array(newdata)
    }
      
    return EPODErrorCodes.eNoError