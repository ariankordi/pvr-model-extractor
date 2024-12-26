import PIL.Image
from PowerVR.PVRPODLoader import PVRPODLoader
from GLB.GLBExporter import GLBExporter
from xml.etree import ElementTree as etree
from os import path
import os
import subprocess as sp
import platform
import PIL
import argparse

# Override default paths for tools.
# These are overridden by the argparse arguments.
NOESIS_PATH = ""
PVR_TEX_TOOL_PATH = ""

# Global Variables (Don't touch):
FBX_CONV_COMPLETED = False
pathto = ""
pathout = ""
xmlroot = None  # Non-null if an XML was found.
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
        self.convert_textures()
        self.convert_materials()

    def save(self, path):
        print("[Part 06] Saving all data to a GLB format...")
        if xmlroot is not None:
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
        return samplers

    def convert_textures(self):
        # Resolve strings to GLenum values.
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

        alphahotfix = False
        alphaarray = []
        diffusearray = []
        print("[Part 04] Converting textures...")
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

        if pvrtextool_exists:  # Is PVRTexTool available?
            dir_of_input = os.path.dirname(pathto)
            print("[Part 04-2] Now converting all images. Walking path:")

            for root, dirs, files in os.walk(dir_of_input):
                for file in files:
                    if not str(file).endswith(".pvr"):
                        continue  # Skip all non-pvr files.
                    # Input is a pvr file:
                    output = os.path.join(os.path.dirname(pathout), os.path.basename(f"{os.path.splitext(file)[0]}.png"))
                    print(f"[Part 04-2] Converting {file} to png...")
                    print(f"[DEBUG] Running PVRTexTool. Will be saved at {output}")
                    sp.run([
                        pvrtextool_path,
                        "-d", output,
                        "-i", os.path.join(root, file)
                    ], check=True)  # Tool will output to console.

                    pvr_out_fname = f"{os.path.splitext(file)[0]}_Out.pvr"
                    print(f"[HOTFIX] Deleting temporary PVRTexTool _Out file if it exists: {pvr_out_fname}")
                    try:
                        pvr_out_path = os.path.join(root, pvr_out_fname)
                        os.remove(pvr_out_path)
                    except FileNotFoundError:  # Ignore if that _Out file doesn't exist.
                        pass
            if alphahotfix:
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

        else:  # not pvrtextool_exists
            print("[Part 04-2 - WARNING!] Textures will be added, but not converted (pvrtextool_exists == False). You don't have PVRTexToolCLI downloaded or didn't put it in the same directory as the converter (Or you misspelled string inside the PVRTEXTOOL variable if you tried to override the paths!). To download it, go to https://developer.imaginationtech.com/solutions/pvrtextool/. If you have downloaded, move PVRTexToolCLI in the same directory as this script! The usual path (for Windows) is C:\\Imagination Technologies\\PowerVR_Graphics\\PowerVR_Tools\\PVRTexTool\\CLI\\Windows_x86_64.")

        # Enumerate through XML for textures, or not.
        if xmlroot is None:
            for (textureIndex, texture) in enumerate(self.scene.textures):
                print(f"[Part 04-1] Adding image {texture.getPath()}...")

                self.glb.addImage({
                    "uri": texture.getPath(dir="", ext=".png")
                })
                self.glb.addSampler({
                    "magFilter": GLENUM["GL_LINEAR"],
                    "minFilter": GLENUM["GL_LINEAR"],
                    "wrapS": GLENUM["GL_REPEAT"],
                    "wrapT": GLENUM["GL_REPEAT"]
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

                    texture = {
                        "path": str((sampler.find("FileName")).text).replace(".tga", ".png"),
                        "name": str(sampler.attrib['Name'])
                    }
                    mag = sampler.find("GL_TEXTURE_MAG_FILTER")
                    min = sampler.find("GL_TEXTURE_MIN_FILTER")
                    S = sampler.find("GL_TEXTURE_WRAP_S")
                    T = sampler.find("GL_TEXTURE_WRAP_T")

                    magFilter = GLENUM.get(mag.text, GLENUM["GL_LINEAR"])  # Magnificiation filter
                    minFilter = GLENUM.get(min.text, GLENUM["GL_LINEAR"])  # Minification filter
                    wrapS = GLENUM.get(S.text, GLENUM["GL_REPEAT"])  # S (U) Wrapping Mode
                    wrapT = GLENUM.get(T.text, GLENUM["GL_REPEAT"])  # T (V) Wrapping Mode

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

    def convert_materials(self):
        print("[Part 05] Converting materials...")
        if xmlroot is None:
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
                    if str(material.name) != xmmaterial.attrib['Name']:
                        print(f"[DEBUG] Material is not the same! {xmmaterial.attrib['Name']} is not the same as {material.name}")
                        continue

                    for sampler in xmmaterial.findall('Sampler2D'):
                        if sampler.attrib['Name'] == 'uAlbedoTexture':
                            Albedo["baseColorTexture"] = {"index": int(textureIndex)}
                            if sampler.find("UVIdx") is not None:
                                Albedo["texCoord"] = int((sampler.find("UVIdx")).text)
                            textureIndex = textureIndex + 1
                            print("[DEBUG] Has albedo texture!")

                        # NOTE: hasNormal, hasMask are UNUSED!!
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
                            hasAlpha = True

                            # Old alpha code.

                            #Alpha["index"] = int(textureIndex)
                            #if sampler.find("UVIdx") is not None:
                            #    Alpha["texCoord"] = int((sampler.find("UVIdx")).text)
                            #textureIndex += 1
                            print("[DEBUG] Has alpha support!")

                    print(f"[Part 05-1] Adding material {material.name}...")

                    PODMaterial = {
                        "name": material.name,
                        "pbrMetallicRoughness": Albedo,
                        "normalTexture": Normal,
                        "emissiveTexture": Mask,
                        "doubleSided": True,
                    }

                    if hasAlpha:
                        # Old code.
                        #PODMaterial["occlusionTexture"] = Alpha
                        PODMaterial["alphaMode"] = "BLEND"

                    if xmmaterial.find("Culling") is not None:
                        if xmmaterial.find("Culling").text == 'None':
                            print(f"[DEBUG] Material {material.name} does NOT have backface culling on.")
                        else:
                            PODMaterial["doubleSided"] = False
                            print(f"[DEBUG] Material {material.name} has backface culling on.")

                    self.glb.addMaterial(PODMaterial)

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
            if node.animation.matrices is not None:
                print(f"Converting matrix animation data for: {node.name}")
                print("Currently animation porting is not available at this time, sorry :(")
                # keyframes = []
                # matrix = node.animation.matrices.tolist()
                # for x in range(len(matrix)):
                #     if x != 15 or:
                #        rotationX = PVRMaths.PVRMatrix4x4RX3D()


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

            vertexBufferView = self.glb.addBufferView({
                "buffer": 0,
                "byteOffset": self.glb.addData(mesh.vertexElementData[0]),
                "byteStride": vertexElements["POSITION"]["stride"],
                "byteLength": len(mesh.vertexElementData[0]),
            })

            for name in vertexElements:
                element = vertexElements[name]
                componentType = 5126  # FLOAT
                name_to_type = {
                    "TEXCOORD_0": "VEC2",
                    "COLOR_0": "VEC4",
                    # position, normal, tangent: vec3
                    # NOTE: color is R8G8B8A8_UNORM and wont work(???)
                }
                type = name_to_type.get(name, "VEC3")  # vec3 default

                accessor_data = {
                    "bufferView": vertexBufferView,
                    "byteOffset": element["offset"],
                    # https://github.com/KhronosGroup/glTF/blob/master/specification/2.0/README.md#accessor-element-size
                    "componentType": componentType,
                    "count": numVertices,
                    "type": type
                }

                accessorIndex = self.glb.addAccessor(accessor_data)
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

def run_noesis_conversion(file, noesis_path):
    print("Using Noesis to convert to FBX as a way to fix it mainly because I'm lazy. Running now")
    out_file = os.path.basename(f"{os.path.splitext(file)[0]}.fbx")
    noesis_command = [noesis_path, "?cmode", file, out_file]
    if platform != "Windows":
        noesis_command = ["wine"] + noesis_command
        print("[FIX 01] Trying to use Wine to run Noesis")
    sp.run(noesis_command, check=True)
    print("[FIX - FINISH!] Should generate a FBX file - use that instead of the GLB file.")
    global FBX_CONV_COMPLETED
    FBX_CONV_COMPLETED = True

def convert_to_fbx(file):  # Using Noesis/--fix-armature
    print("[FIX 00] Trying to convert the GLB to FBX because Blender doesn't understand the armature this tool generates.")
    # Check if 64-bit version is available
    slash = "\\" if platform == "Windows" else "/"
    noesis_path = f"{os.path.abspath(os.getcwd())}{slash}Noesis64.exe"

    print(f"[DEBUG] Path for Noesis should be: {noesis_path}")
    if path.exists(noesis_path):
        run_noesis_conversion(file, noesis_path)
        return  # Finish and do not go further.
    # not noesis_exists:
    print("[DEBUG] 64-bit version NOT found. Trying 32-bit/override path.")

    # Check if 32-bit version is available
    noesis_path = f"{os.path.abspath(os.getcwd())}{slash}Noesis.exe"
    # Override if user has a path set for Noesis.
    if NOESIS_PATH != "":
        print(f"[OVERRIDE] Overriding path for Noesis with {NOESIS_PATH}")
        noesis_path = NOESIS_PATH
    print(f"[DEBUG] Trying Noesis path: {noesis_path}")
    if path.exists(noesis_path):
        run_noesis_conversion(file, noesis_path)
    else:
        print("[FIX - ERROR!] Fix will NOT continue. You don't have Noesis downloaded or didn't put it in the same directory as the converter (Or you misspelled the NOESIS_PATH variable if you tried to override the paths!). To download it, go to https://www.richwhitehouse.com/index.php?content=inc_projects.php&showproject=91.")

def main():
    # Create argparse instance and add arguments.
    parser = argparse.ArgumentParser(description="Converts POD models from Miitomo to glTF (.glb) format.")

    # Add positional arguments.
    parser.add_argument("pod_path", type=str, help="Path to the input POD file. The XML and textures are expected to be relative to this.")
    parser.add_argument("glb_path", type=str, help="Path to the output glTF model/.glb file.")

    # Optional flag to fix armature/convert to FBX.
    parser.add_argument("-f", "--fix-armature", action="store_true", help="Tries to fix Blender quirks with GLB files by converting it to a FBX file using Noesis.")

    # Optional arguments to specify Noesis/PVRTexTool paths.
    parser.add_argument("--noesis-path", type=str, help="Path to Noesis binary.")
    parser.add_argument("--pvrtextool-path", type=str, help="Path to PVRTexTool.")
    args = parser.parse_args()

    global pathto, pathout  # Used when converting textures.
    pathto = args.pod_path
    pathout = args.glb_path

    # Set Noesis and PVRTexTool paths.
    global NOESIS_PATH, PVR_TEX_TOOL_PATH
    if args.noesis_path:
        NOESIS_PATH = args.noesis_path
    if args.pvrtextool_path:
        PVR_TEX_TOOL_PATH = args.pvrtextool_path

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
            print(f"Model is called \"{xmlroot.attrib['Name']}\"")

    converter = POD2GLB.open(pathto)
    converter.save(pathout)

    if args.fix_armature:
        convert_to_fbx(pathout)
    else:
        print("[DEBUG] Will not convert to FBX as --fix-armature option was not specified.")

if __name__ == "__main__":
    main()
