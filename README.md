# Project for Hackathon Challenge - Site Safety Patrol

## Running the System

Source the environment in every new terminal first:

```bash
source /opt/ros/humble/setup.bash
source ~/RoboTUNN/install/setup.bash
```

### Step 1: Start the sensors (Terminal 1)

```bash
ros2 launch ~/Hackathon_CTRL/launch/overall_launch_hackathon.launch.py
```

This brings up the three sensor drivers:

- `rslidar_sdk` — 3D LiDAR
- `xsens_mti_ros2_driver` — IMU
- `realsense2_camera` — RGB camera, publishing under `/camera_depth/head/...`

Any driver can be skipped, e.g. `start_lidar:=false`, `start_imu:=false`, or `start_camera:=false`.

### Step 2: Start the robot FSM (Terminal 2)

```bash
cd ~/RoboTUNN/src/FSM/scripts
python3 FSM_b2.py eno1
```

Press Enter at the safety confirmation, then choose the AI controller when
prompted (`1=ai`). Keep the other default parameters unchanged. Wait until the
robot has squatted twice and reached its standby state, then type `Move` and
press Enter to start listening for velocity commands.

> `eno1` is the network interface used to reach the robot; replace it if your
> machine uses a different one.

### Step 3: Start MonoNavi (Terminal 3)

```bash
python3 ~/RoboTUNN/src/MonoNavi/launch/mononavi_launch.py \
    --middle_line_ratio 0.8 \
    --image_topic /camera_depth/head/color/image_raw \
    --enable_viz --reached_continue --use_imu \
    --lidar_denied_range 0.8 --rotate_search true
```

MonoNavi prompts with `Select model number:` on startup — enter `4` to pick the
**external** backend, which consumes the detections published in Step 4.

### Step 4: Start the external detection publisher (Terminal 4)

```bash
python3 ~/RoboTUNN/src/MonoNavi/launch/external_detection_publisher.py
```

Publishes `robot_msgs/msg/Detection2DArray` on `/mononavi/detections` at 10 Hz
by default.

> **Note:** This example script can be replaced by your own detector. Make sure
> the interface stays the same: publish `robot_msgs/msg/Detection2DArray` on
> `/mononavi/detections`, with `class_id` set to `target` or `obstacle` and
> bounding boxes in the camera image's pixel coordinates.

> This repository also contains an identical copy at
> [scripts/external_detection_publisher.py](scripts/external_detection_publisher.py),
> which can be run directly instead.
