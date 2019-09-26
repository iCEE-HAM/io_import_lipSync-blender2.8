# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# TODO:
# * Relative path to lipsync file
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "LipSync Importer & Blinker",
    "author": "Yousef Harfoush - bat3a ;) / Konstantin Dmitriev / fixed for 2.76x by Looch / 2.8 fix by iCEE HAM", 
    "version": (0, 5, 3),
    "blender": (2, 80, 0),
    "location": "3D window > Tool Shelf",
    "description": "Plot Moho (Papagayo, Jlipsync, Yolo) file to frames and adds automatic blinking. Modified by Konstantin Dmitriev for Morevna Project to support Pose Libraries and CG Cookie Flex Rig",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php?title=Extensions:2.6/Py/"
    "Scripts/Import-Export/Lipsync Importer",
    "tracker_url": "https://developer.blender.org/T24080",
    "category": "Import-Export"}


import bpy, re
from random import random
from bpy.props import *
from bpy.props import IntProperty, FloatProperty, StringProperty

global lastPhoneme
lastPhoneme="nothing"

# add blinking
def blinker():

    scn = bpy.context.scene
    obj = bpy.context.object

    if scn.regMENU_PG_types.enumBlinkTypes == '0':
        modifier = 0
    elif scn.regMENU_PG_types.enumBlinkTypes == '1':
        modifier = scn.blinkMod

    #creating keys with blinkNm count
    for y in range(scn.blinkNm):
        frame = y * scn.blinkSp + int(random()*modifier)
        createShapekey('blink', frame)
        
# ----------- cg cookie flexrig support-------------------

lastPhonemeIdx = -100

def blinkerFlexRig():
    
    scn = bpy.context.scene
    obj = bpy.context.object
    
    # saving current scene state
    state_record = scn.tool_settings.use_keyframe_insert_auto
    state_frame = scn.frame_current
    state_poselib = obj.pose_library

    if scn.regMENU_PG_types.enumBlinkTypes == '0':
        modifier = 0
    elif scn.regMENU_PG_types.enumBlinkTypes == '1':
        modifier = scn.blinkMod
    
    
    # activate pose library
    obj.pose_library = bpy.data.actions[scn.eyesLib]
    scn.tool_settings.use_keyframe_insert_auto = True
    
    # find which bones should be affected by pose library
    bones_list=[]
    for bone in bpy.data.actions[scn.eyesLib].groups.keys():
        if len(bpy.data.actions[scn.eyesLib].groups[bone].channels)!=0:
            bones_list.append(bone)
    
    # select bones
    if len(bpy.context.selected_pose_bones) != 0:
        bpy.ops.pose.select_all()
    for bone_name in obj.data.bones.keys():
        if bone_name in bones_list:
            obj.data.bones[bone_name].select=True
        else:
            obj.data.bones[bone_name].select=False
    
    offst = scn.offset     # offset value
    frmIn = scn.easeIn     # ease in value
    frmOut = scn.easeOut   # ease out value
    hldIn = scn.holdGap    # holding time value
    
    
    
    #creating keys with blinkNm count
    for y in range(scn.blinkNm):
        frame = y * scn.blinkSp + int(random()*modifier)
        #createShapekey('blink', frame)
        
        # inserting the In key only when phonem change or when blinking
        #if lastPhoneme!=phoneme or eval(scn.regMENU_PG_types.enumModeTypes) == 1:
        #    addFlexRigKey(offst+frame-frmIn, phoneme)
        
        addFlexRigKey(offst+frame-frmIn, 'rest')
        addFlexRigKey(offst+frame, 'blink')
        addFlexRigKey(offst+frame+hldIn, 'blink')
        addFlexRigKey(offst+frame+hldIn+frmOut, 'rest')

    
    # restoring current scene state
    scn.tool_settings.use_keyframe_insert_auto = state_record
    scn.frame_current = state_frame
    obj.pose_library = state_poselib
        
