import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node
import serial
import time

from wrist_interfaces_wired.action import WristMove

class WristActionServer(Node):

    def __init__(self):
        super().__init__('wrist_action_server')
        
        # Pico's serial port, e.g., /dev/ttyACM0
        self.declare_parameter('serial_port', '/dev/ttyACM0')
        self.declare_parameter('baud_rate', 115200)
        
        serial_port = self.get_parameter('serial_port').get_parameter_value().string_value
        baud_rate = self.get_parameter('baud_rate').get_parameter_value().integer_value
        
        try:
            self.serial_conn = serial.Serial(serial_port, baud_rate, timeout=0.1)
            self.get_logger().info(f'Connected to serial port {serial_port} at {baud_rate} baud.')
        except Exception as e:
            self.get_logger().error(f'Failed to connect to serial port {serial_port}: {e}')
            self.serial_conn = None

        self._action_server = ActionServer(
            self,
            WristMove,
            'wrist_move',
            self.execute_callback)
            
        self.get_logger().info('Wrist Action Server has been started.')

    def execute_callback(self, goal_handle):
        self.get_logger().info(f'Executing goal: {goal_handle.request.command}')
        
        if self.serial_conn is None:
            self.get_logger().error("Serial connection not available.")
            goal_handle.abort()
            result = WristMove.Result()
            result.success = False
            return result
        
        cmd = goal_handle.request.command
        val = goal_handle.request.angle_val
        
        if cmd == 'HOMING':
            send_str = "HOMING\n"
        elif cmd == 'ABS':
            send_str = f"ABS:{int(val)}\n"
        elif cmd == 'REL':
            send_str = f"REL:{int(val)}\n"
        else:
            self.get_logger().error(f"Unknown command: {cmd}")
            goal_handle.abort()
            result = WristMove.Result()
            result.success = False
            return result

        try:
            # Clear input buffer before sending new command
            self.serial_conn.reset_input_buffer()
            self.serial_conn.write(send_str.encode('utf-8'))
            
            # Loop to receive feedback and done message
            buffer = ""
            start_time = time.time()
            
            while True:
                # Read whatever is available or wait for timeout
                data = self.serial_conn.read(self.serial_conn.in_waiting or 1)
                if not data:
                    # No data received within timeout
                    # Add a timeout for the entire operation if needed, e.g., 60 seconds
                    if time.time() - start_time > 60.0:
                        self.get_logger().error("Command timed out.")
                        goal_handle.abort()
                        result = WristMove.Result()
                        result.success = False
                        return result
                    continue
                
                # Reset timeout since we received data
                start_time = time.time()
                
                buffer += data.decode('utf-8')
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    
                    if line.startswith('FEEDBACK:'):
                        try:
                            current_angle = float(line.split(':')[1])
                            feedback_msg = WristMove.Feedback()
                            feedback_msg.current_angle = current_angle
                            goal_handle.publish_feedback(feedback_msg)
                        except Exception as e:
                            self.get_logger().warn(f"Failed to parse feedback: {e}")
                            
                    elif line.startswith('DONE:'):
                        try:
                            final_angle = float(line.split(':')[1])
                            goal_handle.succeed()
                            result = WristMove.Result()
                            result.success = True
                            result.final_angle = final_angle
                            return result
                        except Exception as e:
                            self.get_logger().error(f"Failed to parse DONE: {e}")
                            goal_handle.abort()
                            result = WristMove.Result()
                            result.success = False
                            return result
                            
                    elif line.startswith('ERROR:'):
                        self.get_logger().error(f"Pico reported error: {line}")
                        goal_handle.abort()
                        result = WristMove.Result()
                        result.success = False
                        return result

        except Exception as e:
            self.get_logger().error(f"Serial error: {e}")
            goal_handle.abort()
            result = WristMove.Result()
            result.success = False
            return result
            
        # Fallback
        goal_handle.abort()
        result = WristMove.Result()
        result.success = False
        return result

    def destroy_node(self):
        if self.serial_conn is not None:
            self.serial_conn.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    wrist_action_server = WristActionServer()
    try:
        rclpy.spin(wrist_action_server)
    except KeyboardInterrupt:
        pass
    finally:
        wrist_action_server.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
