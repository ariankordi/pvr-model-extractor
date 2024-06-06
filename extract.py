from PowerVR.PVRPODLoader import PVRPODLoader
from GLB.GLBExporter import GLBExporter
import struct
import json
from sys import argv
from os import path
import os
import subprocess as sp

pathto = ""

class POD2GLB:

  def __init__(self):
    self.glb = None
    self.pod = None
    self.scene = None
    self.fix_uvs = True

  @classmethod
  def open(cls, inpath):
    converter = cls()
    converter.load(inpath)
    return converter

  def load(self, inpath):
    # create a glb exporter
    self.glb = GLBExporter()
    # create a pvr pod parser
    self.pod = PVRPODLoader.open(inpath)
    self.scene = self.pod.scene
    self.convert_meshes()
    self.convert_nodes()
    self.convert_textures()
    self.convert_materials()

  def save(self, path):
    self.glb.save(path)

  def convert_textures(self):  
    print("Converting textures...")
    pathforcheck = (os.path.abspath(os.getcwd())) + "\\PVRTexToolCLI.exe"
    print(pathforcheck)
    SANITYCHECK = path.exists(pathforcheck)
    if SANITYCHECK == True:
        for (textureIndex, texture) in enumerate(self.scene.textures):
            self.glb.addImage({
                "uri": texture.getPath(dir="", ext=".png")
            })
            self.glb.addSampler({
                "magFilter": 9729,
                "minFilter": 9987,
                "wrapS": 10497,
                "wrapT": 10497
            })
            self.glb.addTexture({
                "name": texture.name,
                "sampler": textureIndex,
                "source": textureIndex
            })
            sp.call([
                "PVRTexToolCLI",
                "-i", texture.getPath(dir=pathto + "\\..\\", ext=".pvr"),
                "-d", texture.getPath(dir="", ext=".png")
        ])
        print("Hotfix for Miitomo - ignore if this isn't the game this POD belongs to")
        for (textureIndex, texture) in enumerate(self.scene.textures):
            self.glb.addImage({
                "uri": texture.getPath(dir="", ext=".png")
            })
            self.glb.addSampler({
                "magFilter": 9729,
                "minFilter": 9987,
                "wrapS": 10497,
                "wrapT": 10497
            })
            self.glb.addTexture({
                "name": texture.name,
                "sampler": textureIndex,
                "source": textureIndex
            })
            sp.call([
                "PVRTexToolCLI",
                "-i", texture.getPath(dir=pathto + "\\..\\textures\\android\\", ext=".pvr"),
                "-d", texture.getPath(dir="", ext=".png")
        ])
    else:
        print("You don't have PVRTexToolCLI downloaded or didn't put it in the same directory as the converter. To download it, go to https://developer.imaginationtech.com/solutions/pvrtextool/. If you have downloaded, move PVRTexToolCLI in the same directory as this script! The usual path (for Windows) is C:\\Imagination Technologies\\PowerVR_Graphics\\PowerVR_Tools\\PVRTexTool\\CLI\\Windows_x86_64.")
  
  def convert_materials(self):
    for (materialIndex, material) in enumerate(self.scene.materials):
      if material.diffuseTextureIndex > -1:
        pbr = {
          "baseColorTexture": {
            "index": material.diffuseTextureIndex,
            "texCoord": 1
          },
          "roughnessFactor": 1 - material.shininess,
        }
      else: 
        pbr = {
          "baseColorFactor": material.diffuse.tolist() + [1],
          "roughnessFactor": 1 - material.shininess,
        }
      self.glb.addMaterial({
        "name": material.name,
        "pbrMetallicRoughness": pbr
      })

  def convert_nodes(self):
    for (nodeIndex, node) in enumerate(self.scene.nodes):
      nodeEntry = {
        "name": node.name,
        "children": [i for (i, node) in enumerate(self.scene.nodes) if node.parentIndex == nodeIndex],
        "translation": node.animation.positions.tolist(),
        "scale": node.animation.scales[0:3].tolist(),
        "rotation": node.animation.rotations[0:4].tolist(),
      }
      # if the node has a mesh index
      if node.index != -1: 
        meshIndex = node.index
        nodeEntry["mesh"] = meshIndex
        if node.materialIndex != -1:
          self.glb.meshes[meshIndex]["primitives"][0]["material"] = node.materialIndex

      # if the node index is -1 it is a root node
      if node.parentIndex == -1:
        self.glb.addRootNodeIndex(nodeIndex)
      
      self.glb.addNode(nodeEntry)
  
  def convert_meshes(self):
    for (meshIndex, mesh) in enumerate(self.scene.meshes):
      attributes = {}
      numFaces = mesh.primitiveData["numFaces"]
      numVertices = mesh.primitiveData["numVertices"]

      # face index buffer view
      indices = mesh.faces["data"]
      indicesAccessorIndex = self.glb.addAccessor({
        "bufferView": self.glb.addBufferView({
          "buffer": 0,
          "byteOffset": self.glb.addData(indices.tobytes()),
          "byteLength": len(indices) * indices.itemsize,
          "target": 34963
        }),
        "byteOffset": 0,
        # https://github.com/KhronosGroup/glTF/blob/master/specification/2.0/README.md#accessor-element-size
        "componentType": 5123,
        "count": numFaces * 3,
        "type": "SCALAR"
      })

      # vertex buffer view
      vertexElements = mesh.vertexElements

      # PVR texture coordinates are inverted compared to 
      if "TEXCOORD_0" in vertexElements:
        element = vertexElements["TEXCOORD_0"]
        # covnert data to a bytearray so it can be manipulated
        data = bytearray(mesh.vertexElementData[0])
        stride = element["stride"]
        offset = element["offset"]
        mesh.vertexElementData[0] = bytes(data)

      vertexBufferView = self.glb.addBufferView({
        "buffer": 0,
        "byteOffset": self.glb.addData(mesh.vertexElementData[0]),
        "byteStride": vertexElements["POSITION"]["stride"],
        "byteLength": len(mesh.vertexElementData[0]),
      })

      for name in vertexElements:
        element = vertexElements[name]
        componentType = 5126
        type = "VEC3"
        
        if name == "TEXCOORD_0":
          type = "VEC2"
        
        elif name == "COLOR_0": # not implemented
          continue

        accessorIndex = self.glb.addAccessor({
          "bufferView": vertexBufferView,
          "byteOffset": element["offset"],
          # https://github.com/KhronosGroup/glTF/blob/master/specification/2.0/README.md#accessor-element-size
          "componentType": componentType,
          "count": numVertices,
          "type": type
        })
        attributes[name] = accessorIndex

      # POD meshes only have one primitive?
      # https://github.com/KhronosGroup/glTF/blob/master/specification/2.0/README.md#primitive
      self.glb.addMesh({
        "primitives": [{
          "attributes": attributes,
          "indices": indicesAccessorIndex,
          "mode": 4,
        }],
      })
try:
  pathto = argv[1]
  converter = POD2GLB.open(argv[1])
except IndexError:
  print("Please add a path to the POD!")
try:
  converter.save(argv[2])
except IndexError:
  print("Add the path/name of the GLB file!")