def lipsyncerFlexRig():
    # reading imported file & creating keys
    obj = bpy.context.object
    scene = bpy.context.scene
    bone = bpy.context.active_pose_bone
    
    # saving current scene state
    state_record = scene.tool_settings.use_keyframe_insert_auto
    state_frame = scene.frame_current
    state_poselib = obj.pose_library
    
    
    offst = scene.offset     # offset value
    skVlu = scene.skscale    # shape key value
    
    #in case of Papagayo format
    if scene.regMENU_PG_types.enumFileTypes == '0' :
        frmIn = scene.easeIn     # ease in value
        frmOut = scene.easeOut   # ease out value
        hldIn = scene.holdGap    # holding time value
        
    #in case of Jlipsync format or Yolo
    elif scene.regMENU_PG_types.enumFileTypes == '1' :
        frmIn = 1
        frmOut = 1
        hldIn = 0
        
    # activate pose library
    obj.pose_library = bpy.data.actions[scene.phonemesLib]
    scene.tool_settings.use_keyframe_insert_auto = True
        
    # find which bones should be affected by pose library
    bones_list=[]
    for bone in bpy.data.actions[scene.phonemesLib].groups.keys():
        if len(bpy.data.actions[scene.phonemesLib].groups[bone].channels)!=0:
            bones_list.append(bone)
    
    # select bones
    if len(bpy.context.selected_pose_bones) != 0:
        bpy.ops.pose.select_all()
    for bone_name in obj.data.bones.keys():
        if bone_name in bones_list:
            obj.data.bones[bone_name].select=True
        else:
            obj.data.bones[bone_name].select=False
    
    
    f=open(bpy.path.abspath(scene.fpath)) # importing file
    f.readline() # reading the 1st line that we don"t need
    
    global lastPhonemeIdx
    global lastPhoneme
    lastPhoneme = []
    #lastPhoneme.append("rest")
    global prevFrame
    prevFrame = -100
    
    for line in f:
        # removing new lines
        lsta = re.split("\n+", line)

        # building a list of frames & shapes indexes
        lst = re.split(":? ", lsta[0])# making a list of a frame & number 
        frame = int(lst[0])
        phoneme = lst[1]
        
        print("%s --> %s" % (frame,lst[1]))
        
        pl = obj.pose_library
        
        # inserting the In key only when phonem change or when blinking
        #if lastPhoneme[-1]!=phoneme or eval(scene.regMENU_PG_types.enumModeTypes) == 1:
        #    addFlexRigKey(offst+frame-frmIn, phoneme)
        
        # add rest position right before the first phoneme
        #if  len(lastPhoneme) == 0:
        #    addFlexRigKey(offst+frame-frmIn, "rest")
        
        if ( len(lastPhoneme)==0 or lastPhoneme[-1] == "rest" ) and frame-prevFrame > hldIn:
            if phoneme != "rest":
                addFlexRigKey(offst+frame-frmIn, "rest")
                print("adding extra keyframe for REST position")
        
        if frame-prevFrame>=frmOut or frame-prevFrame==0:
            
            if len(lastPhoneme)>=2 and frame-prevFrame==0 and lastPhoneme[-2]==phoneme:
                # avoid duplicating phonemes
                pass
            elif len(lastPhoneme)!=0 and lastPhoneme[-1] == "rest" and phoneme == "rest":
                # don't insert double rest phonemes
                pass
            else:
                addFlexRigKey(offst+frame, phoneme)
                addFlexRigKey(offst+frame+hldIn, phoneme)
                #addFlexRigKey(offst+frame+hldIn+frmOut, phoneme)
                
                lastPhoneme.append(phoneme)
                prevFrame=frame
        else:
            addFlexRigKey(offst+frame+1, phoneme)
            addFlexRigKey(offst+frame+1+hldIn, phoneme)
            lastPhoneme.append(phoneme)
            prevFrame=frame+1
                
            
    
    # restoring current scene state
    scene.tool_settings.use_keyframe_insert_auto = state_record
    scene.frame_current = state_frame
    obj.pose_library = state_poselib

                
def addFlexRigKey(frame=0, pose=""):
    
    global lastPhonemeIdx
    
    bpy.context.scene.frame_current=frame
    
    obj = bpy.context.object
    pl = obj.pose_library
    
    idx = pl.pose_markers.find(pose)
    rest_idx = pl.pose_markers.find("rest")
    
    
    
    if idx == -1:
        idx = pl.pose_markers.find("etc")
    
    if idx != -1:
        if (idx != lastPhonemeIdx) or (idx == rest_idx):
            print("Apply pose %s" % idx)
            bpy.ops.poselib.apply_pose(pose_index=idx)
            lastPhonemeIdx=idx
        
        else:
            print("skipping phoneme: pose already set")
    
    


