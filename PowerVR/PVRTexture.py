# https://github.com/powervr-graphics/WebGL_SDK/blob/4.0/Tools/PVRTexture.js
# http://cdn.imgtec.com/sdk-documentation/PVR%20File%20Format.Specification.pdf

# https://github.com/GerbilSoft/rom-properties/blob/master/src/librptexture/fileformat/pvr3_structs.h
# https://github.com/cocos/cocos-engine/blob/v3.8.6/cocos/asset/assets/image-asset.ts
# https://github.com/nrabinowitz/loaders.gl/blob/master/modules/basis/src/lib/parsers/parse-compressed-texture.js

import struct
from enum import IntEnum, IntFlag
from typing import Optional, List, Tuple
from os import path

# Define Enums for Channel Types, Pixel Formats, Color Spaces, and Flags.

class ChannelTypes(IntEnum):
    UnsignedByteNorm = 0
    SignedByteNorm = 1
    UnsignedByte = 2
    SignedByte = 3
    UnsignedShortNorm = 4
    SignedShortNorm = 5
    UnsignedShort = 6
    SignedShort = 7
    UnsignedIntegerNorm = 8
    SignedIntegerNorm = 9
    UnsignedInteger = 10
    SignedInteger = 11
    SignedFloat = 12
    Float = 12  # Deprecated
    UnsignedFloat = 13

class PixelFormat(IntEnum):
    # PowerVR3 Pixel Formats
    PVRTC_2BPP_RGB = 0
    PVRTC_2BPP_RGBA = 1
    PVRTC_4BPP_RGB = 2
    PVRTC_4BPP_RGBA = 3
    PVRTCII_2BPP = 4
    PVRTCII_4BPP = 5
    ETC1 = 6
    DXT1 = 7
    DXT2 = 8
    DXT3 = 9
    DXT4 = 10
    DXT5 = 11
    BC1 = DXT1
    BC2 = DXT3
    BC3 = DXT5
    BC4 = 12
    BC5 = 13
    BC6 = 14
    BC7 = 15
    UYVY = 16
    YUY2 = 17
    BW1bpp = 18
    R9G9B9E5 = 19
    RGBG8888 = 20
    GRGB8888 = 21
    ETC2_RGB = 22
    ETC2_RGBA = 23
    ETC2_RGB_A1 = 24
    EAC_R11 = 25
    EAC_RG11 = 26
    ASTC_4x4 = 27
    ASTC_5x4 = 28
    ASTC_5x5 = 29
    ASTC_6x5 = 30
    ASTC_6x6 = 31
    ASTC_8x5 = 32
    ASTC_8x6 = 33
    ASTC_8x8 = 34
    ASTC_10x5 = 35
    ASTC_10x6 = 36
    ASTC_10x8 = 37
    ASTC_10x10 = 38
    ASTC_12x10 = 39
    ASTC_12x12 = 40
    ASTC_3x3x3 = 41
    ASTC_4x3x3 = 42
    ASTC_4x4x3 = 43
    ASTC_4x4x4 = 44
    ASTC_5x4x4 = 45
    ASTC_5x5x4 = 46
    ASTC_5x5x5 = 47
    ASTC_6x5x5 = 48
    ASTC_6x6x5 = 49
    ASTC_6x6x6 = 50
    MAX = 51

class ColorSpace(IntEnum):
    RGB = 0      # Linear RGB
    sRGB = 1     # sRGB
    MAX = 2

class PowerVR3Flags(IntFlag):
    COMPRESSED = 1 << 0
    PREMULTIPLIED = 1 << 1

class MetadataKeys(IntEnum):
    TEXTURE_ATLAS = 0
    NORMAL_MAP = 1
    CUBE_MAP = 2
    ORIENTATION = 3
    BORDER = 4
    PADDING = 5

# Define data structures corresponding to the C structs.

class PowerVR3Header:
    def __init__(self, data: bytes):
        if len(data) < 52:
            raise ValueError("Insufficient data for PowerVR3 Header")
        (
            self.version,
            self.flags,
            self.pixel_format,
            self.channel_depth,
            self.color_space,
            self.channel_type,
            self.height,
            self.width,
            self.depth,
            self.num_surfaces,
            self.num_faces,
            self.mipmap_count,
            self.metadata_size
        ) = struct.unpack("<13I", data[:52])

        # Determine endianness
        if self.version == 0x03525650:
            self.endian = '<'  # Little endian
        elif self.version == 0x50565203:
            self.endian = '>'  # Big endian
            # Re-parse with big endian
            (
                self.version,
                self.flags,
                self.pixel_format,
                self.channel_depth,
                self.color_space,
                self.channel_type,
                self.height,
                self.width,
                self.depth,
                self.num_surfaces,
                self.num_faces,
                self.mipmap_count,
                self.metadata_size
            ) = struct.unpack(">13I", data[:52])
        else:
            raise ValueError("Unknown PowerVR3 version")

