import PIL.Image
from PowerVR.PVRPODLoader import PVRPODLoader
from GLB.GLBExporter import GLBExporter
from PowerVR.PVRMesh import EPVRMesh
from xml.etree import ElementTree as etree
from os import path
import os
import subprocess as sp
import platform
import PIL
import argparse
import math
# Matrix decompose
import glm

# numpy is only needed for calculating bounding box
hasnumpy = False
try:
    import numpy as np
    hasnumpy = True
except ImportError as e:
    print(f"[WARNING] numpy could not be imported: {e}. Will not be able to calculate bounding box which is probably fine")

# Override default paths for tools.
# These are overridden by the argparse arguments.
PVR_TEX_TOOL_PATH = ""

# Global Variables (Don't touch):
FBX_CONV_COMPLETED = False
pathto = ""
pathout = ""
xmlroot = None  # Non-null if an XML was found.
embedimage = False
platform = platform.system()  # Determines path of binaries.

print(f"""
-----------------------------------------------------------------------------------
                                  POD2GLB
                        originally made by jaames
                            edited by picelboi
                           running on {platform}
    for more information, go to https://github.com/PicelBoi/pvr-model-extractor
-----------------------------------------------------------------------------------

""")

class POD2GLB:
    # Table to resolve GLenum strings to values needed for glTF.
    GLENUM = {
        "GL_NEAREST": 9728,
        "GL_LINEAR": 9729,
        "GL_NEAREST_MIPMAP_NEAREST": 9784,
        "GL_LINEAR_MIPMAP_NEAREST": 9785,
        "GL_NEAREST_MIPMAP_LINEAR": 9786,
        "GL_LINEAR_MIPMAP_LINEAR": 9787,
        "GL_CLAMP_TO_EDGE": 33061,
        "GL_MIRRORED_REPEAT": 33648,
        "GL_REPEAT": 10497
    }
    # Samplers to add from the XML mapped to glTF materials.
    sampler_table = {
        "uAlbedoTexture": "pbrMetallicRoughness",
        "uNormalTexture": "normalTexture",
        "uMaskTexture": "emissiveTexture",
        "uAlphaTexture": None  # "occlusionTexture"
    }
    # https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#accessor-data-types
    num_components_to_accessor_types = {
        1: "SCALAR",
        2: "VEC2",
        3: "VEC3",
        4: "VEC4"
    }
    # https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#accessor-data-types
    vertex_data_type_to_accessor_data_types = {
        13: 5120,  # EPVRMesh.VertexData.eByte
        10: 5121,  # EPVRMesh.VertexData.eUnsignedByte
        11: 5122,  # EPVRMesh.VertexData.eShort
        3: 5123,   # EPVRMesh.VertexData.eUnsignedShort
        17: 5125,  # EPVRMesh.VertexData.eUnsignedInt
        1: 5126    # EPVRMesh.VertexData.eFloat
    }

    def __init__(self):
        self.glb = None
        self.pod = None
        self.scene = None
        #self.fix_uvs = True

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
        self.add_textures()
        self.convert_materials()

    def save(self, path):
        print("[Part 06] Saving all data to a GLB format...")
        if xmlroot is not None:
            print("[WARNING] Due to constraints with GLTF, any Mask textures found will be attached as \"Emission\". It is up to you to reattach and correctly apply this map.")
        self.glb.save(path)
        print("[FINISH!] Done!")

    @staticmethod
    def findallsamplers(xmlmaterial):
        samplers = 0
        for material in xmlmaterial:
            samp = material.findall("Sampler2D")
            for sample in samp:
                samplers += 1
        print(f"[DEBUG] Found {samplers} in XML file.")
        return samplers

    @staticmethod
    def texture_from_sampler(sampler):
        name = str(sampler.attrib["Name"])
        filename = sampler.find("FileName").text
        if filename is None:
            print(f"[DEBUG] Texture {name} does not have a filename, marking as unused.")
            return None  # Texture is not used.
        # Replace .tga with .png: vv
        path = str(filename).replace(".tga", ".png")
        texture = {
            "path": path,
            "name": name
        }
        return texture

    @staticmethod
    # Returns either the path or False if it does not exist:
    def get_pvrtextool_path_and_exists():
        slash = "\\" if platform == "Windows" else "/"
        suffix = ".exe" if platform == "Windows" else ""
        pvrtextool_path = f"{os.path.abspath(os.getcwd())}{slash}PVRTexToolCLI{suffix}"
        # Override if user has a file path for PVRTexTool
        overridden_text = ""
        if PVR_TEX_TOOL_PATH != "":
            overridden_text = "(OVERRIDDEN!) "
            pvrtextool_path = PVR_TEX_TOOL_PATH
        print(f"[DEBUG] Path for PVRTexToolCLI {overridden_text}is: {pvrtextool_path}")
        pvrtextool_exists = path.exists(pvrtextool_path)
        ret = False if not pvrtextool_exists else pvrtextool_path
        return ret

    @staticmethod
    def convert_texture_single(tool_path, input_file, output):
        print(f"[DEBUG] Running PVRTexTool. Will be saved at {output}")
        sp.run([
            tool_path,
            "-d", output,
            "-i", input_file,
            # Required to remove the _Out files without a janky fix.
            "-noout"
        ], check=True)  # Tool will output to console.

        # Deprecated.
        #pvr_out_fname = f"{os.path.splitext(input_file)[0]}_Out.pvr"
        #print(f"[HOTFIX] Deleting temporary PVRTexTool _Out file if it exists: {pvr_out_fname}")
        #try:
        #    pvr_out_path = os.path.join(os.path.dirname(input_file), pvr_out_fname)
        #    os.remove(pvr_out_path)
        #except FileNotFoundError:  # Ignore if that _Out file doesn't exist.
        #    pass

    def add_textures_no_conversion(self):
        for (textureIndex, texture) in enumerate(self.scene.textures):
            print(f"[Part 04-1] Adding image {texture.getPath()}...")

            self.glb.addImage({
                "uri": texture.getPath(dir="", ext=".png")
            })
            self.glb.addSampler({
                "magFilter": self.GLENUM["GL_LINEAR"],
                "minFilter": self.GLENUM["GL_LINEAR"],
                "wrapS": self.GLENUM["GL_REPEAT"],
                "wrapT": self.GLENUM["GL_REPEAT"]
            })
            self.glb.addTexture({
                "name": texture.name,
                "sampler": textureIndex,
                "source": textureIndex
            })

    def convert_textures(self, alphaarray=[], diffusearray=[]):
        if xmlroot is None:
            # Assumes all textures are in current directory.
            return self.add_textures_no_conversion()
        print("[Part 04] Converting textures...")

        pvrtextool_path = self.get_pvrtextool_path_and_exists()
        if pvrtextool_path:  # Is PVRTexTool available?
            dir_of_input = os.path.dirname(pathto)
            print("[Part 04-2] Now converting all images. Walking path:")

            for root, dirs, files in os.walk(dir_of_input):
                for file in files:
                    if not str(file).endswith(".pvr"):
                        continue  # Skip all non-pvr files.
                    # Input is a pvr file:
                    output = os.path.join(os.path.dirname(pathout), os.path.basename(f"{os.path.splitext(file)[0]}.png"))
                    print(f"[Part 04-2] Converting {file} to png...")
                    input_file = os.path.join(root, file)
                    self.convert_texture_single(pvrtextool_path, input_file, output)

            # Apply alpha maps.
            if not diffusearray:  # array is empty?
                return  # assuming we have nothing else to do
            print("[HOTFIX] Now merging alpha maps with albedo textures to conform with glTF specs.")
            for diffusemap in diffusearray:
                for comalpha in range(len(diffusearray)):
                    diffusepath = diffusemap
                    if diffusepath is None or comalpha >= len(alphaarray):
                        print("[DEBUG] Skipping alpha maps.")
                        continue
                    try:
                        alphamap = PIL.Image.open(alphaarray[comalpha]).convert("L")
                        diffusemap = PIL.Image.open(diffusemap).convert("RGB")

                        dw, dh = diffusemap.size
                        alpharesize = (dw, dh)
                        alphamap.resize(alpharesize)
                        diffusemap.putalpha(alphamap)
                        diffusemap.save(diffusepath)
                        print("[DEBUG] Applied alpha map to diffuse map and re-saved.")
                    except FileNotFoundError as e:
                        print(f"[DEBUG] Caught: {e}. Not applying non-existent alpha.")

            # Miitomo normal maps

        else:  # not pvrtextool_path
            print("[Part 04-2 - WARNING!] Textures will be added, but not converted (pvrtextool_path == False). You don't have PVRTexToolCLI downloaded or didn't put it in the same directory as the converter (Or you misspelled string inside the PVRTEXTOOL variable if you tried to override the paths!). To download it, go to https://developer.imaginationtech.com/solutions/pvrtextool/. If you have downloaded, move PVRTexToolCLI in the same directory as this script! The usual path (for Windows) is C:\\Imagination Technologies\\PowerVR_Graphics\\PowerVR_Tools\\PVRTexTool\\CLI\\Windows_x86_64.")

    def add_textures(self):
        if xmlroot is None:  # Take non-XML path.
            return self.add_textures_no_conversion()
        # Enchanced XML sampler import support
        xmlmaterials = xmlroot.find("Materials")
        xmlmaterial = xmlmaterials.findall("Material")
        textureIndex = 0

        # Albedo textures that need conversion:
        diffusearray = []  # Initialize and fill later: vv
        # Alpha maps to apply to them:
        alphaarray = []

        for material in xmlmaterial:
            # Iterate through all samplers to find
            # uAlbedoTexture/uAlphaTexture.
            for sampler in material.findall("Sampler2D"):
                texture = self.texture_from_sampler(sampler)
                if texture is None:
                    continue
                path = os.path.basename(texture["path"])
                abspath = os.path.join(os.path.dirname(pathout), path)

                if texture["name"] == "uAlbedoTexture":
                    diffusearray.append(abspath)
                    print("[DEBUG] Diffuse Map found.")
                elif texture["name"] == "uAlphaTexture":
                    alphaarray.append(abspath)
                    print("[DEBUG] Alpha Map found.")

        # Convert textures here.
        self.convert_textures(alphaarray, diffusearray)
        # Pass again to add textures.
        for material in xmlmaterial:
            for sampler in material.findall("Sampler2D"):
                texture = self.texture_from_sampler(sampler)
                if texture is None:
                    continue
                if texture["name"] not in self.sampler_table.keys():
                    print(f"[DEBUG] Skipping image {texture["name"]} since it is not in sampler_table and will not be added as a sampler either.")
                    continue

                mag = sampler.find("GL_TEXTURE_MAG_FILTER")
                min = sampler.find("GL_TEXTURE_MIN_FILTER")
                S = sampler.find("GL_TEXTURE_WRAP_S")
                T = sampler.find("GL_TEXTURE_WRAP_T")

                magFilter = self.GLENUM.get(mag.text, self.GLENUM["GL_LINEAR"])  # Magnificiation filter
                minFilter = self.GLENUM.get(min.text, self.GLENUM["GL_LINEAR"])  # Minification filter
                wrapS = self.GLENUM.get(S.text, self.GLENUM["GL_REPEAT"])  # S (U) Wrapping Mode
                wrapT = self.GLENUM.get(T.text, self.GLENUM["GL_REPEAT"])  # T (V) Wrapping Mode

                print(f"[Part 04-1] Adding image {texture["name"]}, path {texture["path"]}...")

                if embedimage:
                    with open(texture["path"], "rb") as img_file:
                        image_data = img_file.read()
                    # Create a buffer view for the image
                    buffer_view_index = self.glb.addBufferView({
                        "buffer": 0,
                        "byteOffset": self.glb.addData(image_data),  # buffer offset
                        "byteLength": len(image_data)
                    })
                    print(f"[DEBUG] Read image in, adding as buffer view index {buffer_view_index}")
                    # Add the image with bufferView and MIME type
                    self.glb.addImage({
                        "bufferView": buffer_view_index,
                        "mimeType": "image/png",
                        "name": os.path.basename(texture["path"]),
                        #"uri": texture["path"]
                    })
                else:  # Just use a link to the local image.
                    self.glb.addImage({
                        "uri": texture["path"]
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
                textureIndex += 1

    def convert_materials(self):
        print("[Part 05] Converting materials...")
        if xmlroot is not None:
            return self.convert_materials_with_xml()
        # Standard non-XML path.
        for (materialIndex, material) in enumerate(self.scene.materials):
            materialGLB = {
                "name": material.name,
            }
            if material.diffuseTextureIndex > -1:
                materialGLB["pbrMetallicRoughness"] = {
                    "baseColorTexture": {
                        "index": material.diffuseTextureIndex,
                    },
                    # Actually? convert shininess to roughness https://computergraphics.stackexchange.com/questions/1515/what-is-the-accepted-method-of-converting-shininess-to-roughness-and-vice-versa
                    "roughnessFactor": math.sqrt(2 / (material.shininess + 2)),
                    # To my understanding metalness doesn't exist in the POD specifications - so defaulting to dielectric
                    "metalnessFactor": 0
                }
            else:
                materialGLB["pbrMetallicRoughness"] = {
                    "baseColorFactor": material.diffuse.tolist() + [1],
                    # Actually? convert shininess to roughness https://computergraphics.stackexchange.com/questions/1515/what-is-the-accepted-method-of-converting-shininess-to-roughness-and-vice-versa
                    "roughnessFactor": math.sqrt(2 / (material.shininess + 2)),
                    # To my understanding metalness doesn't exist in the POD specifications - so defaulting to dielectric
                    "metalnessFactor": 0
                }
            if material.bumpMapTextureIndex > -1:
                materialGLB["normalTexture"] = {
                    "index": material.bumpMapTextureIndex
                }
            if material.opacityTextureIndex > -1:
                materialGLB["occlusionTexture"] = {
                    "index": material.bumpMapTextureIndex
                }

            self.glb.addMaterial(materialGLB)

    def convert_materials_with_xml(self):
        xmlmaterials = xmlroot.find("Materials")
        xmlmaterial = xmlmaterials.findall("Material")
        textureIndex = 0
        for (materialIndex, material) in enumerate(self.scene.materials):
            # Settings to list which option is available
            for materialkeys in xmlmaterial:
                print(f"[DEBUG] Material from POD Name is {material.name}, from XML: {materialkeys.attrib["Name"]}")
                if str(material.name) != materialkeys.attrib["Name"]:
                    #print(f"[DEBUG] Material is not the same! {materialkeys.attrib["Name"]} is not the same as {material.name}")
                    continue

                print(f"[Part 05-1] Adding material {material.name}...")

                cull_mode_to_double_sided = {
                    "None": True,
                    "Back": False,
                    "Front": False
                    # NOTE: Front is NOT supported in glTF.
                    # Also rare (headwear0063). Triangle windings
                    # need to be flipped in the index
                    # buffer in order to simulate this.
                }
                culling_key = materialkeys.find("Culling")
                if culling_key == "Front":
                    print("[WARNING] Culling is set to Front. This is not supported.")
                # Double sided as false by default.
                double_sided = cull_mode_to_double_sided.get(culling_key, False)
                print(f"[DEBUG] Material {material.name} {"does NOT have" if double_sided else "has"} backface culling on.")

                PODMaterial = {
                    "name": material.name,
                    # Albedo/uAlbedoTexture
                    "pbrMetallicRoughness": {  # Makes texture visible
                        "baseColorTexture": {},
                        # Actually? convert shininess to roughness https://computergraphics.stackexchange.com/questions/1515/what-is-the-accepted-method-of-converting-shininess-to-roughness-and-vice-versa
                        "roughnessFactor": math.sqrt(2 / (material.shininess + 2)),
                        # To my understanding metalness doesn't exist in the POD specifications - so defaulting to dielectric
                        "metalnessFactor": 0
                    },
                    # uNormalTexture
                    "normalTexture": {},
                    # uMaskTexture
                    "emissiveTexture": {},
                }
                if double_sided:
                    PODMaterial["doubleSided"] = double_sided

                for sampler in materialkeys.findall("Sampler2D"):
                    if "Name" not in sampler.attrib:
                        continue
                    name = sampler.attrib["Name"]
                    material_tex_name = self.sampler_table.get(name, None)
                    if material_tex_name is not None:
                        print(f"[DEBUG] Has sampler {name}!")
                        # glTF validator: Unexpected property. vv
                        if sampler.find("UVIdx") is not None:
                            PODMaterial[material_tex_name]["texCoord"] = int((sampler.find("UVIdx")).text)

                        # uAlbedoTexture:
                        if material_tex_name == "pbrMetallicRoughness":
                            PODMaterial[material_tex_name]["baseColorTexture"] = {"index": int(textureIndex)}
                        else:
                            PODMaterial[material_tex_name]["index"] = int(textureIndex)
                        textureIndex += 1

                # Set alphaMode to BLEND if IsXlu is enabled.
                for isxlu in materialkeys.findall('IsXlu'):
                    if isxlu.text == 'true':
                        PODMaterial["alphaMode"] = "BLEND"

                self.glb.addMaterial(PODMaterial)

    def convert_nodes(self):
        print("[Part 03] Converting nodes...")
        for (nodeIndex, node) in enumerate(self.scene.nodes):
            children = [i for (i, node) in enumerate(self.scene.nodes) if node.parentIndex == nodeIndex]

            nodeEntry = {
                "name": node.name
            }

            if node.animation.positions == None:
                nodeEntry["translation"] = [0,0,0]
            else:
                nodeEntry["translation"] = node.animation.positions.tolist()

            if node.animation.scales == None:
                nodeEntry["scale"] = [1,1,1]
            else:
                nodeEntry["scale"] = node.animation.scales[0:3].tolist()

            if node.animation.rotations == None:
                nodeEntry["rotation"] = [1,0,0,0]
            else:    
                nodeEntry["rotation"] = node.animation.rotations[0:4].tolist()

            if children:  # skip if it is empty array
                nodeEntry["children"] = children

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
            if node.animation.matrices is not None:
                print(f"Converting matrix animation data for: {node.name}")
                print(node.animation.matrices)
                keyframes = []
                matrix = node.animation.matrices.tolist()
                print(matrix)
                matrixIndex = 0
                for x in range(len(matrix)):
                    matrixIndex = matrixIndex + 1
                    if (nodeIndex + 1) % 16:
                        translation = glm.vec3()
                        rotation = glm.quat()
                        scale = glm.vec3()
                        skew = glm.vec3()
                        perspective = glm.vec4()
                        try:
                            animation = glm.mat4(matrix[matrixIndex - 15], matrix[matrixIndex - 14], matrix[matrixIndex - 13], matrix[matrixIndex - 12], matrix[matrixIndex - 11], matrix[matrixIndex - 10], matrix[matrixIndex - 9], matrix[matrixIndex - 8], matrix[matrixIndex - 7], matrix[matrixIndex - 6], matrix[matrixIndex - 5], matrix[matrixIndex - 4], matrix[matrixIndex - 3], matrix[matrixIndex - 2], matrix[matrixIndex - 1], matrix[matrixIndex])
                        except IndexError:
                            animation = glm.mat4()

                        decompose = glm.decompose(animation, scale, rotation, translation, skew, perspective)
                        matrixkey = [translation, rotation, scale]
                        print(matrixkey)
                        keyframes.append(matrixkey)

                # Now let's add the translation, rotation, and scale

                translations = []
                rotations = []
                scales = []
                times = []

                print("baka mitai")

                timer = 0

                for keyframe in keyframes:
                    # Create a buffer view for the translation, rotation, and scales

                    translation = keyframe[0].x, keyframe[0].y, keyframe[0].z

                    rotation = keyframe[1].w, keyframe[1].x, keyframe[1].y, keyframe[1].z
                    
                    scale = keyframe[2].x, keyframe[2].y, keyframe[2].z
                  
                    translations.append(np.array(translation))
                    rotations.append(np.array(rotation))
                    scales.append(np.array(scale))

                    times.append(timer)
                    timer += 0.33
                  
                tarray = np.asarray(translations)
                rarray = np.asarray(rotations)
                sarray = np.asarray(scale)
                timearray = np.asarray(times)

                translationAccessorIndex = self.glb.addAccessor({
                "bufferView": self.glb.addBufferView({
                    "buffer": 0,
                    "byteOffset": self.glb.addData(tarray.tobytes()),
                    "byteLength": len(translations) * tarray.itemsize,
                }),
                "byteOffset": 0,
                # https://github.com/KhronosGroup/glTF/blob/master/specification/2.0/README.md#accessor-element-size
                "componentType": 5126,
                "count": len(keyframes),
                "type": "VEC3",
                #"max": [tarray.max(axis=0)],
                #"min": [tarray.min(axis=0)]
            })
                
                rotationAccessorIndex = self.glb.addAccessor({
                "bufferView": self.glb.addBufferView({
                    "buffer": 0,
                    "byteOffset": self.glb.addData(rarray.tobytes()),
                    "byteLength": len(rotations) * rarray.itemsize,
                }),
                "byteOffset": 0,
                # https://github.com/KhronosGroup/glTF/blob/master/specification/2.0/README.md#accessor-element-size
                "componentType": 5126,
                "count": len(keyframes),
                "type": "VEC4",
                #"max": [rarray.max(axis=0)],
                #"min": [rarray.min(axis=0)]
            })
                
                scaleAccessorIndex = self.glb.addAccessor({
                "bufferView": self.glb.addBufferView({
                    "buffer": 0,
                    "byteOffset": self.glb.addData(sarray.tobytes()),
                    "byteLength": len(scales) * sarray.itemsize,
                }),
                "byteOffset": 0,
                # https://github.com/KhronosGroup/glTF/blob/master/specification/2.0/README.md#accessor-element-size
                "componentType": 5126,
                "count": len(keyframes),
                "type": "VEC3",
                #"max": [sarray.max(axis=0)],
                #"min": [sarray.min(axis=0)]
            })
                
                timesAccessorIndex = self.glb.addAccessor({
                "bufferView": self.glb.addBufferView({
                    "buffer": 0,
                    "byteOffset": self.glb.addData(timearray.tobytes()),
                    "byteLength": len(times) * timearray.itemsize,
                }),
                "byteOffset": 0,
                # https://github.com/KhronosGroup/glTF/blob/master/specification/2.0/README.md#accessor-element-size
                "componentType": 5126,
                "count": len(keyframes),
                "type": "SCALAR",
                #"max": [timearray.max(axis=0)],
                #"min": [timearray.min(axis=0)]
            })
                
                # Add animation
                translationSampler = {
                        "input": timesAccessorIndex,
                        "interpolation": "LINEAR",
                        "output": translationAccessorIndex
                    }
                scaleSampler = {
                        "input": timesAccessorIndex,
                        "interpolation": "LINEAR",
                        "output": scaleAccessorIndex
                    }
                rotationSampler = {
                        "input": timesAccessorIndex,
                        "interpolation": "LINEAR",
                        "output": rotationAccessorIndex
                    }
                
                self.glb.addAnimation(translationSampler, nodeIndex, "translation")
                self.glb.addAnimation(rotationSampler, nodeIndex, "rotation")
                self.glb.addAnimation(scaleSampler, nodeIndex, "scale")
                



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
                    "target": 34963     # ELEMENT_ARRAY_BUFFER
                }),
                "byteOffset": 0,
                # https://github.com/KhronosGroup/glTF/blob/master/specification/2.0/README.md#accessor-element-size
                "componentType": 5123,  # UNSIGNED_SHORT
                "count": numFaces * 3,
                "type": "SCALAR"
            })

            # vertex buffer view
            vertexElements = mesh.vertexElements

            # NOTE: Assuming that it's all in one vertex buffer...!!!
            vertexBufferView = self.glb.addBufferView({
                "buffer": 0,
                "byteOffset": self.glb.addData(mesh.vertexElementData[0]),
                "byteStride": vertexElements["POSITION"]["stride"],
                "target": 34962,  # ARRAY_BUFFER
                "byteLength": len(mesh.vertexElementData[0]),
            })
            print(f"[DEBUG] Creating bufferView for mesh {meshIndex}, length: {len(mesh.vertexElementData[0])}")

            for name in vertexElements:
                if name == "COLOR_0":
                    # COLOR_0 is is R8G8B8A8_UNORM
                    # it is not 4 floats, so adding it
                    # will not work and cause "accessor
                    # does not fit referenced bufferView..."
                    print("[DEBUG] Model has COLOR_0 attribute. This is not supported, so it will be skipped.")
                    continue

                element = vertexElements[name]
                accessorType = self.num_components_to_accessor_types \
                    .get(element["numComponents"], None)
                if accessorType is None:
                    raise NotImplementedError(f"Don't have glTF accessor data type for number of components: {element["numComponents"]}")

                componentType = self.vertex_data_type_to_accessor_data_types \
                    .get(element["dataType"], None)

                if componentType is None:
                    raise NotImplementedError(f"Don't have glTF accessor type for corresponding EPVR vertex data type: {element["dataType"]}")

                accessor_data = {
                    "bufferView": vertexBufferView,
                    "byteOffset": element["offset"],
                    # https://github.com/KhronosGroup/glTF/blob/master/specification/2.0/README.md#accessor-element-size
                    "componentType": componentType,
                    "count": numVertices,
                    "type": accessorType
                }

                # Make bounding box for position.
                if name == "POSITION" and hasnumpy:
                    # Import single vertex buffer.
                    data = np.frombuffer(mesh.vertexElementData[0], dtype=np.float32)
                    # 4 = sizeof(float)
                    stride = int(vertexElements["POSITION"]["stride"] / 4)
                    assert data.size % stride == 0, "oh no! the data is not divisible by the stride... did we assume "
                    # Reshape into (-1, stride) to process the interleaved data
                    data = data.reshape(-1, stride)
                    positions = data[:, :3]

                    # get min and max, convert np.array
                    # float32 to list of floats
                    accessor_data["min"] = [float(x) for x in positions.min(axis=0)]
                    accessor_data["max"] = [float(x) for x in positions.max(axis=0)]

                accessorIndex = self.glb.addAccessor(accessor_data)
                print(f"[DEBUG] Creating accessor {accessorIndex} for attribute {name}")
                attributes[name] = accessorIndex

            # POD meshes only have one primitive?
            # https://github.com/KhronosGroup/glTF/blob/master/specification/2.0/README.md#primitive
            print("[Part 02-1] Adding mesh...")
            self.glb.addMesh({
                "primitives": [{
                    "attributes": attributes,
                    "indices": indicesAccessorIndex,
                    "mode": 4,  # triangles
                }],
            })