# -----------code contributed by dalai felinto adds armature support modified by Looch-------------------

bone_keys = {
"AI":   ('location', 0),
"E":    ('location', 1),
"FV":   ('location', 2),
"L":    ('rotation_euler', 0),
"MBP":  ('rotation_euler', 1),
"O":    ('rotation_euler', 2),
"U":    ('scale', 0),
"WQ":   ('scale', 1),
"etc":  ('scale', 2),
"rest": ('ik_stretch', -1)
}

def lipsyncerBone():
    # reading imported file & creating keys
    object = bpy.context.object
    scene = bpy.context.scene
    bone = bpy.context.active_pose_bone

    resetBoneScale(bone)

    f=open(bpy.path.abspath(scene.fpath)) # importing file
    f.readline() # reading the 1st line that we don"t need

    for line in f:
        # removing new lines
        lsta = re.split("\n+", line)

        # building a list of frames & shapes indexes
        lst = re.split(":? ", lsta[0])# making a list of a frame & number
        frame = int(lst[0])

        for key,attribute in bone_keys.items():
            if lst[1] == key:
                createBoneKeys(key, bone, attribute, frame)

def resetBoneScale(bone):
    # set the attributes used by papagayo to 0.0
    for attribute,index in bone_keys.values():
        if index != -1:
            #bone.location[0] = 0.0
            exec("bone.%s[%d] = %f" % (attribute, index, 0.0))
        else:
            exec("bone.%s = %f" % (attribute, 0.0))

def addBoneKey(bone, data_path, index=-1, value=None, frame=0, group=""):
    # set a value and keyframe for the bone
    # it assumes the 'bone' variable was defined before
    # and it's the current selected bone
    frame=bpy.context.scene.frame_current
    if value != None:
        if index != -1:
            # bone.location[0] = 0.0
            exec("bone.%s[%d] = %f" % (data_path, index, value))
        else:
            exec("bone.%s = %f" % (data_path, value))

    # bone.keyframe_insert("location", 0, 10.0, "Lipsync")
    exec('bone.keyframe_insert("%s", %d, %f, "%s")' % (data_path, index, frame, group))

# creating keys with offset and eases for a phonem @ the Skframe
def createBoneKeys(phoneme, bone, attribute, frame):
    global lastPhoneme

    scene = bpy.context.scene
    object = bpy.context.object

    offst = scene.offset     # offset value
    skVlu = scene.skscale    # shape key value

    #in case of Papagayo format
    if scene.regMENU_PG_types.enumFileTypes == '0' :
        frmIn = scene.easeIn     # ease in value
        frmOut = scene.easeOut   # ease out value
        hldIn = scene.holdGap    # holding time value

    #in case of Jlipsync format or Yolo
    elif scene.regMENU_PG_types.enumFileTypes == '1' :
        frmIn = 1
        frmOut = 1
        hldIn = 0

    # inserting the In key only when phonem change or when blinking
    if lastPhoneme!=phoneme or eval(scene.regMENU_PG_types.enumModeTypes) == 1:
        addBoneKey(bone, attribute[0], attribute[1], 0.0, offst+frame-frmIn, "Lipsync")

    addBoneKey(bone, attribute[0], attribute[1], skVlu, offst+frame, "Lipsync")
    addBoneKey(bone, attribute[0], attribute[1], skVlu, offst+frame+hldIn, "Lipsync")
    addBoneKey(bone, attribute[0], attribute[1], 0.0, offst+frame+hldIn+frmOut, "Lipsync")

    lastPhoneme=phoneme

# -------------------------------------------------------------------------------

# reading imported file & creating keys
def lipsyncer():

    obj = bpy.context.object
    scn = bpy.context.scene

    f=open(bpy.path.abspath(scn.fpath)) # importing file
    f.readline() # reading the 1st line that we don"t need

    for line in f:

        # removing new lines
        lsta = re.split("\n+", line)

        # building a list of frames & shapes indexes
        lst = re.split(":? ", lsta[0])# making a list of a frame & number
        frame = int(lst[0])

        for key in obj.data.shape_keys.key_blocks:
            if lst[1] == key.name:
                createShapekey(key.name, frame)

