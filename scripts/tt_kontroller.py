#!/usr/bin/env python3

import rospy
from geometry_msgs.msg import Twist

import sys
import termios
import tty
import select

msg = """
Control Your Robot!
------------------
Moving around:
   q    w    e
   a    s    d
   z    x    c

w/x : increase/decrease linear velocity
a/d : increase/decrease angular velocity
s : force stop
t/b : increase/decrease speed

CTRL-C to quit
"""

move_bindings = {
    'w': (1,0,0,0),
    'e': (1,0,0,-1),
    'a': (0,0,0,1),
    'd': (0,0,0,-1),
    'q': (1,0,0,1),
    'x': (-1,0,0,0),
    'c': (-1,0,0,1),
    'z': (-1,0,0,-1),
}

speed_bindings = {
    't': (1.1, 1.1),  # Increase speed
    'b': (0.9, 0.9),  # Decrease speed
}


class TTKontroller:
    def __init__(self):
        # Initialize the node
        rospy.init_node('teleop_twist_keyboard')
        
        # Publisher for cmd_vel
        self.velocity_publisher = rospy.Publisher('cmd_vel', Twist, queue_size=1)
        
        # Initial velocities
        self.linear_x = 0.0
        self.linear_y = 0.0
        self.linear_z = 0.0
        self.theta = 0.0

        # Movement settings
        self.speed = 0.5
        self.turn = 1.0
        
        # Initialize the Twist message
        self.twist = Twist()

        self.settings = termios.tcgetattr(sys.stdin)
        

    def getKey(self):
        """Get keyboard input."""
        tty.setraw(sys.stdin.fileno())
        select.select([sys.stdin], [], [], 0)
        key = sys.stdin.read(1)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        return key


    def log_vels(self, speed, turn):
        return f"logging:\tspeed {speed}\tturn {turn}"

    def run(self):
        # log the controller controls first
        print(msg)

        try:
            speed = rospy.get_param("~speed", 0.5)
            turn = rospy.get_param("~turn", 1.0)
            # stamped = rospy.get_param("~stamped", False)

            while not rospy.is_shutdown():
                key = self.getKey()

                if key in move_bindings.keys():
                    self.linear_x, self.linear_y, self.linear_z, self.theta = move_bindings[key]
                elif key in speed_bindings.keys():
                    sp, tt = speed_bindings[key]
                    speed *= sp
                    turn *= tt

                self.twist.linear.x = self.linear_x * speed
                self.twist.linear.y = self.linear_y * speed
                self.twist.linear.z = self.linear_z * speed
                self.twist.angular.x = 0
                self.twist.angular.y = 0
                self.twist.angular.z = self.theta * turn

                self.velocity_publisher.publish(self.twist)

                print(self.log_vels(speed, turn))
            
            # Publish stop message when thread exits.
            self.twist.linear.x = 0
            self.twist.linear.y = 0
            self.twist.linear.z = 0
            self.twist.angular.x = 0
            self.twist.angular.y = 0
            self.twist.angular.z = 0

            self.velocity_publisher.publish(self.twist)

        except rospy.ROSInterruptException:
            pass



if __name__ == "__main__":
    controller = TTKontroller()

    controller.run()