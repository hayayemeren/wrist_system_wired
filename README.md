# Wrist Controller System

This repository contains the software stack for controlling a Wi-Fi enabled wrist motor (using a Raspberry Pi Pico W and a 28BYJ-48 stepper motor) natively through ROS 2 Actions.

## Repository Structure

*   **`wrist_controller/`**: MicroPython code (`main.py`) intended to run on the Raspberry Pi Pico. It hosts a TCP socket server on port `8080` to receive commands and stream feedback.
*   **`wrist_interfaces/`**: Custom ROS 2 action definition (`WristMove.action`) for the wrist motor.
*   **`wrist_ros2/`**: The ROS 2 Action Server Python node (`wrist_node`) that acts as the bridge between the ROS 2 network and the Pico over Wi-Fi.

## 1. Building the Workspace

To build the ROS 2 packages on your PC, run the following from your ROS 2 workspace root (e.g., `~/ros2_ws`):

```bash
cd ~/ros2_ws
colcon build --packages-up-to wrist_ros2
source install/setup.bash
```

## 2. Running the Action Server

Start the ROS 2 Action Server and provide it with the IP address of your Raspberry Pi Pico (which is printed to the serial console when the Pico boots up):

```bash
ros2 run wrist_ros2 wrist_node --ros-args -p pico_ip:="192.168.1.150"
```
*(Replace `192.168.1.150` with the actual IP address of your Pico).* 

## 3. Sending Test Commands (CLI)

You can use the ROS 2 command-line interface to send action goals to the server. Add the `--feedback` flag if you want to see the live angle updates as the motor turns.

**Move to an Absolute Angle (e.g., 90 degrees):**
```bash
ros2 action send_goal /wrist_move wrist_interfaces/action/WristMove "{command: 'ABS', angle_val: 90.0}" --feedback
```

**Move Relative to Current Position (e.g., turn -30 degrees):**
```bash
ros2 action send_goal /wrist_move wrist_interfaces/action/WristMove "{command: 'REL', angle_val: -30.0}" --feedback
```

**Home the Motor (Rotates 120 degrees CCW and resets origin):**
```bash
ros2 action send_goal /wrist_move wrist_interfaces/action/WristMove "{command: 'HOMING', angle_val: 0.0}" --feedback
```
