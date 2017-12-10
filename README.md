This is my attempt at making a Blender addon which lets you import Silkroad Onlines .bsr files.
it is currently barely working and with hardcoded paths, so it probably wont work on your machine unless you edit the hardcoded parts.

The Material Reader is not finished yet, ambient and emissive color is ignored, as well as normals maps, if there are any. There might also be some material files, that crash the parser given that I do not know how the material_entry_flags work yet.

The Mesh Reader currently ignores lightmaps cause I dont know how to parse the lightmap info yet, normals are also ignored as well as any bonedata.

Impl Skeleton Reader

Impl Animation Reader

Figure out why some/most weapon/armor textures have a full non-one alpha channel(aka are completely semi-transparent)

I know that having everything inside one big script file is ugly, but it makes it easier to use in the blender script editor for now. 