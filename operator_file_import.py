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
        
        f.seek(p_material)
        mats = create_materials(root_path, f)
        f.seek(p_mesh)
        build_meshes(root_path, f, flag_0, mats)

        f.seek(p_mesh_group)
        for i in range(0,read_int(f)):
            name = read_str(f)
            # print("[MeshGroup] {}".format(name))
            for ii in range(0,read_int(f)):
                mfi = read_int(f)
                # print("[MeshGroup] {}".format(mfi))
        
    return {'FINISHED'}

def create_materials(root_path, f):
    mats = {}
    for i in range(0, read_int(f)):
        m_id = read_int(f)
        path = read_str(f)
        path = root_path+path
        with open(path, 'rb') as f:
            version = f.read(12)
            print("[Material] File version: {}".format(version))
            for i in range(0, read_int(f)):
                name = read_str(f)
                print("[Material] {}".format(name))
                diffuse = (read_float(f), read_float(f), read_float(f))
                diffuse_intensity = read_float(f)
                print("[Material] Diffuse color: {} {}".format(diffuse, diffuse_intensity))
                ambient = (read_float(f), read_float(f), read_float(f), read_float(f))
                print("[Material] Ambient color: {} (Blender only supports one global ambient color)".format(ambient))
                specular = (read_float(f), read_float(f), read_float(f))
                specular_intensity = read_float(f)
                print("[Material] Specular color: {} {}".format(specular, specular_intensity))
                emissive = (read_float(f), read_float(f), read_float(f))
                print("[Material] Emissive color: {} {} (Blender does not support alpha for this)".format(emissive, read_float(f)))
                print("[Material] Specular Power? {}".format(read_float(f)))
                material_entry_flag = read_int(f)
                print("[Material] MaterialEntryFlags {}".format(material_entry_flag))
                diffuse_map = read_str(f)
                print("[Material] Always 1.0 == {}".format(read_float(f)))
                print("[Material] {} (0, 24, 2080)".format(read_short(f)))
                same_dir = f.read(1) == b'\x00'
                print("[Material] Diffuse map path: {} {}".format(diffuse_map, same_dir))
                if material_entry_flag == 9029:
                    print("[Material] NormalMap: {}".format(read_str(f)))
                if material_entry_flag != 833:
                    print("[Material] {}".format(read_int(f)))
                mat = bpy.data.materials.new(name=name)
                mat.diffuse_color = diffuse
                mat.diffuse_intensity = diffuse_intensity
                mat.specular_color = specular
                mat.specular_intensity = specular_intensity
                mat.ambient = 1 # Blender only supports one global ambient color it seems
                mat.use_transparency = True
                mat.alpha = 0.0

                p = path.rfind('\\')
                if same_dir:
                    img = bpy.data.images.load(path[:p+1]+diffuse_map.replace(".ddj", ".dds"))
                else:
                    img = bpy.data.images.load(root_path+diffuse_map.replace(".ddj", ".dds"))
                cTex = bpy.data.textures.new(name, type = 'IMAGE')
                cTex.image = img
                cTex.use_alpha = True

                mtex = mat.texture_slots.add()
                mtex.texture = cTex
                mtex.texture_coords = 'UV'
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
        create_mesh(root_path, f, mesh, flag, materials)

def create_mesh(root_path, f, mesh, flag, materials):
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
        print("[Mesh] {:X}, {:X}, {:X}, {:X}".format(p_unk0, p_unk1, p_unk2, p_unk3))
        
        flag_0 = read_int(f)
        flag_1 = read_int(f)
        flag_2 = read_int(f)
        flag_lightmap = read_int(f)
        flag_4 = read_int(f)
        print("[Mesh] {:X}, {:X}, {:X}, {:X}, {:X}".format(flag_0, flag_1, flag_2, flag_lightmap, flag_4))

        name = read_str(f)
        print("[Mesh] {}".format(name))
        material = read_str(f)
        print("[Mesh] {}".format(material))
        unk = read_int(f)
        print("[Mesh] {}".format(unk))

        me = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, me)
        obj.data.materials.append(materials[material])
        
        scn = bpy.context.scene
        scn.objects.link(obj)
        scn.objects.active = obj
        obj.select = True

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
        me.update(calc_edges=True)

        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(me)
        bm.verts.ensure_lookup_table()
        bm.verts.index_update()
        uv_layer = bm.loops.layers.uv.new(name)
        for face in bm.faces:
            for loop in face.loops:
                loop[uv_layer].uv = tex_coords[loop.vert.index]
        bmesh.update_edit_mesh(me)
        bpy.ops.object.mode_set(mode='OBJECT')

        f.seek(p_unk0)
        for i in range(0, read_int(f)):
            # print("[Spam] {} {}".format(read_float(f), read_int(f)))
        f.seek(p_unk1)
        for i in range(0, read_int(f)):
            # print("[Spam] {} {} {}".format(read_int(f), read_int(f), read_float(f)))

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