import math
import subprocess
import os
import inspect

def open_edm(screen, macros='', path=None, sh_script='edm_open.sh'):
    if not path:
        path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    edm_open = '{:}/{:} {:} {:}'.format(path, sh_script, screen, macros)
    subprocess.call(edm_open, shell=True)

class EDM_Screen_Maker(object):

    _motor_type_order = ['MMS','MMN','MZM','PIC']
    _screen_sizes = {'MMS':{'w':375,'h':100,'columns':2},
            'PIC':{'w':195,'h':215,'columns':4},
            'MZM':{'w':255,'h':102,'columns':3},
            'MMN':{'w':375,'h':100,'columns':2}}

    def __init__(self,file,motor_list,group_name=None,path='/tmp/'):
        self.path = path
        self.screen_file = '{:}/{:}'.format(path,file)
        self._screen_name = file
        self._motors = list(sorted(motor_list))
        #Create group dictionary
        self._groups = {}
        if not group_name:
            group_name = 'Motors'
        self._groups[group_name] = motor_list
    
    def change_type_order(self):
        print 'Enter order for motor type to display in each group'
        print 'Current order is  ---> {:}'.format(self._motor_type_order)
        print '(Start at 1 -> Top to Bottom'
        print '-'*80
        new_order = [0]*len(self._motor_type_order)
        for type in self._motor_type_order:

            #Ask for correct motor ordering
            #Ask for correct motor ordering
            while True:
                order_no = input('Order for {:}: '.format(type))
                #If slot is empty
                if order_no in range(1,len(new_order)+1) and not new_order[int(order_no-1)]:
                    new_order[order_no-1] = type
                    break
                #If bad input, ask again:
                else:
                    print 'Slot is either already filled or non-existant'
                    continue
                 
        #Add ordered motor of same type to list
        self._motor_type_order = new_order


    def show_preview(self):
        cd = os.getcwd()
        os.chdir(self.path)
        edmbin = '/reg/g/pcds/package/epics/3.14/extensions/current/bin/linux-x86_64/edm'
        subprocess.call('{:} -x -eolc {:}'.format(edmbin, self._screen_name),shell=True)
        os.chdir(cd)


    def sort_order_in_group(self,group):
        master_motor_order = []
        
        for motor_type in self._motor_type_order:
            type_motor_list = []
            for motor in self._groups[group]:
                if motor_type in motor:
                    type_motor_list.append(motor)
           
            print type_motor_list
            #Skip if motor type not present or only one representation
            if len(motor_type) < 2:
                continue
            else:
                 print 'Enter order for motors in group with type -> {:}'.format(motor_type)
                 print 'Total number ---> {:}'.format(len(type_motor_list))
                 print '(Start at 1 -> Left to Right,Top to Bottom)'
                 print '-'*80

                 new_motor_order=[0]*len(type_motor_list)
                 for motor in type_motor_list:
                     #Ask for correct motor ordering
                     while True:
                         order_no = input('Group Order for {:}: '.format(motor))
                         #If slot is empty
                         if order_no in range(1,len(new_motor_order)+1) and not new_motor_order[int(order_no)-1]:
                             new_motor_order[order_no-1] = motor
                             break
                         #If bad input, ask again:
                         else:
                             print 'Slot is either already filled or non-existant'
                             continue
                 #Add ordered motor of same type to list
                 master_motor_order.extend(new_motor_order)
        
        #Place new order in dictionary
        self._groups[group] = master_motor_order
    
    def group_motors(self):

        group_list = list(sorted(self._groups.keys()))
        print 'To add a motor to a specific group use the corresponding number code'
        for i,group in enumerate(group_list):
            print '{:} --> {:}'.format(group,i)
        print '-'*80
        for motor in self._motors:
            while True:
                group_no = input('Group for {:}: '.format(motor))
                try:
                    self.add_motor_to_group(motor,group_list[group_no])
                    break
                except:
                    print 'Not a valid group number'
 
    def add_motor_to_group(self,motor,group):
        self._remove_motor_from_groups(motor)
        self._groups[group].append(motor)

    def _remove_motor_from_groups(self,motor):

        for group,motors in self._groups.items():
            if motor in motors: motors.remove(motor)
    
    def swap_motors_positions(self,motor_A,motor_B):
        for group,motors in self._groups.items():
            if motor_A in motors and motor_B in motors:
                a,b = motors.index(motor_A),motors.index(motor_B)
                motors[a],motors[b]=motors[b],motors[a]

    def delete_group(self,group_name):

        if group_name in self._groups.keys():
            del self._groups[group_name]

        else:
            return '{:} not found in created groups'.format(group_name)

    def add_group(self,group_name):
        if group_name in self._groups.keys():
            print 'Group already exists'
        else:
            self._groups[group_name] = []

    def _create_blank_screen(self,w=820,h=1000):
        file = open(self.screen_file,'w')
        file.write("""
4 0 1
beginScreenProperties
major 4
minor 0
release 1
x 2888
y 2208
w {:}
h {:}
font "helvetica-medium-r-18.0"
ctlFont "helvetica-medium-r-18.0"
btnFont "helvetica-medium-r-18.0"
fgColor index 14
bgColor index 7
textColor index 14
ctlFgColor1 index 14
ctlFgColor2 index 0
ctlBgColor1 index 0
ctlBgColor2 index 14
topShadowColor index 0
botShadowColor index 14
showGrid
gridSize 8
endScreenProperties

                """.format(w,h))
        file.close()
    def _draw_rectangle(self,x=11,y=0,w=798,h=800):

        file = open(self.screen_file,'a')
        file.write("""
# (Rectangle)
object activeRectangleClass
beginObjectProperties
major 4
minor 0
release 0
x {:}
y {:}
w {:}
h {:}
lineColor index 14
fill
fillColor index 10
endObjectProperties
   
                   """.format(x,y,w,h))
        file.close()
        

    def _make_title(self,title,x=222,y=0,w=375,h=20):
        file  = open(self.screen_file,'a')
        file.write("""
# (Static Text)
object activeXTextClass
beginObjectProperties
major 4
minor 1
release 1
x {:}
y {:}
w {:}
h {:}
font "helvetica-medium-r-18.0"
fontAlign "center"
fgColor index 14
bgColor index 0
useDisplayBg
value {{
  "{:}"
}}
endObjectProperties

                   """.format(x,y,w,h,title))
        file.close()
    def _make_embedded_motor(self,motor,motor_type,x=0,y=0):
        w = self._screen_sizes[motor_type]['w']
        h = self._screen_sizes[motor_type]['h']
        file = open(self.screen_file,'a')

        file.write("""
# (Embedded Window)
object activePipClass
beginObjectProperties
major 4
minor 1
release 0
x {:}
y {:}
w {:}
h {:}
fgColor index 14
bgColor index 0
topShadowColor index 0ll
botShadowColor index 14
displaySource "menu"
filePv "LOC\\\\emb-SC3-mmss=0"
numDsps 1
displayFileName {{
  0 "pcds_motionScreens/emb-{:}-small.edl"
}}
menuLabel {{
  0 "{:}"
}}
symbols {{
  0 "MOTOR={:}"
}}
noScroll
endObjectProperties
                   
                   """.format(x,y,w,h,motor_type.lower(),motor,motor))


    def _draw_motor_group(self,motor_list,motor_type,drawing_height=0,screen_width=820,border=11,vert_motor_spacing=8):
        motor_width = self._screen_sizes[motor_type]['w']
        motor_height = self._screen_sizes[motor_type]['h']
        columns = self._screen_sizes[motor_type]['columns']

        #Determine Total Space Needed
        num_motors = len(motor_list)
        rows = math.ceil(num_motors/float(columns))
        vertical_space = (motor_height*rows)+((rows-1)*vert_motor_spacing)

        #Determine Complete Rows 
        complete_rows = num_motors/columns
        stragglers = num_motors%columns
        
        #Determine Spacing
        working_horiz_space = screen_width-(2*border)
        row_space = columns*motor_width
        horiz_spacing = (working_horiz_space-row_space)/(columns+1)
        
        #Determine Starting Drawing Height
        y_drawing=drawing_height
        
        #Draw complete_rows
        for row in range(complete_rows):
            x_drawing=border+horiz_spacing
            for column in range(columns):
                motor_num = (row*columns)+column
                self._make_embedded_motor(motor_list[motor_num],motor_type,x=x_drawing,y=y_drawing)
                x_drawing+=(motor_width+horiz_spacing)
            y_drawing+=motor_height+vert_motor_spacing

        if not stragglers:
            return vertical_space

        #Draw incomplete rows
        row_space = (stragglers*motor_width)+((stragglers-1)*horiz_spacing)
        center_addon = (working_horiz_space-row_space)/2.0
        x_drawing=border+center_addon
        
        straggler_motors = motor_list[-stragglers:]
        for motor in straggler_motors:
            self._make_embedded_motor(motor,motor_type,x=x_drawing,y=y_drawing)         
            x_drawing+=motor_width+horiz_spacing

        return vertical_space




    def _draw_group(self,group_name,top_height,screen_width=820,motor_type_vert=8,motor_type_horiz=16,border=11,title_width=375,title_height=20,vert_motor_spacing=8):
    
        vert_group_space = title_height+(2*motor_type_vert)

        group_title = group_name
        group_motors = self._groups[group_name] 
        

        y_drawing = vert_group_space+top_height

        for motor_type in self._motor_type_order:
            motors = []
            for motor in group_motors:
                if motor_type in motor:
                    motors.append(motor)

            if motors:
                space = self._draw_motor_group(motors,motor_type,drawing_height=y_drawing,screen_width=screen_width,border=border,vert_motor_spacing=vert_motor_spacing)
                y_drawing+=space+motor_type_vert
                vert_group_space += space+motor_type_vert

        self._draw_rectangle(x=border,y=top_height,w=(screen_width-(2*border)),h=vert_group_space)
        
        #Draw Title
        center = (screen_width-title_width)/2.0
        self._make_title(group_name,x=center,y=top_height+motor_type_vert,w=title_width,h=title_height)

        return vert_group_space

    def create_screen(self,group_spacing=8,screen_width=820,screen_height=1000,vert_motor_spacing=8,motor_type_vert=8,motor_type_horiz=16,border=11,
                    title_width=375,title_height=20):
        '''
        Keywords Arguments:
        ----------------------
        (Should all be given as integer values)

        group_spacing : Distance between groups (default=8)
    
        vert_space : Vertical distance between items inside the group (default=8)

        horiz_space: Horizontal distance between items inside the group(default=16)

        border: The distance between the edges of the screen and the 
                edges of the background rectangle (default=11)

        title_width = The width given for the title of each group (default=20)

        title_height = The height left for the title of each group (default=20)
        '''
        #Create blank screen
        self._create_blank_screen(w=screen_width,h=screen_height)

        #Draw Groups
        group_drawing_height = group_spacing
        for group,motors in self._groups.items():
            
            #If Group is empty skip
            if not motors:
                continue

            #Draw Group
            y_offset = self._draw_group(group,group_drawing_height,screen_width=screen_width, motor_type_vert=motor_type_vert,
                                       motor_type_horiz=motor_type_horiz,border=border,title_width=title_width,title_height=title_height,
                                       vert_motor_spacing=vert_motor_spacing)

            group_drawing_height += y_offset+group_spacing         





