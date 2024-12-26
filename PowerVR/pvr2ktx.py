#!/usr/bin/python3

import sys
import struct
from PVRTexture import PVRTexture, PixelFormat

def map_pvr_format_to_gl(pvr_format):
    # Map PVR pixel format to OpenGL internal format constants
    pvr_to_gl_format = {
        PixelFormat.PVRTC_2BPP_RGB: 0x8C01,     # GL_COMPRESSED_RGB_PVRTC_2BPPV1_IMG
        PixelFormat.PVRTC_2BPP_RGBA: 0x8C03,    # GL_COMPRESSED_RGBA_PVRTC_2BPPV1_IMG
        PixelFormat.PVRTC_4BPP_RGB: 0x8C00,     # GL_COMPRESSED_RGB_PVRTC_4BPPV1_IMG
        PixelFormat.PVRTC_4BPP_RGBA: 0x8C02,    # GL_COMPRESSED_RGBA_PVRTC_4BPPV1_IMG
        PixelFormat.ETC1: 0x8D64,               # GL_ETC1_RGB8_OES
        PixelFormat.ETC2_RGB: 0x9274,           # GL_COMPRESSED_RGB8_ETC2
        PixelFormat.ETC2_RGBA: 0x9278,          # GL_COMPRESSED_RGBA8_ETC2_EAC
        # Add more mappings as needed
    }
    return pvr_to_gl_format.get(pvr_format, None)

def map_gl_base_format(gl_internal_format):
    # Map GL internal format to base format
    gl_base_format_map = {
        0x8C01: 0x1907,  # GL_RGB
        0x8C03: 0x1908,  # GL_RGBA
        0x8C00: 0x1907,  # GL_RGB
        0x8C02: 0x1908,  # GL_RGBA
        0x8D64: 0x1907,  # GL_RGB
        0x9274: 0x1907,  # GL_RGB
        0x9278: 0x1908,  # GL_RGBA
        # Add more mappings as needed
    }
    return gl_base_format_map.get(gl_internal_format, None)

def pvr_to_ktx(pvr_file_path, ktx_file):
    # Load the PVR texture
    texture = PVRTexture.from_file(pvr_file_path)

    # Extract mipmaps
    mipmaps = texture.extract_mipmaps()

    # Prepare the KTX header
    ktx_header = bytearray()
    ktx_header.extend(b'\xABKTX 11\xBB\r\n\x1A\n')  # identifier
    ktx_header.extend(struct.pack('<I', 0x04030201))  # endianness
    ktx_header.extend(struct.pack('<I', 0))  # glType (0 for compressed data)
    ktx_header.extend(struct.pack('<I', 1))  # glTypeSize
    ktx_header.extend(struct.pack('<I', 0))  # glFormat
    glInternalFormat = map_pvr_format_to_gl(texture.pixel_format)
    if glInternalFormat is None:
        raise NotImplementedError(f"Unsupported PVR pixel format: {texture.pixel_format}")

    ktx_header.extend(struct.pack('<I', glInternalFormat))  # glInternalFormat
    glBaseInternalFormat = map_gl_base_format(glInternalFormat)
    if glBaseInternalFormat is None:
        raise NotImplementedError(f"Unsupported GL internal format: {hex(glInternalFormat)}")

    ktx_header.extend(struct.pack('<I', glBaseInternalFormat))  # glBaseInternalFormat
    ktx_header.extend(struct.pack('<I', texture.width))  # pixelWidth
    ktx_header.extend(struct.pack('<I', texture.height))  # pixelHeight
    ktx_header.extend(struct.pack('<I', 0))  # pixelDepth
    ktx_header.extend(struct.pack('<I', 0))  # numberOfArrayElements
    ktx_header.extend(struct.pack('<I', texture.num_faces))  # numberOfFaces
    ktx_header.extend(struct.pack('<I', texture.mipmap_count))  # numberOfMipmapLevels
    ktx_header.extend(struct.pack('<I', 0))  # bytesOfKeyValueData

    # Write to KTX file handle
    ktx_file.write(ktx_header)
    for mipmap_data in mipmaps:
        image_size = len(mipmap_data)
        # Write imageSize field
        ktx_file.write(struct.pack('<I', image_size))
        # Write image data
        ktx_file.write(mipmap_data)
        # 4-byte alignment padding
        padding = (3 - ((image_size + 3) % 4))
        if padding != 0:
            ktx_file.write(b'\x00' * padding)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python pvr2ktx.py input.pvr output.ktx")
        sys.exit(1)

    pvr_file = sys.argv[1]
    ktx_file = sys.argv[2]
    with open(ktx_file, 'wb') as f:
        pvr_to_ktx(pvr_file, f)
    print(f"Converted {pvr_file} to {ktx_file} successfully.")
