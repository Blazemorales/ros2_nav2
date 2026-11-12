#!/usr/bin/env python3
"""Mede o RTF comparando o avanço de /clock com o tempo de parede.

`gz stats` não existe no gz_tools_vendor do Jazzy, por isso este script.
Rodar dentro do container, com a simulação estabilizada, sem LLM e sem
exploração ativa, rover parado:

    python3 tools/rtf_meter.py [segundos]   (default: 15)
"""

import sys
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy
from rosgraph_msgs.msg import Clock


class RTFMeter(Node):
    def __init__(self):
        super().__init__("rtf_meter")
        qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )
        self.create_subscription(Clock, "/clock", self._cb, qos)
        self.first_sim = self.first_wall = None
        self.last_sim = self.last_wall = None

    def _cb(self, msg):
        sim = msg.clock.sec + msg.clock.nanosec * 1e-9
        wall = time.monotonic()
        if self.first_sim is None:
            self.first_sim, self.first_wall = sim, wall
        self.last_sim, self.last_wall = sim, wall

    def result(self):
        if self.first_sim is None or self.last_sim == self.first_sim:
            return None
        d_sim = self.last_sim - self.first_sim
        d_wall = self.last_wall - self.first_wall
        return d_sim / d_wall if d_wall > 0 else None


def main():
    duration = float(sys.argv[1]) if len(sys.argv) > 1 else 15.0
    rclpy.init()
    node = RTFMeter()
    deadline = time.monotonic() + duration
    while rclpy.ok() and time.monotonic() < deadline:
        rclpy.spin_once(node, timeout_sec=0.1)
    rtf = node.result()
    node.destroy_node()
    rclpy.shutdown()
    if rtf is None:
        print("ERRO: nenhum dado em /clock. A simulacao esta rodando?")
        sys.exit(1)
    print(f"RTF = {rtf:.3f}  (janela de {duration:.0f} s de parede)")


if __name__ == "__main__":
    main()
