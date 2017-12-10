import bpy
import struct
import bmesh

# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator

from enum import IntEnum
class ResourceType(IntEnum):
        Character = 0x20000
        NPC = 0x20001
        Building = 0x20002
        Artifact = 0x20003
        Nature = 0x20004
        Item = 0x20005
        Other = 0x20006
        CompoundCharacter = 0x30000
        CompoundObject = 0x30002

bl_info = {"name": "Silkroad Resource Loader", "category": "Object"}

class ImportJMXVRES(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "import_sro.bsr"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import .bsr file"

    # ImportHelper mixin class uses this
    filename_ext = ".bsr"
    filter_glob = StringProperty(
            default="*.bsr",
            options={'HIDDEN'},
            maxlen=255,  # Max internal buffer length, longer would be clamped.
            )

    def execute(self, context):
        return read_bsr(context, self.filepath)

def read_bsr(context, filepath):
    root_path = filepath[:filepath.rfind("\\Data\\")+6]
    print("\n[Info] {}".format(filepath))
    with open(filepath, 'rb') as f:
        version = f.read(12)
        print("[Resource] File version: {}".format(version))
        p_material = read_int(f)
        p_mesh = read_int(f)
        p_skeleton = read_int(f)
        p_animation = read_int(f)
        p_mesh_group = read_int(f)
        p_animation_group = read_int(f)
        p_sound_effect= read_int(f)
        p_bounding_box = read_int(f)
        
        flag_0 = read_int(f)
        flag_1 = read_int(f)
        flag_2 = read_int(f)
        flag_3 = read_int(f)
        flag_4 = read_int(f)
        print("[Resource] {}, {}, {}, {}, {}".format(flag_0, flag_1, flag_2, flag_3, flag_4))
        
        typ = ResourceType(read_int(f))
        name = read_str(f)
        print("[Resource] {}".format(name))
        print("[Resource] Type: {:X}".format(typ))
        # HEADEREND
        
        f.seek(p_skeleton)
        create_skeleton(root_path, f)

        bm = bmesh.new()

        f.seek(p_material)
        mats = create_materials(root_path, f)
        f.seek(p_mesh)
        objects = []
        #bpy.ops.object.select_all(action='DESELECT')
        for mesh in build_meshes(root_path, f, flag_0, mats):
            #bm.from_mesh(mesh)
            o = bpy.data.objects.new(name, mesh)
            bpy.context.scene.objects.link(o)
            o.select = True
            objects.append(o)
        #bpy.context.scene.objects.active = bpy.data.objects[name]
        #bpy.ops.object.join()
        #me = bpy.data.meshes.new(name)
        #bm.to_mesh(me)
        #o = bpy.data.objects.new(name, me)
        #bpy.context.scene.objects.link( o )


        f.seek(p_mesh_group)
        for i in range(0,read_int(f)):
            name = read_str(f)
            # print("[MeshGroup] {}".format(name))
            for ii in range(0,read_int(f)):
                mfi = read_int(f)
                # print("[MeshGroup] {}".format(mfi))
        
    return {'FINISHED'}

from mathutils import Vector, Matrix
import math
def create_skeleton(root_path, f):
    for i in range(0, read_int(f)):
        path = read_str(f)
        print("[Skeleton] {}".format(path))
        bpy.ops.object.add(
            type='ARMATURE', 
            enter_editmode=True,
            location=(0, 0, 0))
        ob = bpy.context.object
        ob.show_x_ray = True
        ob.name = path
        amt = ob.data
        amt.name = path
        amt.show_axes = True
        amt.show_names = True
        ttp = {}
        root = None
        bpy.ops.object.mode_set(mode='EDIT')
        with open(root_path+path, 'rb') as f2:
            version = f2.read(12)
            print("[Skeleton] File version: {}".format(version))
            for bi in range(0, read_int(f2)):
                f2.read(1)
                bone = read_str(f2)
                if not root:
                    root = bone
                parent = read_str(f2)
                rotation_to_parent = read_vec(f2, 4)
                translation_to_parent = read_vec(f2, 3)
                rotation_to_origin = read_vec(f2, 4)
                translation_to_origin = read_vec(f2, 3)
                unkRotation = read_vec(f2, 4)
                unkTranslation = read_vec(f2, 3)
                b = amt.edit_bones.new(bone)
                b.use_connect = False
                b.head = translation_to_origin
                b.tail = translation_to_origin
                if parent:
                    b.tail = amt.edit_bones[parent].head
                    b.parent = amt.edit_bones[parent]
                children = []
                for ci in range(0, read_int(f2)):
                    children.append(read_str(f2))
                ttp[bone] = (translation_to_parent, rotation_to_parent, parent, children)
        bpy.ops.object.mode_set(mode='OBJECT')

        patch_bone_recursive(amt, bone, root, ttp)

        mat_rot = Matrix.Rotation(math.radians(90.0), 4, 'X')
        mat_rot = mat_rot * Matrix.Rotation(math.radians(90.0), 4, 'Y')
        mat = mat_rot * Matrix.Scale(-1.0, 4, (1.0, 0.0, 0.0))
        amt.transform(mat)
        f.read(read_int(f))
        f.read(read_int(f))

def patch_bone_recursive(amt, bone, root, ttp):
    cbone = amt.bones[bone]
    if bone == root:
        pass
    else:
        cbone.head_local = ttp[bone][0]
    for c in ttp[bone][3]:
        patch_bone_recursive(amt, c, root, ttp)

def read_vec(f, l):
    return tuple(read_float(f) for _ in range(0, l))

def create_materials(root_path, f):
    mats = {}
    for i in range(0, read_int(f)):
        m_id = read_int(f)
        path = read_str(f)
        path = root_path+path
        with open(path, 'rb') as f2:
            version = f2.read(12)
            print("[Material] File version: {}".format(version))
            for i in range(0, read_int(f2)):
                name = read_str(f2)
                print("[Material] {}".format(name))
                diffuse = (read_float(f2), read_float(f2), read_float(f2))
                diffuse_intensity = read_float(f2)
                print("[Material] Diffuse color: {} {}".format(diffuse, diffuse_intensity))
                ambient = (read_float(f2), read_float(f2), read_float(f2), read_float(f2))
                print("[Material] Ambient color: {} (Blender only supports one global ambient color)".format(ambient))
                specular = (read_float(f2), read_float(f2), read_float(f2))
                specular_intensity = read_float(f2)
                print("[Material] Specular color: {} {}".format(specular, specular_intensity))
                emissive = (read_float(f2), read_float(f2), read_float(f2))
                print("[Material] Emissive color: {} {} (Blender does not support alpha for this)".format(emissive, read_float(f2)))
                print("[Material] Specular Power? {}".format(read_float(f2)))
                material_entry_flags = read_int(f2)
                print("[Material] MaterialEntryFlags {}".format(material_entry_flags))
                diffuse_map = read_str(f2)
                print("[Material] Always 1.0 == {}".format(read_float(f2)))
                print("[Material] {} (0, 24, 2080)".format(read_short(f2)))
                same_dir = f2.read(1) == b'\x00'
                print("[Material] Diffuse map path: {} {}".format(diffuse_map, same_dir))
                if (material_entry_flags & 0b10000000000000) != 0:
                    print("[Material] NormalMap: {}".format(read_str(f2)))
                if (material_entry_flags & 0b100) != 0:
                    print("[Material] {}".format(read_int(f2)))
                mat = bpy.data.materials.new(name=name)
                mat.diffuse_color = diffuse
                mat.diffuse_intensity = diffuse_intensity
                mat.specular_color = specular
                mat.specular_intensity = specular_intensity
                mat.ambient = 1 # Blender only supports one global ambient color it seems
                if material_entry_flags & 0x200 != 0:
                    mat.use_transparency = True
                    mat.alpha = 0.0

                p = path.rfind('\\')
                if same_dir:
                    img = bpy.data.images.load(path[:p+1]+diffuse_map.replace(".ddj", ".dds"))
                else:
                    img = bpy.data.images.load(root_path+diffuse_map.replace(".ddj", ".dds"))
                cTex = bpy.data.textures.new(name, type = 'IMAGE')
                cTex.image = img
                img.use_alpha = material_entry_flags & 0x200 != 0

                mtex = mat.texture_slots.add()
                mtex.texture = cTex
                mtex.texture_coords = 'UV'
                if material_entry_flags & 0x200 != 0:
                    mtex.use_map_alpha = True
                    mtex.alpha_factor = 1.0
                # mtex.use_map_color_diffuse = True 
                # mtex.use_map_color_emission = True 
                # mtex.emission_color_factor = 0.5
                # mtex.use_map_density = True 
                mtex.mapping = 'FLAT' 

                mats[name] = mat
    return mats

def build_meshes(root_path, f, flag, materials):
    mesh_paths = []
    for i in range(0, read_int(f)):
        mesh_path = read_str(f)
        mesh_paths.append(mesh_path)
        if flag == 1:
            read_int(f)
    print("[Resource] {}".format(mesh_paths))
    
    meshes = []
    for mesh in mesh_paths:
        meshes.append(create_mesh(root_path, mesh, flag, materials))
    return meshes

def create_mesh(root_path, mesh, flag, materials):
    with open(root_path+mesh, 'rb') as f:
        version = f.read(12)
        print("[Mesh] File version: {}".format(version))
        p_verticies = read_int(f)
        p_bones = read_int(f)
        p_faces = read_int(f)
        p_unk0 = read_int(f)
        p_unk1 = read_int(f)
        p_bounding_box = read_int(f)
        p_gates = read_int(f)
        p_collision = read_int(f)
        p_unk2 = read_int(f)
        p_unk3 = read_int(f)
        print("[Mesh] unknown_pointers {:X}, {:X}, {:X}, {:X}".format(p_unk0, p_unk1, p_unk2, p_unk3))
        
        flag_0 = read_int(f)
        flag_1 = read_int(f)
        flag_2 = read_int(f)
        flag_lightmap = read_int(f)
        flag_4 = read_int(f)
        print("[Mesh] Flags: {:X}, {:X}, {:X}, {:X}, {:X}".format(flag_0, flag_1, flag_2, flag_lightmap, flag_4))

        name = read_str(f)
        print("[Mesh] Name: {}".format(name))
        material = read_str(f)
        print("[Mesh] Material: {}".format(material))
        unk = read_int(f)
        print("[Mesh] Unk: {}".format(unk))

        me = bpy.data.meshes.new(name)
        me.materials.append(materials[material])
        
        f.seek(p_verticies)
        vert = []
        tex_coords = []
        lightmap_coords = []
        for i in range(0, read_int(f)):
            (x, y, z) = (read_float(f), read_float(f), read_float(f))
            vertex = (z, x, y)
            vert.append(vertex)
            normal = (read_float(f), read_float(f), read_float(f))
            tex_coords.append((read_float(f), -read_float(f)))
            f.read(12)
        f.seek(p_faces)
        faces = []
        for i in range(0, read_int(f)):
            faces.append((read_short(f), read_short(f), read_short(f)))

        me.from_pydata(vert, [], faces)
        me.update()

        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()
        bm.verts.index_update()
        uv_layer = bm.loops.layers.uv.new(name)
        for face in bm.faces:
            for loop in face.loops:
                loop[uv_layer].uv = tex_coords[loop.vert.index]
        bm.to_mesh(me)
        me.update()

        f.seek(p_unk0)
        for i in range(0, read_int(f)):
            # print("[Spam] {} {}".format(read_float(f), read_int(f)))
            pass
        f.seek(p_unk1)
        for i in range(0, read_int(f)):
            # print("[Spam] {} {} {}".format(read_int(f), read_int(f), read_float(f)))
            pass
        return me

#file helper funcs
def read_int(f):
    return int.from_bytes(f.read(4), byteorder='little')

def read_short(f):
    return int.from_bytes(f.read(2), byteorder='little')

import struct
def read_float(f):
    return struct.unpack('f', f.read(4))[0]

def read_str(f):
    len = read_int(f)
    return f.read(len).decode("cp949")

def register():
    bpy.utils.register_class(ImportJMXVRES)


def unregister():
    bpy.utils.unregister_class(ImportJMXVRES)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.import_sro.bsr('INVOKE_DEFAULT')