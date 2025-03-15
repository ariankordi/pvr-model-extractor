# quick and messy glb exporter -- only supports a single mesh / node / scene per file
# glb format spec: https://github.com/KhronosGroup/glTF/blob/master/specification/2.0/README.md#glb-file-format-specification

import numpy as np
from struct import pack
import json

mesh_exist = False
image_exist = False
material_exist = False
sampler_exist = False
texture_exist = False
animation_exist = False

class GLBExporter:
  def __init__(self):
    self.data = bytes()
    self.asset = {"version": "2.0", "generator": f"PicelBoi POD2GLB", "copyright": "2025 (c) ariankordi, 2025 (c) Imagination Technologies (POD File Format), 2025 (c) PicelBoi, 2018 (c) jaames"}
    self.scene = 0
    self.scenes = [{
      "nodes": []
    }]
    self.nodes = []
    self.buffers = []
    self.bufferViews = []
    self.accessors = []
    self.meshes = []
    self.materials = []
    self.textures = []
    self.images = []
    self.samplers = []
    self.skins = []
    self.animations = [
      {
        "samplers": [],
        "channels": []
      }
    ]

  def addRootNodeIndex(self, index):
    self.scenes[0]["nodes"].append(index)

  def addNode(self, node):
    self.nodes.append(node)

  def addMesh(self, mesh):
    global mesh_exist
    self.meshes.append(mesh)
    mesh_exist = True

  def addMaterial(self, material):
    global material_exist
    self.materials.append(material)
    material_exist = True

  def addTexture(self, texture):
    global texture_exist
    self.textures.append(texture)
    texture_exist =True

  def addImage(self, image):
    global image_exist
    self.images.append(image)
    image_exist = True

  def addSampler(self, sampler):
    global sampler_exist
    self.samplers.append(sampler)
    sampler_exist = True
  
  def addData(self, data):
    # Calculate the current offset
    offset = len(self.data)
    # Pad current data to 4-byte boundary
    padding = (4 - (offset % 4)) % 4
    self.data += bytes(padding)
    # Add the new data
    self.data += data
    return offset + padding
  
  def addBufferView(self, bufferView):
    index = len(self.bufferViews)
    self.bufferViews.append(bufferView)
    return index
  
  def addAccessor(self, accessor):
    index = len(self.accessors)
    self.accessors.append(accessor)
    return index
  
  def addSkin(self, bones):
    self.skins.append({
      "joints": bones
    })

  def addAnimation(self, sampler, nodeindex, path):
    global animation_exist
    animation_exist = True
    # Get the amount of samplers in samplers so far
    samplerIndex = len(self.animations[0]["samplers"]) - 1

    # now add the sampler
    self.animations[0]["samplers"].append(sampler)

    # finally add the channel
    channel = {
      "sampler": samplerIndex,
      "target": {
        "node": nodeindex,
        "path": path
      }
    }

    # add the sampler
    self.animations[0]["channels"].append(channel)
    

  def buildJSON(self):
    return {
      "asset": self.asset,
      "scene": self.scene,
      "scenes": self.scenes,
      "nodes": self.nodes,
      "buffers": self.buffers,
      "bufferViews": self.bufferViews,
      "accessors": self.accessors,
      "meshes": self.meshes,
      "materials": self.materials,
      "textures": self.textures,
      "images": self.images,
      "samplers": self.samplers,
      "animations": self.animations,
      "skins": self.skins
    }
  
  def save(self, path):
    with open(path, "wb") as f:
      self.buffers.append({
        "byteLength": len(self.data)
      })
      json_data = json.dumps(self.buildJSON())
      # pad json data with spaces
      json_data += " " * (4 - len(json_data) % 4)
      # pad binary data with null bytes
      self.data += bytes((4 - len(self.data) % 4))
      # write fileheader
      f.write(pack("<4sII", b'glTF', 2, len(json_data) + len(self.data) + 28))
      # write json chunk
      f.write(pack("<I4s", len(json_data), b'JSON'))
      f.write(json_data.encode())
      # write data chunk
      f.write(pack("<I4s", len(self.data), b'BIN\x00'))
      f.write(self.data)