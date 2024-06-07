# PVR Model Extractor (GLB2FBX)

Crappy Python decompiler (made even crappier, but hey, it works) for the [PowerVR model]() format (`.pod`), built for ripping models from Nintendo's mobile games (particularly Miitomo). It includes utils to convert `.pod` models to the binary glTF (`.glb`) format.

This tool works, but please make an issue in case for other models that break this extractor! This extractor was intended for Miitomo - if there was a better way I could have implemented some fixes let me know!

### Requirements

* Python 3.5 or above (Tested with Python 3.12)
* PVRTexTool from the [Imgination Technology Website](https://developer.imaginationtech.com/solutions/pvrtextool/)
* PVRTexTool CLI (instructions can be found on page 28 of the [PVRTexTool User Manual](https://docs.imgtec.com/tools-manuals/pvrtextool-manual/html/topics/introduction.html)). It is assumed to be located in the same directory as `extract.py`, so you may need to change `PVR_TEX_TOOL_PATH` to suit your setup.
* A glTF plugin for your 3D tool of choice, such as [this glTF plugin for Blender](https://docs.blender.org/manual/en/latest/addons/import_export/scene_gltf2.html). This will let you load .gltf models. 

Optionally, you can install Noesis to automagically convert the GLB to FBX! [You can download Noesis here!](https://www.richwhitehouse.com/index.php?content=inc_projects.php&showproject=91)

### Usage

`extract.py` can be used to convert `.pod` models to the `.glb` model format:

```bash
python3 extract.py <.pod model path> <.glb output path> <-f>
```

Textures are assumed to be in the same directory as extract.py