class LegacyPVRHeaderV2:
    def __init__(self, data: bytes):
        if len(data) < 48:
            raise ValueError("Insufficient data for Legacy PVR V2 Header")
        (
            self.header_size,
            self.height,
            self.width,
            self.mipmap_count,
            self.pixel_format_and_flags,
            self.data_size,
            self.bit_count,
            self.red_bit_mask,
            self.green_bit_mask,
            self.blue_bit_mask,
            self.alpha_bit_mask,
            self.magic,
            self.num_surfaces
        ) = struct.unpack("<13I", data[:52])

        if self.magic != 0x21525650:
            raise ValueError("Invalid magic number for Legacy PVR V2 Header")

class LegacyPVRHeaderV1:
    def __init__(self, data: bytes):
        if len(data) < 44:
            raise ValueError("Insufficient data for Legacy PVR V1 Header")
        (
            self.header_size,
            self.height,
            self.width,
            self.mipmap_count,
            self.pixel_format_and_flags,
            self.data_size,
            self.bit_count,
            self.red_bit_mask,
            self.green_bit_mask,
            self.blue_bit_mask,
            self.alpha_bit_mask
        ) = struct.unpack("<11I", data[:44])

class PVRTexture:
    PVR3_MAGIC = 0x03525650
    PVR3_MAGIC_SWAP = 0x50565203
    LEGACY_PVR_V2_MAGIC = 0x21525650
    LEGACY_PVR_V1_HEADER_SIZE = 44
    LEGACY_PVR_V2_HEADER_SIZE = 52
    PVR3_HEADER_SIZE = 52

    def __init__(self):
        self.name: str = ""
        self.version: int = self.PVR3_MAGIC
        self.flags: int = 0
        self.pixel_format_h: int = 0
        self.pixel_format_l: int = 0
        self.color_space: ColorSpace = ColorSpace.RGB
        self.channel_type: ChannelTypes = ChannelTypes.UnsignedByteNorm
        self.height: int = 1
        self.width: int = 1
        self.depth: int = 1
        self.num_surfaces: int = 1
        self.num_faces: int = 1
        self.mipmap_count: int = 1
        self.metadata_size: int = 0
        self.pixel_format: Optional[PixelFormat] = None
        self.compressed_data: bytes = b""
        self.metadata: dict = {}

    # NOTE: below are camelcase bc that is what the original did
    def setName(self, name: str):
        self.name = path.splitext(name)[0]

    def getPath(self, directory: str = "./", extension: str = ".pvr") -> str:
        return path.join(directory, self.name + extension)

    @classmethod
    def from_file(cls, file_path: str) -> 'PVRTexture':
        instance = cls()
        instance.setName(file_path)  # set_name(file_path)
        with open(file_path, 'rb') as f:
            data = f.read()
            instance.parse(data)
        return instance

    def parse(self, data: bytes):
        if len(data) < 4:
            raise ValueError("Data too short to determine PVR version")

        magic = struct.unpack("<I", data[:4])[0]

        if magic in [self.PVR3_MAGIC, self.PVR3_MAGIC_SWAP]:
            self._parse_pvr3(data)
        elif magic == self.LEGACY_PVR_V2_MAGIC:
            self._parse_legacy_v2(data)
        else:
            # Attempt to parse as Legacy V1
            self._parse_legacy_v1(data)

    def _parse_pvr3(self, data: bytes):
        header_data = data[:self.PVR3_HEADER_SIZE]
        header = PowerVR3Header(header_data)
        self.version = header.version
        self.flags = header.flags
        self.pixel_format = PixelFormat(header.pixel_format) if header.pixel_format in PixelFormat.__members__.values() else None
        self.color_space = ColorSpace(header.color_space) if header.color_space in ColorSpace.__members__.values() else ColorSpace.RGB
        self.channel_type = ChannelTypes(header.channel_type) if header.channel_type in ChannelTypes.__members__.values() else ChannelTypes.UnsignedByteNorm
        self.height = header.height
        self.width = header.width
        self.depth = header.depth
        self.num_surfaces = header.num_surfaces
        self.num_faces = header.num_faces
        self.mipmap_count = header.mipmap_count
        self.metadata_size = header.metadata_size

        # Parse metadata if present
        metadata = {}
        if self.metadata_size > 0:
            metadata_data = data[self.PVR3_HEADER_SIZE:self.PVR3_HEADER_SIZE + self.metadata_size]
            metadata = self._parse_metadata(metadata_data)
        self.metadata = metadata

        # Extract compressed data
        self.compressed_data = data[self.PVR3_HEADER_SIZE + self.metadata_size:]

    def _parse_legacy_v2(self, data: bytes):
        header_size = self.LEGACY_PVR_V2_HEADER_SIZE
        if len(data) < header_size:
            raise ValueError("Data too short for Legacy PVR V2 Header")
        header = LegacyPVRHeaderV2(data[:header_size])
        self.version = header.magic  # Not exactly version, but to identify it's V2
        self.flags = header.pixel_format_and_flags
        self.pixel_format = self._map_legacy_pixel_format(header.pixel_format_and_flags)
        self.color_space = ColorSpace.RGB  # Legacy might not have color space
        self.channel_type = ChannelTypes.UnsignedByteNorm  # Legacy might not have channel type
        self.height = header.height
        self.width = header.width
        self.mipmap_count = header.mipmap_count
        self.compressed_data = data[header_size:]

    def _parse_legacy_v1(self, data: bytes):
        header_size = self.LEGACY_PVR_V1_HEADER_SIZE
        if len(data) < header_size:
            raise ValueError("Data too short for Legacy PVR V1 Header")
        header = LegacyPVRHeaderV1(data[:header_size])
        self.version = 1  # Explicitly set version
        self.flags = header.pixel_format_and_flags
        self.pixel_format = self._map_legacy_pixel_format(header.pixel_format_and_flags)
        self.color_space = ColorSpace.RGB  # Legacy might not have color space
        self.channel_type = ChannelTypes.UnsignedByteNorm  # Legacy might not have channel type
        self.height = header.height
        self.width = header.width
        self.mipmap_count = header.mipmap_count
        self.compressed_data = data[header_size:]

    def _map_legacy_pixel_format(self, fmt: int) -> Optional[PixelFormat]:
        legacy_formats = {
            0x00: PixelFormat.ARGB4444,
            0x01: PixelFormat.ARGB1555,
            0x02: PixelFormat.RGB565,
            0x03: PixelFormat.RGB555,
            0x04: PixelFormat.RGB888,
            0x05: PixelFormat.ARGB8888,
            0x06: PixelFormat.ARGB8332,
            0x07: PixelFormat.I8,
            0x08: PixelFormat.AI88,
            0x09: PixelFormat.BW1bpp,
            0x0A: PixelFormat.VY1UY0,
            0x0B: PixelFormat.Y1VY0U,
            0x0C: PixelFormat.PVRTC2,
            0x0D: PixelFormat.PVRTC4,
            # Add more mappings as needed
        }
        return legacy_formats.get(fmt, None)

    def _parse_metadata(self, data: bytes) -> dict:
        metadata = {}
        offset = 0
        while offset + 12 <= len(data):
            fourcc, key, size = struct.unpack("<III", data[offset:offset + 12])
            offset += 12
            if offset + size > len(data):
                break  # Prevent reading beyond data
            block_data = data[offset:offset + size]
            offset += size
            metadata[key] = block_data
        return metadata

    def get_texture_parameters(self) -> dict:
        return {
            "name": self.name,
            "version": hex(self.version),
            "flags": self.flags,
            "pixel_format": self.pixel_format.name if self.pixel_format else None,
            "color_space": self.color_space.name,
            "channel_type": self.channel_type.name,
            "height": self.height,
            "width": self.width,
            "depth": self.depth,
            "num_surfaces": self.num_surfaces,
            "num_faces": self.num_faces,
            "mipmap_count": self.mipmap_count,
            "metadata_size": self.metadata_size,
            "metadata": self.metadata
        }

    def get_compressed_data(self) -> bytes:
        return self.compressed_data

    def extract_mipmaps(self) -> List[bytes]:
        """
        Extract mipmaps from the compressed data.
        Handles PVRTC alignment and size constraints properly.
        """
        mipmaps = []
        data = self.compressed_data
        offset = 0

        for level in range(self.mipmap_count):
            # Calculate dimensions for the current mipmap level
            level_width = max(1, self.width >> level)
            level_height = max(1, self.height >> level)

            # Calculate the size of the mipmap level
            level_size = self._calculate_mipmap_size(level_width, level_height)

            # Extract the mipmap data
            mipmap_data = data[offset:offset + level_size]
            mipmaps.append(mipmap_data)

            # Update the offset for the next mipmap
            offset += level_size

            # Ensure 4-byte alignment for the next level
            padding = (4 - (level_size % 4)) % 4
            offset += padding

        return mipmaps

    def _calculate_mipmap_size(self, width: int, height: int) -> int:
        """
        Calculate the size of a mipmap level based on the pixel format.
        Handles PVRTC, ETC, and other formats.
        """
        if self.pixel_format is None:
            return 0

        if self.pixel_format in [
            PixelFormat.PVRTC_2BPP_RGB,
            PixelFormat.PVRTC_2BPP_RGBA
        ]:
            # PVRTC 2bpp: Ensure width is at least 16 and height at least 8
            block_width = max(width, 16)
            block_height = max(height, 8)
            return (block_width * block_height) // 4
        elif self.pixel_format in [
            PixelFormat.PVRTC_4BPP_RGB,
            PixelFormat.PVRTC_4BPP_RGBA
        ]:
            # PVRTC 4bpp: Ensure width and height are at least 8
            block_width = max(width, 8)
            block_height = max(height, 8)
            return (block_width * block_height) // 2
        elif self.pixel_format in [
            PixelFormat.ETC1,
            PixelFormat.ETC2_RGB,
            PixelFormat.ETC2_RGBA,
            PixelFormat.ETC2_RGB_A1,
            PixelFormat.EAC_R11,
            PixelFormat.EAC_RG11
        ]:
            # ETC formats: 4x4 blocks, each block is 8 bytes
            block_width = 4
            block_height = 4
            num_blocks = ((width + block_width - 1) // block_width) * ((height + block_height - 1) // block_height)
            return num_blocks * 8
        elif self.pixel_format in [
            PixelFormat.DXT1,
            PixelFormat.DXT2,
            PixelFormat.DXT3,
            PixelFormat.DXT4,
            PixelFormat.DXT5,
            PixelFormat.BC1,
            PixelFormat.BC2,
            PixelFormat.BC3
        ]:
            # S3TC/DXT formats: 4x4 blocks, block size varies
            block_width = 4
            block_height = 4
            bytes_per_block = 8 if self.pixel_format in [PixelFormat.DXT1, PixelFormat.BC1] else 16
            num_blocks = ((width + block_width - 1) // block_width) * ((height + block_height - 1) // block_height)
            return num_blocks * bytes_per_block
        elif self.pixel_format in [
            PixelFormat.ASTC_4x4,
            PixelFormat.ASTC_5x4,
            PixelFormat.ASTC_5x5,
            PixelFormat.ASTC_6x5,
            PixelFormat.ASTC_6x6,
            PixelFormat.ASTC_8x5,
            PixelFormat.ASTC_8x6,
            PixelFormat.ASTC_8x8,
            PixelFormat.ASTC_10x5,
            PixelFormat.ASTC_10x6,
            PixelFormat.ASTC_10x8,
            PixelFormat.ASTC_10x10,
            PixelFormat.ASTC_12x10,
            PixelFormat.ASTC_12x12
        ]:
            # ASTC formats: Calculate based on block dimensions
            block_width, block_height = self._get_astc_block_dimensions(self.pixel_format)
            num_blocks = ((width + block_width - 1) // block_width) * ((height + block_height - 1) // block_height)
            return num_blocks * 16  # ASTC uses 16 bytes per block
        else:
            # Unsupported format
            raise ValueError(f"Unsupported pixel format: {self.pixel_format}")

    def _get_astc_block_dimensions(self, fmt: PixelFormat) -> Tuple[int, int]:
        """
        Return the block dimensions for ASTC formats.
        """
        astc_block_map = {
            PixelFormat.ASTC_4x4: (4, 4),
            PixelFormat.ASTC_5x4: (5, 4),
            PixelFormat.ASTC_5x5: (5, 5),
            PixelFormat.ASTC_6x5: (6, 5),
            PixelFormat.ASTC_6x6: (6, 6),
            PixelFormat.ASTC_8x5: (8, 5),
            PixelFormat.ASTC_8x6: (8, 6),
            PixelFormat.ASTC_8x8: (8, 8),
            PixelFormat.ASTC_10x5: (10, 5),
            PixelFormat.ASTC_10x6: (10, 6),
            PixelFormat.ASTC_10x8: (10, 8),
            PixelFormat.ASTC_10x10: (10, 10),
            PixelFormat.ASTC_12x10: (12, 10),
            PixelFormat.ASTC_12x12: (12, 12),
        }
        return astc_block_map.get(fmt, (4, 4))  # Default to 4x4 if unknown

    def __repr__(self):
        return f"PVRTexture(name={self.name}, width={self.width}, height={self.height}, mipmap_count={self.mipmap_count}, pixel_format={self.pixel_format})"

# Example Usage:
# texture = PVRTexture.from_file("example.pvr")
# params = texture.get_texture_parameters()
# mipmaps = texture.extract_mipmaps()
# print(params)
