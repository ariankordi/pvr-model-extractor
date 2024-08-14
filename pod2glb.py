# File paths for advanced people
NOESIS = ""
PVRTEXTOOL = ""

# Don't touch.

FIX_COMPLETED = False

import PIL.Image
from PowerVR.PVRPODLoader import PVRPODLoader
from GLB.GLBExporter import GLBExporter
from PowerVR.PVRMaths import PVRMaths
import struct
import json
from xml.etree import ElementTree as etree
from sys import argv
from os import path
import os
import subprocess as sp
import platform
import PIL

# Global Variables
pathto = ""
pathout = ""
xmlsupport = False
xmlfile = None
xmldata = None
xmlroot = None
xmlmodel = None
platform = platform.system()

print(f"""
-----------------------------------------------------------------------------------
                                  POD2GLB
                        originally made by jaames
                            edited by picelboi
                           running on {platform}
    for more information, go to https://github.com/PicelBoi/pvr-model-extractor
-----------------------------------------------------------------------------------

""")
print(f"[DEBUG] Platform is {platform}")
class POD2GLB:

  def __init__(self):
    self.glb = None
    self.pod = None
    self.scene = None
    self.fix_uvs = True
    

  @classmethod
  def open(cls, inpath):
    print("[Part 00] Loading POD...")
    converter = cls()
    converter.load(inpath)
    return converter

  def load(self, inpath):
    print("[Part 01] Starting up all loaders...") 
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
    print("[Part 06] Saving all data to a GLB format...")
    if xmlsupport == True:
      print('[WARNING] Due to constraints with GLTF, any Mask textures found will be attached as "Emission". It is up to you to reattach and correctly apply this map.')
    self.glb.save(path)
    print("[FINISH!] Done!")

  def findallsamplers(xmlmaterial):
      samplers = 0
      for material in xmlmaterial:
        samp = material.findall("Sampler2D")
        for sample in samp:
          samplers = samplers + 1
      print(f"[DEBUG] Found {samplers} in XML file.")
      return(samplers)

  def convert_textures(self):  
    alphahotfix = False
    alphaarray = []
    diffusearray = []
    print("[Part 04] Converting textures...")
    if platform == "Windows":
      pathforcheck = ((os.path.abspath(os.getcwd())) + "\\PVRTexToolCLI.exe")
    elif platform == "Darwin":
      pathforcheck = ((os.path.abspath(os.getcwd())) + "/PVRTexToolCLI")
    elif platform == "Linux":
      pathforcheck = ((os.path.abspath(os.getcwd())) + "/PVRTexToolCLI")
    else:
      print("UNKNOWN PLATFORM! DEFAULTING TO LINUX...")
      pathforcheck = ((os.path.abspath(os.getcwd())) + "/PVRTexToolCLI")
    # Override if user has a file path for PVRTexTool
    if PVRTEXTOOL != "":
      print(f"[OVERRIDE] Overriding path for PVRTexTool with {PVRTEXTOOL}")
      pathforcheck = PVRTEXTOOL
    print("[DEBUG] Path for PVRTexToolCLI should be in: " + pathforcheck)
    SANITYCHECK = path.exists(pathforcheck)
    if xmlsupport == False:
      for (textureIndex, texture) in enumerate(self.scene.textures):
        print(f"[Part 04-1] Adding image {texture.getPath()}...")
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
    else:
      # Enchanced XML sampler import support
      xmlmaterials = xmlroot.find("Materials")
      xmlmaterial = xmlmaterials.findall('Material')
      textureIndex = 0
      for material in xmlmaterial:
        for sampler in material.findall('Sampler2D'):
          magFilter = 9729
          minFilter = 9987
          wrapS = 10497
          wrapT = 10497
          texture = {
            "path": str((sampler.find("FileName")).text).replace(".tga",".png"),
            "name": str(sampler.attrib['Name'])
          }
          mag = sampler.find("GL_TEXTURE_MAG_FILTER")
          min = sampler.find("GL_TEXTURE_MIN_FILTER")
          S = sampler.find("GL_TEXTURE_WRAP_S")
          T = sampler.find("GL_TEXTURE_WRAP_T")

          # If statement hell for deciding which stuff is which.

          # Magnification filter
          if mag.text == "GL_NEAREST":
            magFilter = 9728
          elif mag.text == "GL_LINEAR":
            magFilter = 9729

          # Minification filter
          if min.text == "GL_NEAREST":
            minFilter = 9728
          elif min.text == "GL_LINEAR":
            minFilter = 9729
          elif min.text == "GL_NEAREST_MIPMAP_NEAREST":
            minFilter = 9784
          elif min.text == "GL_LINEAR_MIPMAP_NEAREST":
            minFilter = 9785
          elif min.text == "GL_NEAREST_MIPMAP_LINEAR":
            minFilter = 9786
          elif min.text == "GL_LINEAR_MIPMAP_LINEAR":
            minFilter = 9787

          # S (U) Wrapping Mode
          if S.text == "GL_CLAMP_TO_EDGE":
            wrapS = 33061
          elif S.text == "GL_MIRRORED_REPEAT":
            wrapS = 33648
          elif S.text == "GL_REPEAT":
            wrapS = 10947

          # T (V) Wrapping Mode
          if T.text == "GL_CLAMP_TO_EDGE":
            wrapT = 33061
          elif T.text == "GL_MIRRORED_REPEAT":
            wrapT = 33648
          elif T.text == "GL_REPEAT":
            wrapT = 10947

          print(f"[Part 04-1] Adding image {texture['name']}, path {texture['path']}...")
          self.glb.addImage({
            "uri": texture['path']
          })
          self.glb.addSampler({
            "magFilter": magFilter,
            "minFilter": minFilter,
            "wrapS": wrapS,
            "wrapT": wrapT
          })
          self.glb.addTexture({
            "name": texture["name"],
            "sampler": textureIndex,
            "source": textureIndex
          })
          textureIndex = textureIndex + 1
          if texture["name"] == "uAlbedoTexture":
            diffusearray.append(os.path.join(os.path.dirname(pathout), os.path.basename(texture['path'])))
            print("[DEBUG] Diffuse Map found.")
          elif texture["name"] == "uAlphaTexture":
            alphaarray.append(os.path.join(os.path.dirname(pathout), os.path.basename(texture['path'])))
            alphahotfix = True
            print("[DEBUG] Alpha Map found.")


    if SANITYCHECK == True:
      print("[Part 04-2] Now converting all images!")
      tobeconvert = []
      for root, dirs, files in os.walk(os.path.dirname(pathto)):
        for pvr in files:
          if str(pvr).endswith(".pvr"):
            output = os.path.join(os.path.dirname(pathout), os.path.basename(os.path.splitext(pvr)[0]+".png"))
            print(f"[Part 04-2] Converting {pvr} to png...")
            print(f"[DEBUG] Will be saved at {output}")
            sp.call([
              pathforcheck,
              "-d", output,
              "-i", os.path.join(root, pvr)
            ])
            print("[HOTFIX] PVRTexTool for some reason generates a _Out file, so automatically deleting that.")
            os.remove(os.path.join(root, os.path.splitext(pvr)[0]+"_Out.pvr"))
      if alphahotfix == True:
        print("[HOTFIX] Due to contraints with GLTF files, alpha maps will be inserted into the diffuse map.")
        for diffusemap in diffusearray:
          for comalpha in range(len(diffusearray)):
            diffusepath = diffusemap
            try:
              alphamap = PIL.Image.open(alphaarray[comalpha]).convert("L")
              diffusemap = PIL.Image.open(diffusemap).convert("RGB")

              dw, dh = diffusemap.size
              alpharesize = (dw, dh)
              alphamap.resize(alpharesize)
              diffusemap.putalpha(alphamap)
              diffusemap.save(diffusepath)
            except FileNotFoundError:
              print("[DEBUG] Not applying non-exsistent alpha.")


    else:
        print("[Part 04-2 - WARNING!] Textures will be added, but not converted. You don't have PVRTexToolCLI downloaded or didn't put it in the same directory as the converter (Or you misspelled string inside the PVRTEXTOOL variable if you tried to override the paths!). To download it, go to https://developer.imaginationtech.com/solutions/pvrtextool/. If you have downloaded, move PVRTexToolCLI in the same directory as this script! The usual path (for Windows) is C:\\Imagination Technologies\\PowerVR_Graphics\\PowerVR_Tools\\PVRTexTool\\CLI\\Windows_x86_64.")
  
  def convert_materials(self):
    print("[Part 05] Converting materials...")
    if xmlsupport == False:
      for (materialIndex, material) in enumerate(self.scene.materials):
        if material.diffuseTextureIndex > -1:
          pbr = {
            "baseColorTexture": {
              "index": material.diffuseTextureIndex,
            },
            "roughnessFactor": 1 - material.shininess,
          }
        else: 
          pbr = {
            "baseColorFactor": material.diffuse.tolist() + [1],
            "roughnessFactor": 1 - material.shininess,
          }
        if material.bumpMapTextureIndex > -1:
          normal = {
            "index": material.bumpMapTextureIndex
          }
        else:
          normal = {}
        if material.opacityTextureIndex > -1:
          Alpha = {
            "index": material.bumpMapTextureIndex
          }
        else:
          Alpha = {}

        self.glb.addMaterial({
          "name": material.name,
          "pbrMetallicRoughness": pbr,
          "normalTexture": normal,
          "occlusionTexture": Alpha
        })
    else:
      xmlmaterials = xmlroot.find("Materials")
      xmlmaterial = xmlmaterials.findall('Material')
      textureIndex = 0
      for (materialIndex, material) in enumerate(self.scene.materials):
        # Settings to list which option is available
        hasAlpha = False
        # Makes texture visible
        Albedo = {
          "baseColorTexture": {},
          "roughnessFactor": 1 - material.shininess
        }
        Normal = {}
        Mask = {}
        Alpha = {}
        for xmmaterial in xmlmaterial:
          print(f"[DEBUG] Material from POD Name is {material.name}")
          print(f"[DEBUG] Material from XML is called {xmmaterial.attrib['Name']}")
          if str(material.name) == xmmaterial.attrib['Name']:
            for sampler in xmmaterial.findall('Sampler2D'):
              if sampler.attrib['Name'] == 'uAlbedoTexture':
                Albedo["baseColorTexture"] = {"index": int(textureIndex)}
                if sampler.find("UVIdx") is not None:
                  Albedo["texCoord"] = int((sampler.find("UVIdx")).text)
                textureIndex = textureIndex + 1
                print("[DEBUG] Has albedo texture!")

              elif sampler.attrib['Name'] == 'uNormalTexture':
                hasNormal = True
                Normal["index"] = int(textureIndex)
                if sampler.find("UVIdx") is not None:
                  Normal["texCoord"] = int((sampler.find("UVIdx")).text)
                textureIndex += 1
                print("[DEBUG] Has normal texture!")

              elif sampler.attrib['Name'] == 'uMaskTexture':
                hasMask = True
                Mask["index"] = int(textureIndex)
                if sampler.find("UVIdx") is not None:
                  Mask["texCoord"] = int((sampler.find("UVIdx")).text)
                textureIndex += 1
                print("[DEBUG] Has mask texture!")

              elif sampler.attrib['Name'] == 'uAlphaTexture':
                hasAlpha =True

                # Old alpha code.

                #Alpha["index"] = int(textureIndex)
                #if sampler.find("UVIdx") is not None:
                #  Alpha["texCoord"] = int((sampler.find("UVIdx")).text)
                textureIndex += 1
                print("[DEBUG] Has alpha support!")
    
            print(f"[Part 05-1] Adding material {material.name}...")

            PODMaterial = {
              "name": material.name,
              "pbrMetallicRoughness": Albedo,
              "normalTexture": Normal,
              "emissiveTexture": Mask,
              "doubleSided": True,
            }
            
            if hasAlpha == True:
              # Old code.
              #PODMaterial["occlusionTexture"] = Alpha
              PODMaterial["alphaMode"] = "BLEND"
            
            if xmmaterial.find("Culling") is not None:
              if xmmaterial.find("Culling").text == 'None':
                print(f"[DEBUG] Material {material.name} does NOT have backface culling on.")
              else:
                PODMaterial["doubleSided"] == False
                print(f"[DEBUG] Material {material.name} has backface culling on.")

            self.glb.addMaterial(PODMaterial)
          else:
            print(f"[DEBUG] Material is not the same! {xmmaterial.attrib['Name']} is not the same as {material.name}")

  def convert_nodes(self):
    print("[Part 03] Converting nodes...")
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
        print(f"[Part 03-1] {node.name} has a mesh index.")
        meshIndex = node.index
        nodeEntry["mesh"] = meshIndex
        if node.materialIndex != -1:
          self.glb.meshes[meshIndex]["primitives"][0]["material"] = node.materialIndex

      # if the node index is -1 it is a root node
      if node.parentIndex == -1:
        print(f"[Part 03-1] {node.name} is a root node.")
        self.glb.addRootNodeIndex(nodeIndex)
      print(f"[Part 03-2] Now adding {node.name}.")
      self.glb.addNode(nodeEntry)
      # To convert or not to convert
      if node.animation.matrices != None:
        print(f"Converting matrix animation data for: {node.name}")
        print("Currently animation porting is not available at this time, sorry :(")
        # keyframes = []
        # matrix = node.animation.matrices.tolist()
        # for x in range(len(matrix)):
        #   if x != 15 or:
        #    rotationX = PVRMaths.PVRMatrix4x4RX3D()

  
  def convert_meshes(self):
    print("[Part 02] Converting meshes...")
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
      print("[Part 02-1] Adding mesh...")
      self.glb.addMesh({
        "primitives": [{
          "attributes": attributes,
          "indices": indicesAccessorIndex,
          "mode": 4,
        }],
      })

