"""
MIT License

Copyright (c) 2018 Julian Bath

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

bl_info = {
    "name": "Auto LOD",
    "category": "Object",
    "author": "Julian Bath"
}

import bpy
from bpy.types import (PropertyGroup, Panel, Operator, UIList)
from bpy.props import (IntProperty, PointerProperty, StringProperty, CollectionProperty, EnumProperty)
import os

class ExcludeFilePath(PropertyGroup):
    value = StringProperty(
        name = "File path",
        subtype = "FILE_PATH"
    )

class Settings(PropertyGroup):
    lod_count = IntProperty(
        name = "LOD count",
        description = "How many lower levels of detail should be generated for each object?",
        default = 1,
        min = 1,
        max = 4
    )

    input_mesh_folder = StringProperty(
        name = "Input mesh folder",
        description = "The path to the folder containing the meshes that need LODs generated.",
        subtype = "DIR_PATH"
    )

    import_excludes = CollectionProperty(type = ExcludeFilePath)

    import_excludes_index = IntProperty(name = "Import excludes index")

    output_mesh_folder = StringProperty(
        name = "Output mesh folder",
        description = "The path to the folder to export meshes to.",
        subtype = "DIR_PATH"
    )

class StringList(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.prop(item, "value")

class AutoLodPanel(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label = "Auto LOD"
    bl_context = "objectmode"
    bl_category = "Auto LOD"

    def draw(self, context):
        self.layout.prop(context.scene.auto_lod_settings, "lod_count")
        self.layout.operator("object.generatelods", text = "Generate LODs")

class HandleExcludeList(Operator):
    bl_idname = "custom.handle_exclude_list"
    bl_label = "Handle Exclude List"
    bl_options = {"UNDO"}

    action = EnumProperty(
        items = (
            ("ADD", "Add", ""),
            ("REMOVE", "Remove", "")
        )
    )

    def invoke(self, context, event):
        settings = context.scene.auto_lod_settings
        if self.action == "ADD":
            settings.import_excludes.add()
        elif self.action == "REMOVE":
            settings.import_excludes_index -= 1
            settings.import_excludes.remove(settings.import_excludes_index)

        return {"FINISHED"}

class GenerateLods(Operator):
    bl_idname = "object.generatelods"
    bl_label = "Generate LODs"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        for current_object in context.selected_objects:
            generate_lods(current_object)

        return {"FINISHED"}

class AutoLodFolderPanel(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label = "Auto LOD Folder"
    bl_context = "objectmode"
    bl_category = "Auto LOD"

    def draw(self, context):
        self.layout.prop(context.scene.auto_lod_settings, "lod_count")
        self.layout.prop(context.scene.auto_lod_settings, "input_mesh_folder")

        self.layout.label("Files to exclude from import:")
        row = self.layout.row()
        row.template_list("StringList", "", context.scene.auto_lod_settings, "import_excludes", context.scene.auto_lod_settings, "import_excludes_index")

        column = row.column(align = True)
        column.operator("custom.handle_exclude_list", icon="ZOOMIN", text = "").action = "ADD"
        column.operator("custom.handle_exclude_list", icon="ZOOMOUT", text = "").action = "REMOVE"

        self.layout.prop(context.scene.auto_lod_settings, "output_mesh_folder")
        self.layout.operator("object.generatelodsfolder", text = "Generate LODs")

class GenerateLodsFolder(Operator):
    bl_idname = "object.generatelodsfolder"
    bl_label = "Generate LODs Folder"
    bl_options = {"UNDO"}

    def execute(self, context):
        settings = context.scene.auto_lod_settings
        input_path = settings.input_mesh_folder
        input_files = [os.path.join(input_path, file_name) for file_name in os.listdir(input_path)]
        input_files = filter(os.path.isfile, input_files)
        input_files = [path for path in input_files if path.endswith(".fbx")]
        for path in input_files:
            if path in [path.value for path in settings.import_excludes.values()]:
                continue
            bpy.ops.import_scene.fbx(filepath = path)
        return {"FINISHED"}

def generate_lods(object):
    for i in range(context.scene.auto_lod_settings.lod_count):
        object_copy = object.copy()
        object_copy.name = object.name + "_LOD" + str(i + 1)
        context.scene.objects.link(object_copy)
        modifier = object_copy.modifiers.new("DecimateMod", "DECIMATE")
        modifier.ratio = 0.5

    object.name += "_LOD0"

def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.auto_lod_settings = PointerProperty(type = Settings)

def unregister():
    bpy.utils.unregister_module(__name__)
    del bpy.types.Scene.auto_lod_settings
