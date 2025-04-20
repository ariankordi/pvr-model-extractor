# quick and messy glb exporter -- only supports a single mesh / node / scene per file
# glb format spec: https://github.com/KhronosGroup/glTF/blob/master/specification/2.0/README.md#glb-file-format-specification

from struct import pack
import json


class GLBExporter:
  RootNodeIndex = 0
  def __init__(self):
    self.data = bytes()
    self.asset = {"version": "2.0", "generator": "pod2glb.py (https://github.com/PicelBoi/pvr-model-extractor)", "copyright": "2025 (c) ariankordi, 2025 (c) Imagination Technologies (POD File Format), 2025 (c) PicelBoi, 2018 (c) jaames"}
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
    self.RootNodeIndex = index

  def addNode(self, node):
    self.nodes.append(node)

  def addMesh(self, mesh):
    self.meshes.append(mesh)

  def addMaterial(self, material):
    self.materials.append(material)

  def addTexture(self, texture):
    self.textures.append(texture)

  def addImage(self, image):
    self.images.append(image)

  def addSampler(self, sampler):
    self.samplers.append(sampler)

  def addData(self, data):
    # Calculate the current offset
    offset = len(self.data)
    # Add the new data
    self.data += data
    return offset

  def addBufferView(self, bufferView):
    index = len(self.bufferViews)
    self.bufferViews.append(bufferView)
    return index

  def addAccessor(self, accessor):
    index = len(self.accessors)
    self.accessors.append(accessor)
    return index

  def addSkin(self, skin):
    index = len(self.skins)
    self.skins.append(skin)
    return index

  def addAnimation(self, sampler, nodeindex, path):
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
    obj = {
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
      #"animations": self.animations
    }
    # only add skins if it is populated (cannot be empty)
    if len(self.skins):
      obj["skins"] = self.skins

    return obj

  def save(self, path):
    with open(path, "wb") as f:
      # pad binary data with null bytes
      self.data += bytes((4 - len(self.data) % 4) % 4)

      self.buffers.append({
        "byteLength": len(self.data)
      })

      json_data = json.dumps(self.buildJSON())
      # pad json data with spaces
      json_data += " " * (4 - len(json_data) % 4)
      # write fileheader
      f.write(pack("<4sII", b'glTF', 2, len(json_data) + len(self.data) + 28))
      # write json chunk
      f.write(pack("<I4s", len(json_data), b'JSON'))
      f.write(json_data.encode())
      # write data chunk
      f.write(pack("<I4s", len(self.data), b'BIN\x00'))
      f.write(self.data)