def NoesisStuff(file, pathforcheck):
  print("Using Noesis to convert to FBX as a way to fix it mainly because I'm lazy")
  if platform == "Windows":
    print("[FIX 01] Platform is Windows/MS-DOS, running Noesis natively")
    sp.call([
      pathforcheck,
      "?cmode",
      file,
      os.path.basename(os.path.splitext(file)[0]+".fbx")
    ])
  elif platform == "Darwin":
    print("[FIX 01] Platform is UNIX-based, trying to use Wine to run Noesis (Note: This is for macOS - No idea if wine would be in PATH)")
    sp.call([
      "wine " + pathforcheck,
      "?cmode",
      file,
      os.path.basename(os.path.splitext(file)[0]+".fbx")
    ])
  elif platform == "Linux":
    print("[FIX 01] Platform is UNIX-based, trying to use Wine to run Noesis (Linux)")
    sp.call([
      "wine " + pathforcheck,
      "?cmode",
      file,
      os.path.basename(os.path.splitext(file)[0]+".fbx")
    ])
  else:
    print("[FIX 01] Platform is unknown, trying to use Wine to run Noesis")
    sp.call([
      "wine " + pathforcheck,
      "?cmode",
      file,
      os.path.basename(os.path.splitext(file)[0]+".fbx")
    ])
  print("[FIX - FINISH!] Should generate a FBX file - use that instead of the GLB file.")
  FIX_COMPLETED = True
