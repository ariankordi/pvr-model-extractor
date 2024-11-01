# PVR Model Extractor (POD2GLB)

Crappy Python decompiler (made even crappier, but hey, it works) for the [PowerVR model]() format (`.pod`), built for ripping models from Nintendo's mobile games (particularly Miitomo). It includes utils to convert `.pod` models to the binary glTF (`.glb`) format.

This tool works, but please make an issue in case for other models that break this extractor! This extractor was intended for Miitomo - if there was a better way I could have implemented some fixes let me know!

### Requirements

* Python 3.12 or above (Tested with Python 3.12)
* PVRTexTool from the [Imgination Technology Website](https://developer.imaginationtech.com/solutions/pvrtextool/)
`PVR_TEX_TOOL_PATH` to suit your setup.
* A glTF plugin for your 3D tool of choice, such as [this glTF plugin for Blender](https://docs.blender.org/manual/en/latest/addons/import_export/scene_gltf2.html). This will let you load .gltf models. 

Optionally, you can install Noesis to automagically convert the GLB to FBX! [You can download Noesis here!](https://www.richwhitehouse.com/index.php?content=inc_projects.php&showproject=91)

### Usage

`extract.py` can be used to convert `.pod` models to the `.glb` model format:

```bash
python3 extract.py <.pod model path> <.glb output path> <-f>
```

Textures are assumed to be in the same directory as extract.py

### Installation Steps
```
steps:

(All download links in the GitHub repo's README.md.)
(This assumes you have Python 3.12.)

Download POD2GLB.
Register for a Imagination Technologies account, and then download and install PVRTexTool.
Then move PVRTexToolCLI.exe/PVRTexToolCLI to the root of the POD2GLB script.
(Optionally, you can also download Noesis and put it in the root of the script to auto-convert it to .fbx if you put the -f option at the end.)
After that, launch Command Prompt.
Type in "pip install numpy pillow".
Then you can now convert the pod model! Here's the anatomy of the command:
python pod2glb.py (pod file) (glb file) (-f if you have noesis)

It should generate a GLB (or if you have the -f option, a companion FBX file) to be used in Blender or other sources. I recommend you use the FBX.

Recommended texture settings for Miitomo/Any other Mii game models:
Change 'Repeat' to 'Mirror' to correct the textures.```
