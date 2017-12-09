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
    root_path = StringProperty(
            name="RootPath",
            description="RootPath",
            default="D:\\sro\\Silkroad\\Data\\",
            )

    filter_glob = StringProperty(
            default="*.bsr",
            options={'HIDDEN'},
            maxlen=255,  # Max internal buffer length, longer would be clamped.
            )

    def execute(self, context):
        return read_bsr(context, self.filepath)

def read_bsr(context, filepath):
    print(filepath)
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
        
        typ = ResourceType(read_int(f))
        name = read_str(f)
        print("[Resource] {}".format(name))
        # HEADEREND
        
        f.seek(p_material)
        mats = create_materials(f)
        f.seek(p_mesh)
        build_mesh(f, flag_0, mats)

        f.seek(p_mesh_group)
        for i in range(0,read_int(f)):
            name = read_str(f)
            # print("[MeshGroup] {}".format(name))
            for ii in range(0,read_int(f)):
                mfi = read_int(f)
                # print("[MeshGroup] {}".format(mfi))
        
    return {'FINISHED'}

def create_materials(f):
    mats = {}
    for i in range(0, read_int(f)):
        mid = read_int(f)
        path = read_str(f)
        path = "D:\\sro\\Silkroad\\Data\\"+path
        with open(path, 'rb') as f:
            version = f.read(12)
            print("[Material] File version: {}".format(version))
            for i in range(0, read_int(f)):
                name = read_str(f)
                diffuse = (read_float(f), read_float(f), read_float(f))
                read_float(f)
                ambient = (read_float(f), read_float(f), read_float(f))
                read_float(f)
                specular = (read_float(f), read_float(f), read_float(f))
                read_float(f)
                emissive = (read_float(f), read_float(f), read_float(f))
                read_float(f)
                read_float(f)
                read_int(f)
                diffuse_map = read_str(f)
                read_float(f)
                read_short(f)
                print("[Material] Diffuse map path: {} {}".format(diffuse_map, bool(f.read(1))))
                mat = bpy.data.materials.new(name=name)
                mat.diffuse_color = diffuse
                mat.diffuse_shader = 'LAMBERT' 
                mat.diffuse_intensity = 1.0
                mat.specular_color = specular
                mat.specular_shader = 'COOKTORR'
                mat.specular_intensity = 1.0
                mat.ambient = 1 # only 1 value?

                p = path.rfind('\\')
                img = bpy.data.images.load(path[:p+1]+diffuse_map.replace(".ddj", ".dds"))
                cTex = bpy.data.textures.new(name, type = 'IMAGE')
                cTex.image = img

                mtex = mat.texture_slots.add()
                mtex.texture = cTex
                mtex.texture_coords = 'UV'
                # mtex.use_map_color_diffuse = True 
                # mtex.use_map_color_emission = True 
                # mtex.emission_color_factor = 0.5
                # mtex.use_map_density = True 
                mtex.mapping = 'FLAT' 

                mats[name] = mat
    return mats

def build_mesh(f, flag, materials):
    mesh_paths = []
    for i in range(0, read_int(f)):
        mesh_path = read_str(f)
        mesh_paths.append(mesh_path)
        if flag == 1:
            read_int(f)
    print(mesh_paths)
    
    meshes = []
    for mesh in mesh_paths:
        with open("D:\\sro\\Silkroad\\Data\\"+mesh, 'rb') as f:
            version = f.read(12)
            print("File version: {}".format(version))
            p_verticies = read_int(f)
            p_bones = read_int(f)
            p_faces = read_int(f)
            p_unk = read_int(f)
            p_unk = read_int(f)
            p_bounding_box = read_int(f)
            p_gates = read_int(f)
            p_collision = read_int(f)
            p_unk = read_int(f)
            p_unk = read_int(f)
            
            flag_0 = read_int(f)
            flag_1 = read_int(f)
            flag_2 = read_int(f)
            flag_lightmap = read_int(f)
            flag_4 = read_int(f)

            name = read_str(f)
            print(name)
            material = read_str(f)
            print(material)
            unk = read_int(f)

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
            for i in range(0, read_int(f)):
                vertex = (read_float(f), read_float(f), read_float(f))
                vert.append(vertex)
                normal = (read_float(f), read_float(f), read_float(f))
                tex_coords.append((read_float(f), -read_float(f)))
                if flag_lightmap > 0:
                    lightmap_coord = (read_float(f), read_float(f))
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