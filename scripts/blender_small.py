import bpy
import os, math

bpy.context.active_object.select_set(True)
bpy.ops.object.delete()
io_folder="D:/Mesh/blender/small"
obj_path = os.path.join(io_folder, "scene.obj")
bpy.ops.import_scene.obj(filepath=obj_path)

tx = 0.0
ty = 0.0
tz = -5.0

rx = 180.0
ry = 0.0
rz = 0.0


pi = 3.14159265


camera = bpy.data.objects['Camera']

# Set camera rotation in euler angles
camera.rotation_mode = 'XYZ'
camera.rotation_euler[0] = rx*(pi/180.0)
camera.rotation_euler[1] = ry*(pi/180.0)
camera.rotation_euler[2] = rz*(pi/180.0)

# Set camera translation
camera.location.x = tx
camera.location.y = ty
camera.location.z = tz


# Set up rendering of depth map
bpy.context.scene.use_nodes = True
tree = bpy.context.scene.node_tree
links = tree.links
bpy.context.scene.render.image_settings.file_format = "OPEN_EXR"
bpy.context.scene.render.image_settings.color_depth = '32'
bpy.context.scene.render.image_settings.color_mode = 'RGB'

bpy.context.view_layer.use_pass_normal = True 

# Clear default nodes
for n in tree.nodes:
    tree.nodes.remove(n)

# Create input render layer node.
render_layers = tree.nodes.new('CompositorNodeRLayers')

depth_file_output = tree.nodes.new(type="CompositorNodeOutputFile")
depth_file_output.label = 'Depth Output'
links.new(render_layers.outputs['Depth'], depth_file_output.inputs[0])

scale_normal = tree.nodes.new(type="CompositorNodeMixRGB")
scale_normal.blend_type = 'MULTIPLY'
scale_normal.inputs[2].default_value = (0.5, 0.5, 0.5, 1)
links.new(render_layers.outputs['Normal'], scale_normal.inputs[1])
bias_normal = tree.nodes.new(type="CompositorNodeMixRGB")
bias_normal.blend_type = 'ADD'
bias_normal.inputs[2].default_value = (0.5, 0.5, 0.5, 0)
links.new(scale_normal.outputs[0], bias_normal.inputs[1])
normal_file_output = tree.nodes.new(type="CompositorNodeOutputFile")
normal_file_output.label = 'Normal Output'
links.new(bias_normal.outputs[0], normal_file_output.inputs[0])

image_file_output = tree.nodes.new(type="CompositorNodeOutputFile")
image_file_output.label = 'Image'
links.new(render_layers.outputs['Image'], image_file_output.inputs[0])

scene = bpy.context.scene
scene.render.resolution_x = 1280
scene.render.resolution_y = 720

scene.render.resolution_percentage = 100
cam = scene.objects['Camera']

# fov
cam.data.angle = 10*(math.pi/180.0)

for output_node in [depth_file_output, normal_file_output, image_file_output]:
    output_node.base_path = ''

scene.render.filepath = os.path.join(io_folder, "blender")
depth_file_output.file_slots[0].path = scene.render.filepath + 'depth_'
normal_file_output.file_slots[0].path = scene.render.filepath + 'normal_'
image_file_output.file_slots[0].path = scene.render.filepath + 'image_'

bpy.ops.render.render()