def NoesisFix(file):
  print("[FIX 00] Trying to convert the GLB to FBX because Blender doesn't understand the armature this tool generates.")
  # Check if 64-bit version is available
  if platform == "Windows":
    pathforcheck = ((os.path.abspath(os.getcwd())) + "\\Noesis64.exe")
  elif platform == "Darwin":
    pathforcheck = ((os.path.abspath(os.getcwd())) + "/Noesis64.exe")
  elif platform == "Linux":
    pathforcheck = ((os.path.abspath(os.getcwd())) + "/Noesis64.exe")
  else:
    print("[FIX 00 - WARNING] UNKNOWN PLATFORM! DEFAULTING TO UNIX...")
    pathforcheck = ((os.path.abspath(os.getcwd())) + "/Noesis64.exe")

  print("[DEBUG] Path for Noesis should be in: " + pathforcheck)
  SANITYCHECK = path.exists(pathforcheck)
  if SANITYCHECK == True:
    NoesisStuff(file, pathforcheck)
  else:
    print("[DEBUG] 64-bit version NOT detected.")
  if FIX_COMPLETED == True:
    # Check if 32-bit version is available
    if platform == "Windows":
      pathforcheck = ((os.path.abspath(os.getcwd())) + "\\Noesis.exe")
    elif platform == "Darwin":
      pathforcheck = ((os.path.abspath(os.getcwd())) + "/Noesis.exe")
    elif platform == "Linux":
      pathforcheck = ((os.path.abspath(os.getcwd())) + "/Noesis.exe")
    else:
      pathforcheck = ((os.path.abspath(os.getcwd())) + "/Noesis.exe")
    
    # Override if user has a file path for Noesis

      if NOESIS != "":
        print(f"[OVERRIDE] Overriding path for Noesis with {NOESIS}")
        pathforcheck = NOESIS
    print("[DEBUG] Path for Noesis should be in: " + pathforcheck)
    if SANITYCHECK == True:
      NoesisStuff(file, pathforcheck)
    else:
      if FIX_COMPLETED == False:
        print("[FIX - ERROR!] Fix will NOT continue. You don't have Noesis downloaded or didn't put it in the same directory as the converter (Or you misspelled the NOESIS variable if you tried to override the paths!). To download it, go to https://www.richwhitehouse.com/index.php?content=inc_projects.php&showproject=91.")

