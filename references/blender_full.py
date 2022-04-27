import bpy
import os, math

def import_obj(io_folder=""):

    bpy.context.active_object.select_set(True)
    bpy.ops.object.delete()

    obj_path = os.path.join(io_folder, "scene.obj")
    bpy.ops.import_scene.obj(filepath=obj_path)

def main(
    io_folder="D:/Mesh/blender/small", load=True,
    format="OPEN_EXR", x=1280, y=720, 
    depth=True, normal=False, albedo=False,
    camera_location=(0, 2, -3), views=5
):
    if format == "PNG":
        color_depth = "8"
    elif format == "OPEN_EXR":
        color_depth = "32"
    
    # Set up
    scale = 1.
    depth_scale = 1.4
    edge_split = True
    remove_doubles = True
    context = bpy.context
    scene = bpy.context.scene
    render = bpy.context.scene.render

    render.engine = "BLENDER_EEVEE"
    render.image_settings.color_mode ="RGBA"
    render.image_settings.file_format = format
    render.image_settings.color_depth = color_depth
    render.resolution_x = x
    render.resolution_y = y
    render.resolution_percentage = 100
    render.film_transparent = True

    scene.use_nodes = True
    scene.view_layers["ViewLayer"].use_pass_normal = True
    scene.view_layers["ViewLayer"].use_pass_diffuse_color = True
    scene.view_layers["ViewLayer"].use_pass_object_index = True

    nodes = bpy.context.scene.node_tree.nodes
    links = bpy.context.scene.node_tree.links

    # Clear default nodes
    for n in nodes:
        nodes.remove(n)

    render_layers = nodes.new('CompositorNodeRLayers')

    if depth:
        depth_file_output = nodes.new(type="CompositorNodeOutputFile")
        depth_file_output.label = 'Depth Output'
        depth_file_output.base_path = ''
        depth_file_output.file_slots[0].use_node_format = True
        depth_file_output.format.file_format = format
        depth_file_output.format.color_depth = color_depth
        if format == 'OPEN_EXR':
            links.new(render_layers.outputs['Depth'], depth_file_output.inputs[0])
        else:
            depth_file_output.format.color_mode = "BW"

            # Remap as other types can not represent the full range of depth.
            map = nodes.new(type="CompositorNodeMapValue")
            #TODO Size is chosen kind of arbitrarily, try out until you're satisfied with resulting depth map.
            map.offset = [-0.7]
            map.size = [depth_scale]
            map.use_min = True
            map.min = [0]

            links.new(render_layers.outputs['Depth'], map.inputs[0])
            links.new(map.outputs[0], depth_file_output.inputs[0])
    
    if normal:
        scale_node = nodes.new(type="CompositorNodeMixRGB")
        scale_node.blend_type = "MULTIPLY"
        # scale_node.use_alpha = True
        scale_node.inputs[2].default_value = (0.5, 0.5, 0.5, 1)
        links.new(render_layers.outputs['Normal'], scale_node.inputs[1])

        bias_node = nodes.new(type="CompositorNodeMixRGB")
        bias_node.blend_type = 'ADD'
        # bias_node.use_alpha = True
        bias_node.inputs[2].default_value = (0.5, 0.5, 0.5, 0)
        links.new(scale_node.outputs[0], bias_node.inputs[1])

        normal_file_output = nodes.new(type="CompositorNodeOutputFile")
        normal_file_output.label = 'Normal Output'
        normal_file_output.base_path = ''
        normal_file_output.file_slots[0].use_node_format = True
        normal_file_output.format.file_format = format
        links.new(bias_node.outputs[0], normal_file_output.inputs[0])
    
    if albedo:
        alpha_albedo = nodes.new(type="CompositorNodeSetAlpha")
        links.new(render_layers.outputs['DiffCol'], alpha_albedo.inputs['Image'])
        links.new(render_layers.outputs['Alpha'], alpha_albedo.inputs['Alpha'])

        albedo_file_output = nodes.new(type="CompositorNodeOutputFile")
        albedo_file_output.label = 'Albedo Output'
        albedo_file_output.base_path = ''
        albedo_file_output.file_slots[0].use_node_format = True
        albedo_file_output.format.file_format = format
        albedo_file_output.format.color_mode = 'RGBA'
        albedo_file_output.format.color_depth = color_depth
        links.new(alpha_albedo.outputs['Image'], albedo_file_output.inputs[0])
    
    id_file_output = nodes.new(type="CompositorNodeOutputFile")
    id_file_output.label = 'ID Output'
    id_file_output.base_path = ''
    id_file_output.file_slots[0].use_node_format = True
    id_file_output.format.file_format = format
    id_file_output.format.color_depth = color_depth

    if format == 'OPEN_EXR':
        links.new(render_layers.outputs['IndexOB'], id_file_output.inputs[0])
    else:
        id_file_output.format.color_mode = 'BW'

        divide_node = nodes.new(type='CompositorNodeMath')
        divide_node.operation = 'DIVIDE'
        divide_node.use_clamp = False
        divide_node.inputs[1].default_value = 2**int(color_depth)

        links.new(render_layers.outputs['IndexOB'], divide_node.inputs[0])
        links.new(divide_node.outputs[0], id_file_output.inputs[0])

    # Load scene obj
    if load:
        import_obj(io_folder)
    obj = bpy.context.selected_objects[0]
    context.view_layer.objects.active = obj

    # Possibly disable specular shading
    for slot in obj.material_slots:
        node = slot.material.node_tree.nodes['Principled BSDF']
        node.inputs['Specular'].default_value = 0.05

    if scale != 1:
        bpy.ops.transform.resize(value=(scale,scale,scale))
        bpy.ops.object.transform_apply(scale=True)
    if remove_doubles:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.remove_doubles()
        bpy.ops.object.mode_set(mode='OBJECT')
    if edge_split:
        bpy.ops.object.modifier_add(type='EDGE_SPLIT')
        context.object.modifiers["EdgeSplit"].split_angle = 1.32645
        bpy.ops.object.modifier_apply(modifier="EdgeSplit")
    
    # Set objekt IDs
    obj.pass_index = 1

    # Make light just directional, disable shadows.
    light = bpy.data.lights['Light']
    light.type = 'SUN'
    light.use_shadow = False
    # Possibly disable specular shading:
    light.specular_factor = 1.0
    light.energy = 10.0

    # Add another light source so stuff facing away from light is not completely dark
    bpy.ops.object.light_add(type='SUN')
    light2 = bpy.data.lights['Sun']
    light2.use_shadow = False
    light2.specular_factor = 1.0
    light2.energy = 0.015
    bpy.data.objects['Sun'].rotation_euler = bpy.data.objects['Light'].rotation_euler
    bpy.data.objects['Sun'].rotation_euler[0] += 180

    # Place Camera
    cam = scene.objects['Camera']
    cam.location = camera_location
    cam.data.lens = 35
    cam.data.sensor_width = 32

    cam_constraint = cam.constraints.new(type='TRACK_TO')
    cam_constraint.track_axis = 'TRACK_NEGATIVE_Z'
    cam_constraint.up_axis = 'UP_Y'

    cam_empty = bpy.data.objects.new("Empty", None)
    cam_empty.location = (0, 0, 0)
    cam.parent = cam_empty

    scene.collection.objects.link(cam_empty)
    context.view_layer.objects.active = cam_empty
    cam_constraint.target = cam_empty

    stepsize = 360.0 / views
    rotation_mode = 'XYZ'

    model_identifier = os.path.split(os.path.split(io_folder)[0])[1]
    fp = os.path.join(os.path.abspath(io_folder), model_identifier, model_identifier)

    # Render and output
    for i in range(0, views):
        print("Rotation {}, {}".format((stepsize * i), math.radians(stepsize * i)))

        render_file_path = fp + '_r_{0:03d}'.format(int(i * stepsize))

        scene.render.filepath = render_file_path
        if depth:
            depth_file_output.file_slots[0].path = render_file_path + "_depth"
        if normal:
            normal_file_output.file_slots[0].path = render_file_path + "_normal"
        if albedo:
            albedo_file_output.file_slots[0].path = render_file_path + "_albedo"
        id_file_output.file_slots[0].path = render_file_path + "_id"

        bpy.ops.render.render(write_still=True)  # render still

        cam_empty.rotation_euler[2] += math.radians(stepsize)

if __name__ == "__main__":
    main()