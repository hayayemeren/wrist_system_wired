import sys
import time
import select
from machine import Pin

# --- Motor Configuration ---
motor_pins = [
    Pin(5, Pin.OUT), 
    Pin(4, Pin.OUT), 
    Pin(3, Pin.OUT), 
    Pin(2, Pin.OUT)
]

step_sequence = [
    [1, 0, 0, 0],
    [1, 1, 0, 0],
    [0, 1, 0, 0],
    [0, 1, 1, 0],
    [0, 0, 1, 0],
    [0, 0, 1, 1],
    [0, 0, 0, 1],
    [1, 0, 0, 1]
]

STEPS_PER_REV = 4096  # 28BYJ-48 in half-step mode has 4096 steps per revolution
current_step_position = 0 # 0 represents 0 degrees initially

def turn_off_motor():
    """Forces all coils to turn off to prevent overheating."""
    for pin in motor_pins:
        pin.value(0)

def step_motor(steps, clockwise=True, delay_ms=3):
    """Moves the motor by a specific number of steps."""
    global current_step_position
    for i in range(steps):
        if clockwise:
            current_step_position = (current_step_position + 1) % STEPS_PER_REV
        else:
            current_step_position = (current_step_position - 1) % STEPS_PER_REV
            
        step_index = current_step_position % 8
        current_step = step_sequence[step_index]
        
        for pin_index in range(4):
            motor_pins[pin_index].value(current_step[pin_index])
            
        time.sleep_ms(delay_ms)
        
        # Send feedback over serial every 50 steps
        if i % 50 == 0:
            current_angle = int((current_step_position / STEPS_PER_REV) * 360)
            print(f"FEEDBACK:{current_angle}")
    
    turn_off_motor()

def set_angle(target_angle):
    """Moves the motor to a specific absolute angle (0-359 degrees) taking the shortest path."""
    global current_step_position
    # Convert angle to steps
    target_angle = target_angle % 360
    target_step = int((target_angle / 360.0) * STEPS_PER_REV)
    
    # Calculate difference
    diff = target_step - current_step_position
    
    if diff == 0:
        return
        
    clockwise = diff > 0
    steps_to_move = abs(diff)
    
    # Optimize for shortest rotation
    if steps_to_move > STEPS_PER_REV // 2:
        clockwise = not clockwise
        steps_to_move = STEPS_PER_REV - steps_to_move
        
    step_motor(steps_to_move, clockwise)

def start_serial_server():
    """Starts listening for commands on USB serial."""
    global current_step_position
    
    # Configure non-blocking read using select
    poll_obj = select.poll()
    poll_obj.register(sys.stdin, select.POLLIN)

    while True:
        try:
            # Wait for data with a timeout, allowing for graceful exit or other tasks if needed
            poll_results = poll_obj.poll(100) # 100ms timeout
            
            if poll_results:
                # Read a line from stdin
                request_str = sys.stdin.readline().strip()
                
                if not request_str:
                    continue
                
                # Handle commands
                for cmd in request_str.split('\n'):
                    cmd = cmd.strip()
                    if not cmd:
                        continue
                        
                    if cmd == 'HOMING':
                        # Homing is 120 deg CCW
                        step_motor(int((120 / 360.0) * STEPS_PER_REV), clockwise=False)
                        current_step_position = 0
                        print("DONE:0")
                        
                    elif cmd.startswith('ABS:'):
                        try:
                            target_angle = int(cmd.split(':')[1])
                            set_angle(target_angle)
                            current_angle = int((current_step_position / STEPS_PER_REV) * 360)
                            print(f"DONE:{current_angle}")
                        except Exception as e:
                            print("ERROR:Invalid ABS command")
                            
                    elif cmd.startswith('REL:'):
                        try:
                            angle_diff = int(cmd.split(':')[1])
                            clockwise = angle_diff > 0
                            steps = int((abs(angle_diff) / 360.0) * STEPS_PER_REV)
                            step_motor(steps, clockwise)
                            current_angle = int((current_step_position / STEPS_PER_REV) * 360)
                            print(f"DONE:{current_angle}")
                        except Exception as e:
                            print("ERROR:Invalid REL command")
                    else:
                        print("ERROR:Unknown command")
                        
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f"ERROR:{e}")

if __name__ == '__main__':
    try:
        turn_off_motor() # Ensure motor is off initially
        print("Pico W initialized and waiting for serial commands")
        start_serial_server()
    except KeyboardInterrupt:
        print("Code stopped by user.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Powering down motor coils.")
        turn_off_motor()