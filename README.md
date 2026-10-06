# Wrist Controller System (Wired / USB Serial)

This repository contains the software stack for controlling a USB-wired wrist motor (using a Raspberry Pi Pico W and a 28BYJ-48 stepper motor) natively through ROS 2 Actions.

## Repository Structure

*   **`wrist_controller/`**: MicroPython code (`main.py`) intended to run on the Raspberry Pi Pico. It reads from standard input over the USB serial connection to receive commands and streams feedback over standard output.
*   **`wrist_interfaces_wired/`**: Custom ROS 2 action definition (`WristMove.action`) for the wrist motor.
*   **`wrist_ros2_wired/`**: The ROS 2 Action Server Python node (`wrist_node`) that acts as the bridge between the ROS 2 network and the Pico over the USB serial connection.

## 1. Building the Workspace

To build the ROS 2 packages on your PC/Raspberry Pi, ensure you have PySerial installed:

```bash
sudo apt install python3-serial
```

Then, run the following from your ROS 2 workspace root (e.g., `~/ros2_ws`):

```bash
cd ~/ros2_ws
colcon build --packages-up-to wrist_ros2_wired
source install/setup.bash
```

## 2. Running the Action Server

Start the ROS 2 Action Server and provide it with the serial port of your Raspberry Pi Pico:

```bash
ros2 run wrist_ros2_wired wrist_node --ros-args -p serial_port:="/dev/ttyACM0"
```
*(Replace `/dev/ttyACM0` with the actual port of your Pico if it differs, e.g., `/dev/ttyUSB0`).*

Note: Ensure your user has permissions to access the serial port (e.g., `sudo usermod -a -G dialout $USER`).

## 3. Sending Test Commands (CLI)

You can use the ROS 2 command-line interface to send action goals to the server. Add the `--feedback` flag if you want to see the live angle updates as the motor turns.

**Move to an Absolute Angle (e.g., 90 degrees):**
```bash
ros2 action send_goal /wrist_move wrist_interfaces_wired/action/WristMove "{command: 'ABS', angle_val: 90.0}" --feedback
```

**Move Relative to Current Position (e.g., +45 degrees):**
```bash
ros2 action send_goal /wrist_move wrist_interfaces_wired/action/WristMove "{command: 'REL', angle_val: 45.0}"
```

**Home the Motor:**
```bash
ros2 action send_goal /wrist_move wrist_interfaces_wired/action/WristMove "{command: 'HOMING'}"
```
