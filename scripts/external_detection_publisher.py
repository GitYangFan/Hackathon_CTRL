#!/usr/bin/env python3
"""
Example detection publisher for MonoNavi's "external" vision backend.

Publishes ``robot_msgs/msg/Detection2DArray`` on ``/mononavi/detections``
with a synthetic scene — no camera and no model required.  Use it to verify
the wiring, then replace :meth:`publish_frame` with your own perception
output (keep the message contract below unchanged).

Message contract (consumed by ``ExternalVisionModel``):
    class_id : "target" or "obstacle" (case-insensitive).
               Any other value is treated as "obstacle".
    score    : confidence in [0, 1].  MonoNavi drops detections below its
               navigator min_confidence (0.5 by default).
    bbox     : x1, y1, x2, y2 in pixels of the image your detector processed.
               Pass ``--normalized`` here and ``--external_normalized`` to
               MonoNavi if you publish fractions of width/height instead.

The coordinate space must match MonoNavi's reference frame:
    - with a camera running: the camera image resolution;
    - without a camera: MonoNavi's ``external_image_width/height``
      (640x480 by default, matching this example).

Build and source the message package once:
    colcon build --packages-select robot_msgs
    source install/setup.bash

Usage:
    # Terminal 1 — example publisher (target sweeping + a fixed obstacle)
    python3 external_detection_publisher.py

    # Terminal 2 — MonoNavi, pick [4] external
    python3 mononavi_launch.py --enable_viz

    # Other scenes / topics / rates
    python3 external_detection_publisher.py --scenario obstacle --rate 20
    python3 external_detection_publisher.py --topic /my/detections

Then start MonoNavi with ``--external_topic /my/detections`` if you changed
the topic.
"""

from __future__ import annotations

import argparse
import math
import time

import rclpy
from rclpy.node import Node

try:
    from robot_msgs.msg import Detection2D, Detection2DArray
except ImportError:  # pragma: no cover - depends on the build environment
    raise SystemExit(
        "robot_msgs is not available.\n"
        "Build and source it first:\n"
        "    colcon build --packages-select robot_msgs\n"
        "    source install/setup.bash"
    )


class ExampleDetectionPublisher(Node):
    """Publishes a synthetic target/obstacle scene at a fixed rate.

    The target box sweeps slowly left↔right across the upper (far) part of
    the image; the obstacle sits in the lower-left (near) region.  This
    exercises tracking, region arbitration and visualisation.  Replace
    :meth:`publish_frame` with real detector output.
    """

    def __init__(
        self,
        topic: str,
        rate: float,
        width: int,
        height: int,
        scenario: str,
        normalized: bool,
    ) -> None:
        super().__init__("mononavi_example_detection_publisher")
        self._width = width
        self._height = height
        self._scenario = scenario
        self._normalized = normalized
        self._t0 = time.monotonic()

        self._publisher = self.create_publisher(Detection2DArray, topic, 10)
        self._timer = self.create_timer(1.0 / rate, self.publish_frame)

        frame = "normalized [0, 1]" if normalized else f"{width}x{height} px"
        self.get_logger().info(
            f"Publishing synthetic detections on '{topic}' at {rate:.1f} Hz "
            f"(scenario={scenario}, coords={frame})"
        )
        self.get_logger().info(
            "Start MonoNavi and choose [4] external "
            "(or pass --external_topic to match this topic)."
        )

    # ------------------------------------------------------------------
    # Message helpers
    # ------------------------------------------------------------------

    def _make_detection(
        self,
        stamp,
        class_id: str,
        score: float,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
    ) -> Detection2D:
        """Fill one Detection2D.  This is the part your detector must match."""
        det = Detection2D()
        det.header.stamp = stamp
        det.header.frame_id = "camera"
        det.class_id = class_id
        det.score = float(score)
        det.x1 = float(x1)
        det.y1 = float(y1)
        det.x2 = float(x2)
        det.y2 = float(y2)
        return det

    # ------------------------------------------------------------------
    # Synthetic scene
    # ------------------------------------------------------------------

    def publish_frame(self) -> None:
        """Build and publish one frame of detections.

        Replace the synthetic boxes below with your detector's output and
        keep the message construction in :meth:`_make_detection`.
        """
        W, H = self._width, self._height
        t = time.monotonic() - self._t0
        stamp = self.get_clock().now().to_msg()
        detections = []

        if self._scenario in ("target", "both"):
            # Target: ~24% wide, ~30% tall, sweeping gently around the
            # centre.  Foot point (bottom-centre) stays in "Far", so the
            # navigator drives forward and steers toward it.
            cx = W * (0.5 + 0.20 * math.sin(2.0 * math.pi * t / 8.0))
            cy = H * 0.30
            half_w, half_h = W * 0.12, H * 0.15
            detections.append(
                self._make_detection(
                    stamp, "target", 0.90,
                    cx - half_w, cy - half_h, cx + half_w, cy + half_h,
                )
            )

        if self._scenario in ("obstacle", "both"):
            # Obstacle: fixed in the near-left region (lower part of frame).
            ox, oy = W * 0.15, H * 0.70
            half_w, half_h = W * 0.10, H * 0.15
            detections.append(
                self._make_detection(
                    stamp, "obstacle", 0.80,
                    ox - half_w, oy - half_h, ox + half_w, oy + half_h,
                )
            )

        if self._normalized:
            detections = self._to_normalized(detections, W, H)

        msg = Detection2DArray()
        msg.header.stamp = stamp
        msg.header.frame_id = "camera"
        msg.detections = detections
        self._publisher.publish(msg)

    def _to_normalized(
        self, detections: list[Detection2D], width: int, height: int
    ) -> list[Detection2D]:
        """Convert pixel boxes to fractions of width/height (in place)."""
        for det in detections:
            det.x1 /= width
            det.x2 /= width
            det.y1 /= height
            det.y2 /= height
        return detections


def main(args=None) -> None:
    parser = argparse.ArgumentParser(
        description="Publish example detections for MonoNavi's external backend",
        add_help=True,
    )
    parser.add_argument("--topic", type=str, default="/mononavi/detections",
                        help="Topic to publish on (default /mononavi/detections)")
    parser.add_argument("--rate", type=float, default=10.0,
                        help="Publish rate in Hz (default 10)")
    parser.add_argument("--width", type=int, default=640,
                        help="Reference frame width in pixels (default 640)")
    parser.add_argument("--height", type=int, default=480,
                        help="Reference frame height in pixels (default 480)")
    parser.add_argument("--scenario", choices=("target", "obstacle", "both"),
                        default="both",
                        help="Synthetic scene to publish (default both)")
    parser.add_argument("--normalized", action="store_true", default=False,
                        help="Publish bbox coords as fractions of width/height")
    parsed = parser.parse_args(args)

    if parsed.rate <= 0.0:
        parser.error("--rate must be > 0")
    if parsed.width <= 0 or parsed.height <= 0:
        parser.error("--width/--height must be > 0")

    rclpy.init(args=None)
    node = ExampleDetectionPublisher(
        topic=parsed.topic,
        rate=parsed.rate,
        width=parsed.width,
        height=parsed.height,
        scenario=parsed.scenario,
        normalized=parsed.normalized,
    )
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
