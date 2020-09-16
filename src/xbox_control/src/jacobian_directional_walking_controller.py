#!/usr/bin/env python2

import rospy
from sensor_msgs.msg import JointState
from std_msgs.msg import Header
from std_msgs.msg import Float64
from sensor_msgs.msg import Joy
import math
import numpy as np

a_global = 0
b_global = 0
#l_1 is the shoulder
l_1_global = .35
#l_2 is the elbow
l_2 = .5
#l_3 is the knee
l_3 = .5
q_1_nom =  0
q_2_nom =  math.pi/4
q_3_nom = -math.pi/2
#In order to run this script, joy_node needs to be running as well as new_rviz.launch
class quad_leg:

    def __init__(self, a_offset, b_offset, q_1, q_2, q_3, l_1):
        #constructor to define certain leg variables
        self.a_offset = a_offset
        self.b_offset = b_offset
        self.q_1 = q_1
        self.q_2 = q_2
        self.q_3 = q_3
        self.l_1 = l_1


    def set_joint_angle(self, theta_1, theta_2, theta_3):
        #set shoulder, elbow, knee angles in radians
        self.q_1 = theta_1
        self.q_2 = theta_2
        self.q_3 = theta_3
        print(self.q_1)
        print(self.q_2)
        print(self.q_3)

    def set_nom_position(self):
        #set angles to q_1_nom, q_2_nom, q_3_nom
        #need to be revisited didnt work fully during the directional walking
        self.q_1 = q_1_nom
        self.q_2 = q_2_nom
        self.q_2 = q_2_nom

    def ee_position(self):
        #algorithm to determine the current x, y, z position of the foot

        global l_2
        global l_3

        #origin_base_rot = np.matrix([[0, 0, 1, 0], [-1, 0, 0, 0], [0, -1, 0, 0], [0, 0, 0, 1]])
        # base_link to joint_0 transforms
        base_zero_trans = np.matrix([[1, 0, 0, self.a_offset],[0, 1, 0, self.b_offset],[0, 0, 1, 0], [0, 0, 0, 1]])
        #joint_0 to joint_1 transforms
        #l_1 translation will be -l_1 if it is the right side of the vehicle and l_1 if on the left
        zero_one_rot_z = np.matrix([[math.cos(self.q_1), -1*math.sin(self.q_1), 0, 0], [math.sin(self.q_1), math.cos(self.q_1), 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
        zero_one_trans = np.matrix([[1, 0, 0, self.l_1], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
        zero_one_rot_x = np.matrix([[0, 0, 1, 0], [0, 1, 0, 0], [-1, 0, 0, 0], [0, 0, 0, 1]])
        #joint_1 to joint_2 transforms
        one_two_rot_z = np.matrix([[math.cos(self.q_2), -1*math.sin(self.q_2), 0, 0], [math.sin(self.q_2), math.cos(self.q_2), 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
        one_two_trans = np.matrix([[1, 0, 0, 0], [0, 1, 0, l_2], [0, 0, 1, 0], [0, 0, 0, 1]])
        #joint_2 to end effector transforms
        two_ee_rot_z = np.matrix([[math.cos(self.q_3), -1*math.sin(self.q_3), 0, 0], [math.sin(self.q_3), math.cos(self.q_3), 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
        two_ee_trans = np.matrix([[1, 0, 0, 0], [0, 1, 0, l_3], [0, 0, 1, 0], [0, 0, 0, 1]])
        base_zero = base_zero_trans
        zero_one = zero_one_rot_z * zero_one_trans * zero_one_rot_x
        one_two = one_two_rot_z * one_two_trans
        two_ee = two_ee_rot_z * two_ee_trans
        #origin_ee =  base_zero * zero_one * one_two * two_ee
        base_ee = base_zero * zero_one * one_two * two_ee
        #print(origin_ee)
        position_matrix = np.array([[base_ee.item(0, 3)], [base_ee.item(1, 3)], [base_ee.item(2, 3)]])
        return position_matrix


    def get_delta_q(self, z, x, y):
        
        delta_x = np.matrix([[-x],[-y],[z]])
        dx_dq_1 = l_3*math.cos(self.q_1)*math.sin(self.q_2)*math.sin(self.q_3) - l_2*math.cos(self.q_1)*math.cos(self.q_2) - self.l_1*math.sin(self.q_1)
        dx_dq_2 = l_3*(math.cos(self.q_2)*math.sin(self.q_1)*math.sin(self.q_3) + math.cos(self.q_3)*math.sin(self.q_1)*math.sin(self.q_2)) + l_2*math.sin(self.q_1)*math.sin(self.q_2)
        dx_dq_3 = l_3*(math.cos(self.q_2)*math.sin(self.q_1)*math.sin(self.q_3) + math.cos(self.q_3)*math.sin(self.q_1)*math.sin(self.q_2))
        dy_dq_1 = l_3*(math.sin(self.q_1)*math.sin(self.q_2)*math.sin(self.q_3) - math.cos(self.q_2)*math.cos(self.q_3)*math.sin(self.q_1)) + self.l_1*math.cos(self.q_1) - l_2*math.cos(self.q_2)*math.sin(self.q_1)
        dy_dq_2 = -1*l_3*(math.cos(self.q_1)*math.cos(self.q_2)*math.sin(self.q_3) + math.cos(self.q_1)*math.cos(self.q_3)*math.sin(self.q_2)) - l_2*math.cos(self.q_1)*math.sin(self.q_2)
        dy_dq_3 = -1*l_3*(math.cos(self.q_1)*math.cos(self.q_2)*math.sin(self.q_3) + math.cos(self.q_1)*math.cos(self.q_3)*math.sin(self.q_2))
        dz_dq_1 = 0
        dz_dq_2 = l_3*(math.cos(self.q_2)*math.cos(self.q_3) - math.sin(self.q_2)*math.sin(self.q_3)) + l_2*math.cos(self.q_2)
        dz_dq_3 = l_3*(math.cos(self.q_2)*math.cos(self.q_3) - math.sin(self.q_2)*math.sin(self.q_3))


        jacobian = np.matrix([[dx_dq_1, dx_dq_2, dx_dq_3], [dy_dq_1, dy_dq_2, dy_dq_3], [dz_dq_1, dz_dq_2, dz_dq_3]])
        #print(jacobian)
        jacobian_det = ((dx_dq_1)*((dy_dq_2 * dz_dq_3)-(dy_dq_3*dz_dq_2))) - ((dx_dq_2)*((dy_dq_1*dz_dq_3)-(dy_dq_3*dz_dq_1))) + ((dx_dq_3)*((dy_dq_1*dz_dq_2)-(dy_dq_2*dz_dq_1)))
        #print(jacobian_det)
        jacobian_inv = np.linalg.inv(jacobian)
        delta_q = jacobian_inv * delta_x

        q_1_delta = delta_q[0][0]
        q_2_delta = delta_q[1][0]
        q_3_delta = delta_q[2][0]
        self.q_1 = self.q_1 + q_1_delta
        self.q_2 = self.q_2 + q_2_delta
        self.q_3 = self.q_3 + q_3_delta


rf = quad_leg(-a_global, -b_global, q_1_nom, q_2_nom, q_3_nom, l_1_global)
lf = quad_leg(a_global, -b_global, q_1_nom, q_2_nom, q_3_nom, -l_1_global)
rb = quad_leg(-a_global, -b_global, q_1_nom, q_2_nom, q_3_nom, l_1_global)
lb = quad_leg(a_global, -b_global, q_1_nom, q_2_nom, q_3_nom, -l_1_global)

hello_str = JointState()
hello_str.header = Header()
hello_str.name = ['shoulder_joint_lf', 'elbow_joint_lf', 'wrist_joint_lf', 'ankle_joint_lf', 'shoe_joint_lf',
  'shoulder_joint_rf', 'elbow_joint_rf', 'wrist_joint_rf', 'ankle_joint_rf', 'shoe_joint_rf',
  'shoulder_joint_lb', 'elbow_joint_lb', 'wrist_joint_lb', 'fffankle_joint_lb', 'shoe_joint_lb',
  'shoulder_joint_rb', 'elbow_joint_rb', 'wrist_joint_rb', 'ankle_joint_rb', 'shoe_joint_rb']
hello_str.velocity = []
hello_str.effort = []


def callback(data):
    
    rospy.sleep(.05)
    step_trigger = data.axes[5]
    step_button = data.buttons[0]
    #left joystick horizontal is [0] and vertical is [1]
    step_joystick_hor = data.axes[0]
    step_joystick_vert = data.axes[1]
    #have to make the horizontal joystick negative to match a standard cartesian graph
    step_joystick_hor = step_joystick_hor * 1
    joystick_magnitude = math.sqrt((step_joystick_hor**2) + (step_joystick_vert**2))
    
    if (step_trigger == -1) and (joystick_magnitude != 0):

        delta_x_ratio = step_joystick_vert / joystick_magnitude
        delta_y_ratio = step_joystick_hor / joystick_magnitude
        print(delta_y_ratio)
        recal_step = joystick_magnitude/4
        
        #vertex_y is the height of the step we always want to see
        vertex_z = 1
        #vertex_x is the x position of the apex of the step, which is exactly half of the b_parabola
        vertex_x =  recal_step/2
        #b_parabola also represents how far you want to step forward
        b_parabola = recal_step
        a_parabola = (vertex_z)/((vertex_x**2)+vertex_x)
        land_parabola = [0, recal_step/4, recal_step/2, 3*recal_step/4, recal_step]
        z_parabola = [-a_parabola * (elem**2) + (b_parabola * a_parabola * elem) for elem in land_parabola]
        delta_land_parabola = [land_parabola[1] - land_parabola[0], land_parabola[2] - land_parabola[1], land_parabola[3] - land_parabola[2], land_parabola[4] - land_parabola[3]]
        delta_parabola_z = [z_parabola[1] - z_parabola[0], z_parabola[2] - z_parabola[1], z_parabola[3] - z_parabola[2], z_parabola[4] - z_parabola[3]]
        delta_land_parabola_x = [elem * delta_x_ratio for elem in delta_land_parabola]
        delta_land_parabola_y = [elem * delta_y_ratio for elem in delta_land_parabola]

        feet = [0, 1, 2, 3, 4]
        
        for f in feet:
            if f == 0:
                for i in range(4):
                    rf.get_delta_q(-delta_land_parabola_x[i], -delta_land_parabola_y[i], delta_parabola_z[i])
                    rospy.sleep(.1)
                    hello_str.position = [lf.q_1, lf.q_2, lf.q_3, 0, 0, rf.q_1, rf.q_2, rf.q_3, 0, 0, lb.q_1, lb.q_2, lb.q_3, 0, 0, rb.q_1, rb.q_2, rb.q_3, 0, 0]
                    print "delta_land_parabola_x", delta_land_parabola_x
                    print "delta_parabola_z", delta_parabola_z

            elif f == 1:            
                for i in range(4):
                    rb.get_delta_q(-delta_land_parabola_x[i], -delta_land_parabola_y[i], delta_parabola_z[i])
                    rospy.sleep(.1)
                    hello_str.position = [lf.q_1, lf.q_2, lf.q_3, 0, 0, rf.q_1, rf.q_2, rf.q_3, 0, 0, lb.q_1, lb.q_2, lb.q_3, 0, 0, rb.q_1, rb.q_2, rb.q_3, 0, 0]
        
            elif f == 2:        
                for i in range(4):    
                    lb.get_delta_q(-delta_land_parabola_x[i], -delta_land_parabola_y[i], delta_parabola_z[i])
                    rospy.sleep(.1)
                    hello_str.position = [lf.q_1, lf.q_2, lf.q_3, 0, 0, rf.q_1, rf.q_2, rf.q_3, 0, 0, lb.q_1, lb.q_2, lb.q_3, 0, 0, rb.q_1, rb.q_2, rb.q_3, 0, 0]
        
            elif f == 3:        
                for i in range(4):
                    lf.get_delta_q(-delta_land_parabola_x[i], -delta_land_parabola_y[i], delta_parabola_z[i])
                    rospy.sleep(.1)
                    hello_str.position = [lf.q_1, lf.q_2, lf.q_3, 0, 0, rf.q_1, rf.q_2, rf.q_3, 0, 0, lb.q_1, lb.q_2, lb.q_3, 0, 0, rb.q_1, rb.q_2, rb.q_3, 0, 0]
                    
            elif f == 4:
                rospy.sleep(1)
                rf.set_joint_angle(q_1_nom, q_2_nom, q_3_nom)
                rb.set_joint_angle(q_1_nom, q_2_nom, q_3_nom)
                lf.set_joint_angle(q_1_nom, q_2_nom, q_3_nom)
                lb.set_joint_angle(q_1_nom, q_2_nom, q_3_nom)
                hello_str.position = [lf.q_1, lf.q_2, lf.q_3, 0, 0, rf.q_1, rf.q_2, rf.q_3, 0, 0, lb.q_1, lb.q_2, lb.q_3, 0, 0, rb.q_1, rb.q_2, rb.q_3, 0, 0]
                rospy.sleep(.5)
                print("hello")

    time_now = rospy.Time.now()



def talker():
    
    pub = rospy.Publisher('joint_states', JointState, queue_size=10)
    rospy.init_node('joint_state_publisher')
    rate = rospy.Rate(10) # 10hz
    rospy.Subscriber("joy", Joy, callback)
    hello_str.header.stamp = rospy.Time.now()
    pub.publish(hello_str)
    rate.sleep()

    while not rospy.is_shutdown():

      hello_str.header.stamp = rospy.Time.now()
      pub.publish(hello_str)
      rate.sleep()

if __name__ == '__main__':
    try:
        talker()
    except rospy.ROSInterruptException:
        pass
