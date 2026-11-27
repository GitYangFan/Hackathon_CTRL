# Project for Hackathon Challenge - Site Safety Patrol

> **Note:** This project is intended as a reference framework only. Please do
> not modify any of the local code on this machine. The functional modules
> required for the challenge must be run on each team's own computer.

## Networking with Byte (ROS2)

Configure your computer as follows to communicate with the robot over ROS2:

1. Connect to the onboard 5G module's hotspot:
   - Wi-Fi: `RUT_B1D5_5G`
   - Password: `Rg35SqTd`
2. Set IPv4 to manual assignment:
   - IPv4 address: `192.168.123.190`
   - Netmask: `255.255.255.0`
3. Set the ROS domain:
   ```bash
   export ROS_DOMAIN_ID=1
   ```

> **Warning:** All teams share the same IP address. Do not let multiple teams
> or computers try to communicate with the robot at the same time.

## Running the System

(Please first connect to the Byte onboard Jetson via SSH. Please contact your mentor for login info.)

Source the environment (not necessary on byte because they were added to startup config):

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

> `eno1` is the network interface used to reach the robot; 

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


markdown
## Citation

If you find this work useful in your research, please consider citing our paper:

```bibtex
@article{yourlastname2025mononavi,
  title     = {MonoNavi: A Reactive Map-free Monocular Navigation Framework for Resource-Constrained Robots},
  author    = {Fan Yang, Mia Dietershagen， Xinhua Liu， Katharina Klemt-Albert},
  journal   = {IEEE International Conference on Mechatronics and Machine Vision in Practice},
  year      = {2026},
}