def main():
    # Create argparse instance and add arguments.
    parser = argparse.ArgumentParser(description="Converts POD models from Miitomo to glTF (.glb) format.")

    # Add positional arguments.
    parser.add_argument("pod_path", type=str, help="Path to the input POD file. The XML and textures are expected to be relative to this.")
    parser.add_argument("glb_path", type=str, help="Path to the output glTF model/.glb file.")

    # Embed images in GLB?
    parser.add_argument("-e", "--embed-image", action="store_true", help="Embed images in the .glb itself, rather than alongside the model file. Needed to load the model in web browsers.")

    # Convert Miitomo normal maps into a more standard format.
    parser.add_argument("-n", "--miitomo-normal-fix", action="store_true", help="Required to properly render the normal maps in programs like Blender.")

    # Optional arguments to specify PVRTexTool paths.
    parser.add_argument("--pvrtextool-path", type=str, help="Path to PVRTexTool.")
    args = parser.parse_args()

    global pathto, pathout  # Used when converting textures.
    pathto = args.pod_path
    pathout = args.glb_path

    # Set and PVRTexTool paths.
    if args.pvrtextool_path:
        PVR_TEX_TOOL_PATH = args.pvrtextool_path

    global embedimage
    if args.embed_image is not None:
        print("[DEBUG] Embedding all images in the output .glb.")
        embedimage = args.embed_image

    # Check if a companion XML exists with the POD.
    expected_xml_path = str(os.path.basename(pathto)).replace(".pod", "_model.xml")
    print(f"[DEBUG] Expected XML path for this POD: {expected_xml_path}")

    global xmlroot  # Global that's initialized to None.
    for root, dirs, files in os.walk(os.path.dirname(pathto)):
        for file in files:
            if file != expected_xml_path:
                continue  # Skip if this file is not expected.
            # File has been found:
            print(f"[XML] XML file found: {str(file)}")
            xmlpath = os.path.join(os.path.dirname(pathto), file)
            xmldata = etree.parse(xmlpath)
            xmlroot = xmldata.getroot()  # Global
            print(f"Model is called \"{xmlroot.attrib["Name"]}\"")

    converter = POD2GLB.open(pathto)
    converter.save(pathout)

if __name__ == "__main__":
    main()