# creating keys with offset and eases for a phonem @ the frame
def createShapekey(phoneme, frame):

    global lastPhoneme

    scn = bpy.context.scene
    obj = bpy.context.object
    objSK = obj.data.shape_keys

    offst = scn.offset     # offset value
    skVlu = scn.skscale    # shape key value

    #in case of Papagayo format
    if scn.regMENU_PG_types.enumFileTypes == '0' :
        frmIn = scn.easeIn     # ease in value
        frmOut = scn.easeOut   # ease out value
        hldIn = scn.holdGap    # holding time value

    #in case of Jlipsync format or Yolo
    elif scn.regMENU_PG_types.enumFileTypes == '1' :
        frmIn = 1
        frmOut = 1
        hldIn = 0

    # inserting the In key only when phonem change or when blinking
    if lastPhoneme!=phoneme or eval(scn.regMENU_PG_types.enumModeTypes) == 1:
        objSK.key_blocks[phoneme].value=0.0
        objSK.key_blocks[phoneme].keyframe_insert("value",
            -1, offst+frame-frmIn, "Lipsync")

    objSK.key_blocks[phoneme].value=skVlu
    objSK.key_blocks[phoneme].keyframe_insert("value",
        -1, offst+frame, "Lipsync")

    objSK.key_blocks[phoneme].value=skVlu
    objSK.key_blocks[phoneme].keyframe_insert("value",
        -1, offst+frame+hldIn, "Lipsync")

    objSK.key_blocks[phoneme].value=0.0
    objSK.key_blocks[phoneme].keyframe_insert("value",
    -1, offst+frame+hldIn+frmOut, "Lipsync")

    lastPhoneme = phoneme

# lipsyncer operation start
class BTN_OP_lipsyncer(bpy.types.Operator):
    bl_idname = 'lipsync.go'
    bl_label = 'Start Processing'
    bl_description = 'Plots the voice file keys to timeline'

    def execute(self, context):

        scn = context.scene
        obj = context.active_object

        # testing if object is valid
        if obj!=None:
            if obj.type=="MESH":
                if obj.data.shape_keys!=None:
                    if scn.fpath!='': lipsyncer()
                    else: print ("select a Moho file")
                else: print("No shape keys")

            elif obj.type=="ARMATURE":
                if scn.regMENU_PG_types.enumBoneMethodTypes == '0':
                    if scn.fpath!='': lipsyncerFlexRig()
                    else: print ("select a Moho file")
                else:
                    if 1:#XXX add prop test
                        if scn.fpath!='': lipsyncerBone()
                        else: print ("select a Moho file")
                    else: print("Create Pose properties")
                    
            else: print ("Object is not a mesh ot bone")
        else: print ("Select object")
        return {'FINISHED'}

# blinker operation start
class BTN_OP_blinker(bpy.types.Operator):
    bl_idname = 'blink.go'
    bl_label = 'Start Processing'
    bl_description = 'Add blinks at random or specifice frames'

    def execute(self, context):

        scn = context.scene
        obj = context.object

         # testing if object is valid
        if obj!=None:
            if obj.type=="MESH":
                if obj.data.shape_keys!=None:
                    for key in obj.data.shape_keys.key_blocks:
                        if key.name=='blink':
                            blinker()
                            #return
                else: print("No shape keys")
            elif obj.type=="ARMATURE":
                blinkerFlexRig()
            else: print ("Object is not a mesh ot bone")
        else: print ("Select object")
        return {'FINISHED'}


#defining custom enumeratos
class MENU_PG_types(bpy.types.PropertyGroup):

    enumFileTypes = EnumProperty(items =(('0', 'Papagayo', ''),
                                         ('1', 'Jlipsync Or Yolo', '')
                                       #,('2', 'Retarget', '')
                                         ),
                                 name = 'Choose FileType',
                                 default = '0')

    enumBlinkTypes = EnumProperty(items =(('0', 'Specific', ''),
                                          ('1', 'Random','')),
                                  name = 'Choose BlinkType',
                                  default = '0')

    enumModeTypes = EnumProperty(items =(('0', 'Lipsyncer',''),
                                         ('1', 'Blinker','')),
                                 name = 'Choose Mode',
                                 default = '0')

    enumBoneMethodTypes = EnumProperty(items =(('0', 'Pose Library',''),
                                               ('1', 'Bone Rotation','')),
                                 name = 'Method',
                                 default = '0')
                                 
