#!/usr/bin/python3

import os
import argparse
from PVRTexture import PVRTexture, PixelFormat
import texture2ddecoder
from PIL import Image

def convert_bgra_to_rgba(data: bytes, width: int, height: int) -> bytes:
    """
    Convert BGRA raw data to RGBA format.
    """
    rgba_data = bytearray(len(data))
    for i in range(0, len(data), 4):
        # Swap BGRA to RGBA
        rgba_data[i] = data[i + 2]  # R <- B
        rgba_data[i + 1] = data[i + 1]  # G <- G
        rgba_data[i + 2] = data[i]  # B <- R
        rgba_data[i + 3] = data[i + 3]  # A <- A
    return bytes(rgba_data)

def pvrtexture_to_image(texture):  # input = PVRTexture type
    # Check if the pixel format is supported for decoding
    if texture.pixel_format not in [
        PixelFormat.PVRTC_2BPP_RGB,
        PixelFormat.PVRTC_2BPP_RGBA,
        PixelFormat.PVRTC_4BPP_RGB,
        PixelFormat.PVRTC_4BPP_RGBA,
        PixelFormat.ETC1
    ]:
        raise NotImplementedError(f"Unsupported pixel format: {texture.pixel_format}")

    # Extract the highest resolution mipmap
    mipmaps = texture.extract_mipmaps()
    if not mipmaps:
        raise Exception("No mipmaps found in the PVR file.")

    # Decode the highest resolution mipmap
    compressed_data = mipmaps[0]  # Use the largest mipmap (index 0)
    width, height = texture.width, texture.height

    if texture.pixel_format in [PixelFormat.PVRTC_2BPP_RGB, PixelFormat.PVRTC_2BPP_RGBA]:
        decoded_data = texture2ddecoder.decode_pvrtc(compressed_data, width, height, True)
    elif texture.pixel_format in [PixelFormat.PVRTC_4BPP_RGB, PixelFormat.PVRTC_4BPP_RGBA]:
        decoded_data = texture2ddecoder.decode_pvrtc(compressed_data, width, height, False)
    elif texture.pixel_format == PixelFormat.ETC1:
        decoded_data = texture2ddecoder.decode_etc1(compressed_data, width, height)
    else:
        raise NotImplementedError(f"Decoding for pixel format {texture.pixel_format} is not implemented.")

    # Convert BGRA to RGBA (texture2ddecoder emits BGRA)
    rgba_data = convert_bgra_to_rgba(decoded_data, width, height)

    # Convert the raw RGBA data to a PIL image
    image = Image.frombytes('RGBA', (width, height), rgba_data)
    return image

if __name__ == '__main__':
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Convert PVR textures to PNG format.")
    parser.add_argument('-i', '--input', required=True, help="Path to the input PVR file.")
    parser.add_argument('-d', '--output_dir', required=True, help="Directory to save the output PNG.")
    parser.add_argument('-noout', help="Option is just here to stay compatible with PVRTexTool.", action="store_true")
    args = parser.parse_args()

    # Load the PVR texture
    texture = PVRTexture.from_file(args.input)

    image = pvrtexture_to_image(texture)  # Convert to PIL image

    # Create the output directory if it doesn't exist
    #os.makedirs(args.output_dir, exist_ok=True)
    # Construct the output PNG file path
    #base_name = os.path.splitext(os.path.basename(args.input))[0]
    output_file = args.output_dir  # os.path.join(args.output_dir, f"{base_name}.png")

    image.save(output_file)
    print(f"Converted {args.input} to {output_file} successfully.")
