from PowerVR.EPOD import *

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

# Mapping of VertexData enum values to size in bytes per component.
VERTEX_DATA_TYPE_SIZE = {
    1: 4,   # eFloat
    2: 4,   # eInt
    3: 2,   # eUnsignedShort
    4: 4,   # eRGBA
    5: 4,   # eARGB
    6: 4,   # eD3DCOLOR
    7: 4,   # eUBYTE4
    8: 4,   # eDEC3N
    9: 4,   # eFixed16_16
    10: 1,  # eUnsignedByte
    11: 2,  # eShort
    12: 2,  # eShortNorm
    13: 1,  # eByte
    14: 1,  # eByteNorm
    15: 1,  # eUnsignedByteNorm
    16: 2,  # eUnsignedShortNorm
    17: 4,  # eUnsignedInt
    18: 4   # eABGR
}

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
    if semantic in self.vertexElements:
      return EPODErrorCodes.eKeyAlreadyExists
    self.vertexElements[semantic] = {
      "semantic": semantic,
      "dataType": type,
      "numComponents": numComponents,
      "stride": stride,
      "offset": offset,
      "dataIndex": dataIndex,
    }
    return EPODErrorCodes.eNoError

  def DeinterleaveAttributes(self):
    """
    Deinterleaves vertex attributes from a single vertex buffer into separate binary buffers.

    Args:
        self: A PVRMesh object with vertexElementData and vertexElements.

    Returns:
        Dictionary mapping attribute names (e.g., "POSITION") to raw binary buffers.
    """
    vertex_blob = self.vertexElementData[0]
    num_vertices = self.primitiveData["numVertices"]
    vertex_elements = self.vertexElements

    separated_buffers = {}

    for attr_name, attr in vertex_elements.items():
        offset = attr["offset"]
        stride = attr["stride"]
        num_components = attr["numComponents"]
        data_type = attr["dataType"]

        if data_type not in VERTEX_DATA_TYPE_SIZE:
            raise ValueError(f"Unhandled vertex data type: {data_type}")

        component_size = VERTEX_DATA_TYPE_SIZE[data_type]
        attr_size = component_size * num_components

        output = bytearray()

        for i in range(num_vertices):
            start = i * stride + offset
            end = start + attr_size
            output.extend(vertex_blob[start:end])

        separated_buffers[attr_name] = bytes(output)

    return separated_buffers