# drawing the user interface
class LIPSYNC_PT_bone_ui(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Phonemes"
    bl_category = 'Animation'
    
    def draw(self, context):
        layout = self.layout
        col = layout.column()

        bone = bpy.context.active_pose_bone

        #showing the current object type
        if bone: #and if scn.regMENU_PG_types.enumModeTypes == '0':
            col.prop(bone, "location", index=0, text="AI")
            col.prop(bone, "location", index=1, text="E")
            col.prop(bone, "location", index=2, text="FV")
            if bpy.context.scene.unit_settings.system_rotation == 'RADIANS':
                col.prop(bone, "rotation_euler", index=0, text="L")
                col.prop(bone, "rotation_euler", index=1, text="MBP")
                col.prop(bone, "rotation_euler", index=2, text="O")
            else:
                row=col.row()
                row.prop(bone, "rotation_euler", index=0, text="L")
                row.label(text=str("%4.2f" % (bone.rotation_euler.x)))
                row=col.row()
                row.prop(bone, "rotation_euler", index=1, text="MBP")
                row.label(text=str("%4.2f" % (bone.rotation_euler.y)))
                row=col.row()
                row.prop(bone, "rotation_euler", index=2, text="O")
                row.label(text=str("%4.2f" % (bone.rotation_euler.z)))
            col.prop(bone, "scale", index=0, text="U")
            col.prop(bone, "scale", index=1, text="WQ")
            col.prop(bone, "scale", index=2, text="etc")
        else:
            layout.label(text="No good bone is selected")

# drawing the user interface
class LIPSYNC_PT_ui(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "LipSync Importer & Blinker"
    bl_category = 'Animation'

    newType= bpy.types.Scene

    newType.fpath = StringProperty(name="Import File ", description="Select your voice file", subtype="FILE_PATH")
    newType.skscale = FloatProperty(description="Smoothing shape key values", min=0.1, max=1.0, default=0.8)
    newType.offset = IntProperty(description="Offset your frames", default=0)

    newType.easeIn = IntProperty(description="Smoothing In curve", min=1, default=2)
    newType.easeOut = IntProperty(description="Smoothing Out curve", min=1, default=2)
    newType.holdGap = IntProperty(description="Holding for slow keys", min=0, default=0)

    newType.blinkSp = IntProperty(description="Space between blinks", min=1, default=100)
    newType.blinkNm = IntProperty(description="Number of blinks", min=1, default=10)

    newType.blinkMod = IntProperty(description="Randomzing keyframe placment", min=1, default=10)

    newType.phonemesLib = StringProperty(default="Lib_Phonemes")
    newType.eyesLib = StringProperty(default="Lib_Eyes")


    def draw(self, context):

        obj = bpy.context.active_object
        scn = bpy.context.scene

        layout = self.layout
        col = layout.column()

        # showing the current object type
        if obj != None:
            if obj.type == "MESH":
                split = col.split(align=True)
                split.label(text="The active object is: ", icon="OBJECT_DATA")
                split.label(text=obj.name, icon="EDITMODE_HLT")
            elif obj.type == "ARMATURE": # bone needs to be selected
                if obj.mode == "POSE": # mode needs to be pose
                    split = col.split(align=True)
                    split.label(text="The active object is: ", icon="ARMATURE_DATA")
                    split.label(text=obj.name, icon="EDITMODE_HLT")
                else:
                    col.label(text="You need to select Pose mode!", icon="OBJECT_DATA")
            else:
                col.label(text="The active object is not a Mesh or Armature!", icon="OBJECT_DATA")
        else:
            layout.label(text="No object is selected", icon="OBJECT_DATA")

        col.row().prop(scn.regMENU_PG_types, 'enumModeTypes')
        col.separator()

        # the lipsyncer panel
        if scn.regMENU_PG_types.enumModeTypes == '0':
            # choose the file format
            col.row().prop(scn.regMENU_PG_types, 'enumFileTypes', text = ' ', expand = True)

            # Papagayo panel
            if scn.regMENU_PG_types.enumFileTypes == '0':
                col.prop(context.scene, "fpath")
                split = col.split(align=True)
                split.label(text="Key Value :")
                split.prop(context.scene, "skscale")
                split = col.split(align=True)
                split.label(text="Frame Offset :")
                split.prop(context.scene, "offset")
                split = col.split(align=True)
                split.prop(context.scene, "easeIn", text="Ease In")
                split.prop(context.scene, "holdGap", text="Hold Gap")
                split.prop(context.scene, "easeOut", text="Ease Out")

            # Jlipsync & Yolo panel
            elif scn.regMENU_PG_types.enumFileTypes == '1':
                col.prop(context.scene, "fpath")
                split = col.split(align=True)
                split.label(text="Key Value :")
                split.prop(context.scene, "skscale")
                split = col.split(align=True)
                split.label(text="Frame Offset :")
                split.prop(context.scene, "offset")
                
            if obj.type == "ARMATURE":
                col.separator()
                col.row().prop(scn.regMENU_PG_types, 'enumBoneMethodTypes')
                if scn.regMENU_PG_types.enumBoneMethodTypes == '0':
                    col.prop(context.scene, "phonemesLib", text="Pose Library")
                col.separator()
                
            col.operator('lipsync.go', text='Plot Keys to the Timeline')
        
        # the blinker panel
        elif scn.regMENU_PG_types.enumModeTypes == '1':
            # choose blink type
            col.row().prop(scn.regMENU_PG_types, 'enumBlinkTypes', text = ' ', expand = True)

            # specific panel
            if scn.regMENU_PG_types.enumBlinkTypes == '0':
                split = col.split(align=True)
                split.label(text="Key Value :")
                split.prop(context.scene, "skscale")
                split = col.split(align=True)
                split.label(text="Frame Offset :")
                split.prop(context.scene, "offset")
                split = col.split(align=True)
                split.prop(context.scene, "easeIn", text="Ease In")
                split.prop(context.scene, "holdGap", text="Hold Gap")
                split.prop(context.scene, "easeOut", text="Ease Out")
                col.prop(context.scene, "blinkSp", text="Spacing")
                col.prop(context.scene, "blinkNm", text="Times")

            # Random panel
            elif scn.regMENU_PG_types.enumBlinkTypes == '1':
                split = col.split(align=True)
                split.label(text="Key Value :")
                split.prop(context.scene, "skscale")
                split = col.split(align=True)
                split.label(text="Frame Start :")
                split.prop(context.scene, "offset")
                split = col.split(align=True)
                split.prop(context.scene, "easeIn", text="Ease In")
                split.prop(context.scene, "holdGap", text="Hold Gap")
                split.prop(context.scene, "easeOut", text="Ease Out")
                split = col.split(align=True)
                split.prop(context.scene, "blinkSp", text="Spacing")
                split.prop(context.scene, "blinkMod", text="Random Modifier")
                col.prop(context.scene, "blinkNm", text="Times")
            
            if obj.type == "ARMATURE":
                col.separator()
                if scn.regMENU_PG_types.enumBoneMethodTypes == '0':
                    col.prop(context.scene, "eyesLib", "Pose Library")
                col.separator()
                
            col.operator('blink.go', text='Add Keys to the Timeline')
			

classes = (
    BTN_OP_lipsyncer,
    BTN_OP_blinker,
    MENU_PG_types,
    LIPSYNC_PT_bone_ui,
    LIPSYNC_PT_ui
)

# clearing vars
def clear_properties():

    # can happen on reload
    if bpy.context.scene is None:
        return
     
    props = ["fpath", "skscale", "offset", "easeIn", "easeOut", "holdGap", "blinkSp", "blinkNm", "blinkMod", "phonemesLib", "eyesLib"]
    
    for p in props:
        if p in bpy.types.Scene.bl_rna.properties:
            exec("del bpy.types.Scene."+p)
        if p in bpy.context.scene:
            del bpy.context.scene[p]

# registering the script
def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.Scene.regMENU_PG_types = PointerProperty(type=MENU_PG_types)


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.Scene.regMENU_PG_types

if __name__ == "__main__":
    register()