def help():
  print("""
Help:
extract.py [POD path] [GLB path] [-f]

Options:
-f: Tries to fix Blender quirks with GLB files by converting it to a FBX file using Noesis.

Advanced:
(Both variables have to be set inside the Python script. If you need to reset, just clear everything in the string.)
PVRTEXTOOL: Variable used to override the location of PVRTexToolCli.
NOESIS: Variable used to override the location of Noesis.
""")
#try:
pathto = argv[1]
pathout = argv[2]
# Check if a companion XML exists with the POD.
check = str(os.path.basename(pathto)).replace(".pod", "_model.xml" )
print(f"[DEBUG] File to check is {check}")
for root, dirs, files in os.walk(os.path.dirname(pathto)):
  for xml in files:
    if str(xml).endswith(".xml"):
      print(f"[DEBUG] xml file to check is {xml}")
    if xml == check:
      xmlsupport = True
      print("[XML] XML Detected!")
      xmlfile = xml
      xmldata = etree.parse(os.path.join(os.path.dirname(pathto) ,xmlfile))
      xmlroot = xmldata.getroot()
      print(f"Model is called {xmlroot.attrib["Name"]}")

converter = POD2GLB.open(argv[1])
#except IndexError:
#  help()
#  print("[ERROR!] Please add a path to the POD!")
try:
  converter.save(argv[2])
except IndexError:
  help()
  print("[ERROR!] Add the path/name of the GLB file!")
except NameError:
  print("[ERROR!] GLB not specified.")
try:
  if argv[3] == "--fix-armature" or "-f":
    NoesisFix(argv[2])
except IndexError:
  print("[DEBUG] Will not convert to FBX via Noesis as -f or --fix-armature option was not specified.")
