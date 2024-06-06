# PVR Model Extractor

Crappy Python decompiler (made even crappier, but hey, it works) for the [PowerVR model]() format (`.pod`), built for ripping models from Nintendo's mobile games (particularly Miitomo). It includes utils to convert `.pod` models to the binary glTF (`.glb`) format.

This tool works, but please make an issue in case for other models that break this extractor! This extractor was intended for Miitomo - if there was a better way I could have implemented some fixes let me know!

### Requirements

* Python 3.5 or above
* PVRTexTool from the [PowerVR SDK Tools](https://www.imgtec.com/developers/powervr-sdk-tools/installers/)
* PVRTexTool CLI (instructions can be found on page 28 of the [PVRTexTool User Manual](http://cdn.imgtec.com/sdk-documentation/PVRTexTool.User+Manual.pdf)). It is assumed to be located in the same directory as `extract.py`, so you may need to change `PVR_TEX_TOOL_PATH` to suit your setup.
* A glTF plugin for your 3D tool of choice, such as [this glTF plugin for Blender](https://docs.blender.org/manual/en/dev/addons/io_gltf2.html). This will let you load .gltf models. 

### Usage

`extract.py` can be used to convert `.pod` models to the `.glb` model format:

```bash
python3 extract.py <.pod model path> <.glb output path>
```

Textures are assumed to be in the same directory as extract.py
