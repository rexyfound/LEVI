import sys
import os
import time
import math
import random
import datetime
from typing import Dict, Any
from html import escape

from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import (
    QColor, QFont, QPainter, QPen, QBrush, QRadialGradient,
    QLinearGradient, QPainterPath, QIcon, QFontDatabase, QTextCursor
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QFrame, QProgressBar,
    QScrollArea, QGridLayout, QMessageBox, QSizePolicy, QToolTip
)

from agent import trigger_interrupt
from assistant_service import run_assistant
from event_bus import event_bus
from memory.memory_manager import load_memory
try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False

try:
    import psutil
except ImportError:
    psutil = None

# Ensure .env is loaded
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
if os.path.exists(env_path):
    load_dotenv(env_path, override=True)
else:
    load_dotenv()


# ═══════════════════════════════════════════════════════════════
#  OBSIDIAN GLASS PALETTE & DESIGN TOKENS
# ═══════════════════════════════════════════════════════════════
# A restrained dark palette improves contrast and lets the state color
# carry the visual focus instead of making every surface glow.
NEU_BG           = "#070a12"   # Application background
NEU_SURFACE      = "#0e1422"   # Raised panel surface
NEU_SURFACE_HI   = "#202b45"   # Top-left edge highlight
NEU_SURFACE_LO   = "#03050a"   # Bottom-right edge shadow
NEU_SUNKEN       = "#090d17"   # Inset / debossed surface
NEU_CARD         = "#121a2b"   # Secondary card surface

TEXT_PRIMARY     = "#f4f7fb"
TEXT_DIM         = "#a7b3c8"
TEXT_MUTED       = "#6f7d95"

ACCENT_PURPLE    = "#8b5cf6"
ACCENT_LAVENDER  = "#c4b5fd"
ACCENT_CYAN      = "#4cc9f0"
ACCENT_GREEN     = "#34d399"
ACCENT_RED       = "#fb7185"
ACCENT_AMBER     = "#fbbf24"
ACCENT_BLUE      = "#60a5fa"


# ═══════════════════════════════════════════════════════════════
#  AGENT WORKER THREAD
# ═══════════════════════════════════════════════════════════════
class AgentWorker(QThread):
    finished_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, prompt: str):
        super().__init__()
        self.prompt = prompt

    def run(self):
        try:
            res = run_assistant(self.prompt)
            self.finished_signal.emit(res)
        except Exception as e:
            self.error_signal.emit(str(e))


class PendingActionWorker(QThread):
    finished_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, action_id, approved: bool):
        super().__init__()
        self.action_id = action_id
        self.approved = approved

    def run(self):
        try:
            from pending_actions import execute_pending_action
            result = execute_pending_action(self.action_id, approved=self.approved)
            self.finished_signal.emit(result if isinstance(result, dict) else {"message": str(result)})
        except Exception as exc:
            self.error_signal.emit(str(exc))


class NeuralBackdrop(QWidget):
    """Lightweight animated network field matching the Figma idle canvas."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.t = 0.0
        random.seed(421)
        self.nodes = []
        for _ in range(128):
            self.nodes.append({
                "x": random.random(),
                "y": random.random(),
                "phase": random.random() * math.tau,
                "speed": random.uniform(0.004, 0.012),
                "cyan": random.random() < 0.18,
                "size": random.uniform(1.0, 2.8),
            })
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(42)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)

    def _tick(self):
        self.t += 1.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = max(1, self.width()), max(1, self.height())
        painter.fillRect(0, 0, w, h, QColor(3, 6, 15))

        points = []
        for node in self.nodes:
            drift = math.sin(self.t * node["speed"] + node["phase"]) * 0.008
            x = (node["x"] + drift) * w
            y = (node["y"] + math.cos(self.t * node["speed"] * 0.8 + node["phase"]) * 0.006) * h
            points.append((x, y, node))

        # Fine constellation lines first, then the brighter nodes on top.
        for index, (x1, y1, node1) in enumerate(points):
            for x2, y2, node2 in points[index + 1:]:
                dx, dy = x1 - x2, y1 - y2
                distance = math.sqrt(dx * dx + dy * dy)
                threshold = min(w, h) * 0.20
                if distance < threshold:
                    alpha = max(10, int(44 * (1.0 - distance / threshold)))
                    if node1["cyan"] or node2["cyan"]:
                        color = QColor(48, 211, 232, alpha)
                    else:
                        color = QColor(137, 92, 246, alpha)
                    painter.setPen(QPen(color, 0.55))
                    painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        for x, y, node in points:
            pulse = 0.72 + 0.28 * math.sin(self.t * node["speed"] * 2.6 + node["phase"])
            if node["cyan"]:
                rgb = (46, 210, 231)
            else:
                rgb = (145, 93, 250)
            glow = QRadialGradient(x, y, node["size"] * 7.0)
            glow.setColorAt(0.0, QColor(*rgb, int(115 * pulse)))
            glow.setColorAt(0.35, QColor(*rgb, int(48 * pulse)))
            glow.setColorAt(1.0, QColor(*rgb, 0))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(glow))
            painter.drawEllipse(QPointF(x, y), node["size"] * 7.0, node["size"] * 7.0)
            painter.setBrush(QBrush(QColor(*rgb, int(165 * pulse))))
            painter.drawEllipse(QPointF(x, y), node["size"], node["size"])

        painter.end()


# ═══════════════════════════════════════════════════════════════
#  NEUMORPHIC CONCAVE REACTOR DISH CANVAS
# ═══════════════════════════════════════════════════════════════
class NeumorphicCoreCanvas(QWidget):
    """Animated 3D-style revolving neural core with live state interaction."""
    core_interaction = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.state = "IDLE"
        self.t = 0.0
        self.paused = False
        self.focus_mode = False
        self.selected_orbit = 0
        # Keep the previous attribute name available for existing integrations.
        self.selected_band = 0
        self.hover_pos = QPointF(-100, -100)
        self.hover_target = ""
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumSize(280, 280)
        self.setToolTip("Click the nucleus to focus. Click an orbit to amplify it. Right-click or press P to pause.")

        random.seed(108)
        self.particles = []
        for _ in range(108):
            self.particles.append({
                "angle": random.uniform(0, math.tau),
                "radius": random.uniform(0.32, 0.98),
                "speed": random.uniform(0.004, 0.018),
                "size": random.uniform(1.1, 3.7),
                "alpha": random.randint(70, 220),
                "orbit": random.randrange(3),
                "phase": random.uniform(0, math.tau),
            })
        # Compatibility collection for older callers/tests that expect fibers.
        self.fibers = [{"angle": random.uniform(0, math.tau), "band": index % 3} for index in range(58)]

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(24)

    def _accent(self):
        color_map = {
            "IDLE": QColor(160, 108, 255), "RECEIVING": QColor(70, 235, 255),
            "PLANNING": QColor(128, 192, 255), "EXECUTING": QColor(205, 248, 255),
            "WAITING_CONFIRMATION": QColor(255, 205, 96), "VALIDATING": QColor(125, 176, 255),
            "COMPLETED": QColor(83, 230, 176), "FAILED": QColor(255, 125, 150),
        }
        return color_map.get(self.state, QColor(80, 210, 255))

    def _geometry(self):
        w, h = self.width(), self.height()
        center = QPointF(w / 2.0, h / 2.0 - 4.0)
        outer_r = max(62.0, min(w, h) * 0.44)
        nucleus_r = outer_r * (0.19 + 0.018 * math.sin(self.t * 2.0))
        return center, outer_r, nucleus_r

    def _hit_target(self, pos):
        center, outer_r, nucleus_r = self._geometry()
        distance = math.hypot(pos.x() - center.x(), pos.y() - center.y())
        if distance <= nucleus_r * 1.55:
            return "nucleus"
        if distance <= outer_r * 1.04:
            return "orbit"
        if distance <= outer_r * 1.16:
            return "glass"
        return ""

    def set_state(self, state: str):
        self.state = state
        self.update()

    def set_focus_mode(self, enabled: bool):
        self.focus_mode = enabled
        self.update()

    def set_paused(self, paused: bool):
        self.paused = paused
        self.update()

    def _tick(self):
        if not self.paused:
            speed_map = {
                "IDLE": 0.010, "RECEIVING": 0.027, "PLANNING": 0.040,
                "EXECUTING": 0.066, "WAITING_CONFIRMATION": 0.004,
                "VALIDATING": 0.028, "COMPLETED": 0.016, "FAILED": 0.055,
            }
            multiplier = 1.32 if self.focus_mode else 1.0
            self.t += speed_map.get(self.state, 0.010) * multiplier
        self.update()

    def mouseMoveEvent(self, event):
        self.hover_pos = event.position()
        self.hover_target = self._hit_target(self.hover_pos)
        self.setCursor(Qt.CursorShape.PointingHandCursor if self.hover_target else Qt.CursorShape.ArrowCursor)
        self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self.hover_pos = QPointF(-100, -100)
        self.hover_target = ""
        self.unsetCursor()
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self.setFocus()
        if event.button() == Qt.MouseButton.RightButton:
            self.paused = not self.paused
            self.core_interaction.emit("paused" if self.paused else "resumed")
            self.update()
            return
        if event.button() != Qt.MouseButton.LeftButton:
            return
        target = self._hit_target(event.position())
        if target == "nucleus":
            self.focus_mode = not self.focus_mode
            self.core_interaction.emit("focus_on" if self.focus_mode else "focus_off")
        elif target == "orbit":
            self.selected_orbit = (self.selected_orbit + 1) % 3
            self.selected_band = self.selected_orbit
            self.core_interaction.emit(f"orbit_{self.selected_orbit + 1}")
        elif target == "glass":
            self.core_interaction.emit("surface")
        self.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self.focus_mode = not self.focus_mode
            self.core_interaction.emit("focus_on" if self.focus_mode else "focus_off")
            self.update()
        elif event.key() == Qt.Key.Key_P:
            self.paused = not self.paused
            self.core_interaction.emit("paused" if self.paused else "resumed")
            self.update()
        else:
            super().keyPressEvent(event)

    def _draw_rotated_ring(self, painter, center, radius, y_scale, rotation, color, width, arc_offset=0):
        painter.save()
        painter.translate(center)
        painter.rotate(rotation)
        painter.scale(1.0, y_scale)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(color, width))
        painter.drawEllipse(QPointF(0, 0), radius, radius)
        painter.setPen(QPen(QColor(color.red(), color.green(), color.blue(), min(255, color.alpha() + 80)), width + 0.8))
        painter.drawArc(int(-radius), int(-radius), int(radius * 2), int(radius * 2), int(arc_offset * 16), int(78 * 16))
        painter.restore()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        w, h = self.width(), self.height()
        center, outer_r, nucleus_r = self._geometry()
        cx, cy = center.x(), center.y()
        accent = self._accent()

        # Circular glass surface rather than the old rectangular reactor dish.
        disk_r = outer_r * 1.04
        shadow = QRadialGradient(cx, cy, disk_r * 1.22)
        shadow.setColorAt(0.0, QColor(12, 7, 34, 188))
        shadow.setColorAt(0.72, QColor(10, 7, 30, 148))
        shadow.setColorAt(1.0, QColor(5, 6, 17, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(shadow))
        painter.drawEllipse(center, disk_r * 1.20, disk_r * 1.20)

        glass = QRadialGradient(cx - disk_r * 0.18, cy - disk_r * 0.24, disk_r * 1.12)
        glass.setColorAt(0.0, QColor(31, 23, 66, 168))
        glass.setColorAt(0.48, QColor(13, 13, 36, 185))
        glass.setColorAt(0.92, QColor(8, 8, 23, 215))
        glass.setColorAt(1.0, QColor(6, 7, 18, 230))
        painter.setBrush(QBrush(glass))
        painter.drawEllipse(center, disk_r, disk_r)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(143, 115, 255, 78), 1.0))
        painter.drawEllipse(center, disk_r, disk_r)
        painter.setPen(QPen(QColor(80, 211, 231, 32), 0.65))
        painter.drawEllipse(center, disk_r * 0.95, disk_r * 0.95)

        # Three orbital traces and softly glowing particles.
        orbit_r = disk_r * 0.72
        orbit_specs = ((0.28, -12.0), (0.54, 19.0), (0.82, -28.0))
        for orbit_index, (y_scale, tilt) in enumerate(orbit_specs):
            selected = orbit_index == self.selected_orbit
            alpha = 112 if selected else 38
            color = QColor(accent.red(), accent.green(), accent.blue(), alpha)
            self._draw_rotated_ring(
                painter, center, orbit_r * (0.92 + orbit_index * 0.045),
                y_scale, tilt + math.sin(self.t * 0.28 + orbit_index) * 8.0,
                color, 1.25 if selected else 0.7, self.t * 42 + orbit_index * 110,
            )

        particles = []
        for particle in self.particles:
            angle = particle["angle"] + self.t * particle["speed"] * 42
            orbit_index = particle["orbit"]
            y_scale = orbit_specs[orbit_index][0]
            radius = orbit_r * particle["radius"] * (0.88 + orbit_index * 0.04)
            depth = (math.sin(angle) + 1.0) / 2.0
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle) * y_scale
            particles.append((depth, x, y, particle, orbit_index))
        particles.sort(key=lambda item: item[0])
        for depth, x, y, particle, orbit_index in particles:
            selected = orbit_index == self.selected_orbit
            size = particle["size"] * (0.48 + depth * 0.72) * (1.18 if selected else 0.78)
            alpha = int(particle["alpha"] * (0.28 + depth * 0.64))
            color = QColor(190, 166, 255, max(22, alpha)) if not particle.get("cyan") else QColor(98, 228, 239, max(22, alpha))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(color.red(), color.green(), color.blue(), max(10, alpha // 4))))
            painter.drawEllipse(QPointF(x, y), size * 3.2, size * 3.2)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPointF(x, y), size, size)

        # Violet center star and low-key bloom.
        bloom = QRadialGradient(cx, cy, nucleus_r * 3.8)
        bloom.setColorAt(0.0, QColor(238, 225, 255, 210))
        bloom.setColorAt(0.16, QColor(190, 137, 255, 170))
        bloom.setColorAt(0.48, QColor(133, 77, 245, 62))
        bloom.setColorAt(1.0, QColor(98, 60, 200, 0))
        painter.setBrush(QBrush(bloom))
        painter.drawEllipse(center, nucleus_r * 3.8, nucleus_r * 3.8)

        painter.save()
        painter.translate(center)
        painter.rotate(self.t * 12)
        painter.setPen(QPen(QColor(214, 180, 255, 145), 1.0))
        painter.drawLine(QPointF(-nucleus_r * 0.86, 0), QPointF(nucleus_r * 0.86, 0))
        painter.drawLine(QPointF(0, -nucleus_r * 0.86), QPointF(0, nucleus_r * 0.86))
        painter.setPen(QPen(QColor(162, 103, 255, 110), 0.8))
        painter.drawLine(QPointF(-nucleus_r * 0.60, -nucleus_r * 0.36), QPointF(nucleus_r * 0.60, nucleus_r * 0.36))
        painter.restore()

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(250, 242, 255, 250)))
        painter.drawEllipse(center, max(4.5, nucleus_r * 0.075), max(4.5, nucleus_r * 0.075))
        painter.setBrush(QBrush(QColor(191, 136, 255, 170)))
        painter.drawEllipse(center, max(14.0, nucleus_r * 0.26), max(14.0, nucleus_r * 0.26))
        painter.setBrush(QBrush(QColor(250, 242, 255, 255)))
        painter.drawEllipse(center, max(4.5, nucleus_r * 0.075), max(4.5, nucleus_r * 0.075))

        if self.hover_target:
            hover_radius = 20 if self.hover_target == "nucleus" else 13
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(218, 192, 255, 210), 1.0))
            painter.drawEllipse(self.hover_pos, hover_radius, hover_radius)

        state_label = "IDLE" if self.state == "IDLE" else self.state.replace("_", " ")
        painter.setPen(QColor(190, 154, 255, 235))
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        painter.drawText(QRectF(20, cy + disk_r * 0.57, w - 40, 18), Qt.AlignmentFlag.AlignCenter, state_label)
        painter.setPen(QColor(112, 105, 145, 210))
        painter.setFont(QFont("Segoe UI", 8))
        painter.drawText(QRectF(20, cy + disk_r * 0.68, w - 40, 16), Qt.AlignmentFlag.AlignCenter, "●  LEVI  ·  AIS")
        painter.end()


# ═══════════════════════════════════════════════════════════════
#  NEUMORPHIC UI COMPONENT BUILDERS
# ═══════════════════════════════════════════════════════════════
def make_neu_panel(parent=None):
    """Raised Neumorphic Panel with dual-shadow borders."""
    f = QFrame(parent)
    f.setStyleSheet(f"""
        QFrame {{
            background: {NEU_SURFACE};
            border-top: 1px solid {NEU_SURFACE_HI};
            border-left: 1px solid {NEU_SURFACE_HI};
            border-right: 1px solid {NEU_SURFACE_LO};
            border-bottom: 2px solid {NEU_SURFACE_LO};
            border-radius: 18px;
        }}
    """)
    return f


def make_neu_stat_box(title: str, value: str, color: str = ACCENT_LAVENDER):
    """Raised tactile stat tile."""
    frame = QFrame()
    frame.setStyleSheet(f"""
        QFrame {{
            background: {NEU_CARD};
            border-top: 1px solid {NEU_SURFACE_HI};
            border-left: 1px solid {NEU_SURFACE_HI};
            border-right: 1px solid {NEU_SURFACE_LO};
            border-bottom: 1px solid {NEU_SURFACE_LO};
            border-radius: 14px;
        }}
    """)
    frame.setMinimumHeight(54)
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(14, 10, 14, 10)
    lay.setSpacing(3)
    t = QLabel(title)
    t.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 8.5px; font-weight: 700; letter-spacing: 1px; border: none; background: transparent;")
    v = QLabel(value)
    v.setObjectName("stat_value")
    v.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold; border: none; background: transparent;")
    lay.addWidget(t)
    lay.addWidget(v)
    return frame


def make_neu_tool_row(icon: str, name: str, desc: str, status: str = "IDLE"):
    """Soft tactile tool button with status LED."""
    row = QFrame()
    row.setStyleSheet(f"""
        QFrame {{
            background: {NEU_CARD};
            border-top: 1px solid {NEU_SURFACE_HI};
            border-left: 1px solid {NEU_SURFACE_HI};
            border-right: 1px solid {NEU_SURFACE_LO};
            border-bottom: 1px solid {NEU_SURFACE_LO};
            border-radius: 10px;
        }}
        QFrame:hover {{
            background: #151b2c;
            border-top: 1px solid {ACCENT_PURPLE};
        }}
    """)
    lay = QHBoxLayout(row)
    row.setMinimumHeight(42)
    lay.setContentsMargins(10, 6, 10, 6)
    lay.setSpacing(9)

    ic = QLabel(icon)
    ic.setFixedWidth(20)
    ic.setStyleSheet(f"color: {ACCENT_LAVENDER}; font-size: 11.5px; border: none; background: transparent;")

    info = QFrame()
    info.setStyleSheet("border: none; background: transparent;")
    info_lay = QVBoxLayout(info)
    info_lay.setContentsMargins(0, 0, 0, 0)
    info_lay.setSpacing(0)
    n = QLabel(name)
    n.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 9.5px; font-weight: bold; border: none;")
    d = QLabel(desc)
    d.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 8px; border: none;")
    info_lay.addWidget(n)
    info_lay.addWidget(d)

    s = QLabel(f"● {status}")
    s.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    s.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 8px; font-weight: bold; border: none; background: transparent;")

    lay.addWidget(ic)
    lay.addWidget(info, 1)
    lay.addWidget(s)
    return row


def make_neu_pipeline_step(label: str, desc: str, is_active: bool = False):
    """Raised / illuminated neumorphic pipeline step."""
    frame = QFrame()
    if is_active:
        style = f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #7c3aed, stop:1 #4338ca);
                border-top: 1px solid {ACCENT_LAVENDER};
                border-left: 1px solid {ACCENT_LAVENDER};
                border-right: 1px solid #1e1b4b;
                border-bottom: 2px solid #1e1b4b;
                border-radius: 10px;
            }}
        """
    else:
        style = f"""
            QFrame {{
                background: {NEU_CARD};
                border-top: 1px solid {NEU_SURFACE_HI};
                border-left: 1px solid {NEU_SURFACE_HI};
                border-right: 1px solid {NEU_SURFACE_LO};
                border-bottom: 1px solid {NEU_SURFACE_LO};
                border-radius: 10px;
            }}
        """
    frame.setStyleSheet(style)
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(8, 6, 8, 6)
    lay.setSpacing(2)
    l = QLabel(label)
    l.setStyleSheet(f"color: {'#ffffff' if is_active else TEXT_DIM}; font-size: 8.5px; font-weight: 800; letter-spacing: 1px; border: none; background: transparent;")
    l.setAlignment(Qt.AlignmentFlag.AlignCenter)
    d = QLabel(desc)
    d.setStyleSheet(f"color: {'#f3e8ff' if is_active else TEXT_MUTED}; font-size: 7.5px; border: none; background: transparent;")
    d.setAlignment(Qt.AlignmentFlag.AlignCenter)
    d.setWordWrap(True)
    lay.addWidget(l)
    lay.addWidget(d)
    return frame


# ═══════════════════════════════════════════════════════════════
#  MAIN LEVI NEUMORPHIC HUD WINDOW
# ═══════════════════════════════════════════════════════════════
class LEVIHUDWindow(QMainWindow):
    external_event_signal = pyqtSignal(object)
    BUSY_STATES = {"RECEIVING", "PLANNING", "EXECUTING", "WAITING_CONFIRMATION", "VALIDATING"}

    def __init__(self):
        super().__init__()
        self.setWindowTitle("LEVI OS — Adaptive Intelligence Control Surface")
        self.resize(1440, 900)
        self.setMinimumSize(1180, 760)
        self.current_state = "IDLE"
        self.worker = None
        self.b_worker = None
        self.pending_worker = None
        self.start_time = time.time()
        self._active_task_started = None
        self._task_generation = 0
        self._active_task_generation = 0
        self._interrupt_requested = False
        self._last_live_phase = None
        self._event_bus_binding = None
        self._metric_tokens = 2341
        self._context_used_k = 24
        self._context_limit_k = 128
        self._metric_steps = 0
        self._metric_depth = "High"
        self._last_metric_event = 0.0
        self._last_wake_mode = None

        self._build_ui()
        self._setup_timers()
        self._apply_state_visuals(self.current_state)
        self.input_field.setFocus()
        QTimer.singleShot(600, self._start_wake_listener)

    def _start_wake_listener(self):
        try:
            from voice.wake_listener import wake_listener
            wake_listener.on_command = self._on_wake_command
            wake_listener.start()
        except Exception:
            pass

    def _build_ui(self):
        """Build the calm, core-first native desktop composition."""
        self.setStyleSheet(f"""
            QMainWindow {{ background: {NEU_BG}; }}
            QWidget {{ color: {TEXT_PRIMARY}; font-family: 'Segoe UI', 'Consolas', sans-serif; font-size: 10px; }}
            QToolTip {{ background: #0b1020; color: {TEXT_PRIMARY}; border: 1px solid #2c3154; border-radius: 8px; padding: 6px 10px; font-size: 9px; }}
            QLineEdit:focus, QTextEdit:focus {{ border-color: {ACCENT_PURPLE}; }}
            QLineEdit::selection, QTextEdit::selection {{ background: #4c1d95; color: #ffffff; }}
            QPushButton:disabled {{ color: {TEXT_MUTED}; }}
            QScrollBar:vertical {{ width: 5px; background: transparent; }}
            QScrollBar::handle:vertical {{ background: #2a3150; border-radius: 2px; min-height: 22px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        root = NeuralBackdrop()
        root.setObjectName('leviRoot')
        root.setStyleSheet("QWidget#leviRoot { background: transparent; }")
        self.setCentralWidget(root)
        root_lay = QVBoxLayout(root)
        root_lay.setContentsMargins(14, 10, 14, 12)
        root_lay.setSpacing(8)

        # Compatibility state and telemetry widgets remain available to the
        # existing event/metric handlers, but are not permanently displayed.
        self.clock_lbl = QLabel()
        self.date_lbl = QLabel()
        self.uptime_val = QLabel('00:00:00')
        self.cpu_val = QLabel('—%')
        self.ram_val = QLabel('— GB')
        self.voice_lbl = QLabel('VOICE   Native')
        self.stat_token_value = QLabel('2,341')
        self.stat_context_value = QLabel('24K / 128K')
        self.stat_steps_value = QLabel('0 / 6')
        self.stat_depth_value = QLabel('High')
        self.context_token_tag = QLabel('24K / 128K')
        self.pipe_steps = []

        # Compact top identity bar: branding left, operational state right.
        top_bar = QFrame()
        top_bar.setFixedHeight(42)
        top_bar.setStyleSheet("""
            QFrame { background: rgba(12, 18, 34, 0.62); border: 1px solid rgba(255,255,255,0.07); border-radius: 18px; }
        """)
        top_lay = QHBoxLayout(top_bar)
        top_lay.setContentsMargins(12, 4, 12, 4)
        top_lay.setSpacing(8)

        logo = QLabel('●  LEVI')
        logo.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 12px; font-weight: 800; letter-spacing: 3px; background: transparent; border: none;")
        ais = QLabel('AIS')
        ais.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 8px; letter-spacing: 1.5px; background: transparent; border: none;")
        top_lay.addWidget(logo)
        top_lay.addWidget(ais)
        top_lay.addStretch()

        self.status_badge = QLabel('● OPTIMAL')
        self.status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_badge.setStyleSheet(f"color: {ACCENT_GREEN}; background: rgba(7, 14, 22, 0.72); border: 1px solid rgba(52,211,153,0.28); border-radius: 12px; padding: 5px 10px; font-size: 8px; font-weight: 800; letter-spacing: 1px;")
        top_lay.addWidget(self.status_badge)
        root_lay.addWidget(top_bar)

        # Main scene is deliberately borderless; the neural core is the visual identity.
        scene = QWidget(root)
        scene.setObjectName('leviScene')
        scene.setStyleSheet('QWidget#leviScene { background: transparent; border: none; }')
        scene_lay = QVBoxLayout(scene)
        scene_lay.setContentsMargins(58, 2, 30, 2)
        scene_lay.setSpacing(8)
        scene_lay.addStretch(2)

        self.core_canvas = NeumorphicCoreCanvas(scene)
        self.core_canvas.setMinimumSize(390, 390)
        self.core_canvas.setMaximumSize(560, 560)
        self.core_canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.core_canvas.core_interaction.connect(self._on_core_interaction)
        scene_lay.addWidget(self.core_canvas, 0, Qt.AlignmentFlag.AlignHCenter)

        self.state_badge = QLabel('IDLE')
        self.state_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.state_badge.setStyleSheet(f"color: {TEXT_DIM}; background: transparent; border: none; font-size: 11px; letter-spacing: 2px; padding: 1px 8px;")
        scene_lay.addWidget(self.state_badge, 0, Qt.AlignmentFlag.AlignHCenter)

        # Conversation is hidden until the first request or Chat is selected.
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setMinimumHeight(110)
        self.chat_display.setMaximumHeight(250)
        self.chat_display.setMinimumWidth(420)
        self.chat_display.setMaximumWidth(700)
        self.chat_display.setVisible(False)
        self.chat_display.setStyleSheet("""
            QTextEdit { background: rgba(6, 11, 22, 0.72); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; color: #e8edf7; padding: 12px 14px; font-size: 11px; }
        """)
        self.chat_display.setHtml(f"<div style='color:{TEXT_MUTED}; font-size:10px;'>Conversation will appear here.</div>")
        scene_lay.addWidget(self.chat_display, 0, Qt.AlignmentFlag.AlignHCenter)

        # Primary command bar directly beneath the core/conversation.
        command_dock = QFrame()
        command_dock.setMaximumWidth(700)
        command_dock.setMinimumHeight(54)
        command_dock.setStyleSheet("""
            QFrame { background: rgba(4, 8, 16, 0.82); border: 1px solid rgba(255,255,255,0.10); border-radius: 17px; }
        """)
        command_lay = QHBoxLayout(command_dock)
        command_lay.setContentsMargins(9, 8, 9, 8)
        command_lay.setSpacing(7)

        self.briefing_icon_btn = QPushButton('✦')
        self.briefing_icon_btn.setFixedSize(30, 30)
        self.briefing_icon_btn.setToolTip('Launch morning briefing')
        self.briefing_icon_btn.setStyleSheet(f"QPushButton {{ color: {ACCENT_CYAN}; background: transparent; border: none; font-size: 15px; }} QPushButton:hover {{ color: #ffffff; }}")
        self.briefing_icon_btn.clicked.connect(self.trigger_two_phase_briefing)
        # Briefing is a secondary utility, kept subtle rather than dashboard-like.
        self.briefing_icon_btn.setVisible(False)

        self.interrupt_icon_btn = QPushButton('■')
        self.interrupt_icon_btn.setFixedSize(28, 28)
        self.interrupt_icon_btn.setToolTip('Interrupt execution')
        self.interrupt_icon_btn.setStyleSheet(f"QPushButton {{ color: {ACCENT_RED}; background: transparent; border: none; font-size: 12px; }} QPushButton:hover {{ color: #ffffff; }}")
        self.interrupt_icon_btn.clicked.connect(self.on_interrupt_clicked)
        self.interrupt_icon_btn.setVisible(False)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText('Ask LEVI anything...')
        self.input_field.setClearButtonEnabled(False)
        self.input_field.setStyleSheet(f"QLineEdit {{ background: transparent; border: none; color: {TEXT_PRIMARY}; font-size: 12px; padding: 3px 2px; }}")
        self.input_field.returnPressed.connect(self.send_command)

        self.voice_input_btn = QPushButton('◉')
        self.voice_input_btn.setFixedSize(30, 30)
        self.voice_input_btn.setToolTip('Voice input')
        self.voice_input_btn.setStyleSheet(f"QPushButton {{ color: {TEXT_MUTED}; background: rgba(18, 26, 43, 0.55); border: 1px solid rgba(255,255,255,0.07); border-radius: 10px; font-size: 12px; }} QPushButton:hover {{ color: {ACCENT_LAVENDER}; border-color: rgba(139,92,246,0.45); }}")
        self.voice_input_btn.clicked.connect(self._toggle_voice_input)

        self.send_icon_btn = QPushButton('↑')
        self.send_icon_btn.setFixedSize(30, 30)
        self.send_icon_btn.setToolTip('Send command')
        self.send_icon_btn.setStyleSheet(f"QPushButton {{ color: {ACCENT_LAVENDER}; background: rgba(30,18,55,0.72); border: 1px solid rgba(139,92,246,0.35); border-radius: 10px; font-size: 16px; font-weight: 700; }} QPushButton:hover {{ background: rgba(80,45,130,0.82); }} QPushButton:disabled {{ color: #4b4860; border-color: rgba(255,255,255,0.05); }}")
        self.send_icon_btn.clicked.connect(self.send_command)

        command_lay.addWidget(self.interrupt_icon_btn)
        prompt_mark = QLabel('>')
        prompt_mark.setStyleSheet(f"color: {ACCENT_PURPLE}; font-size: 15px; background: transparent; border: none; padding: 0 2px;")
        command_lay.addWidget(prompt_mark)
        command_lay.addWidget(self.input_field, 1)
        command_lay.addWidget(self.voice_input_btn)
        command_lay.addWidget(self.send_icon_btn)
        scene_lay.addWidget(command_dock, 0, Qt.AlignmentFlag.AlignHCenter)
        scene_lay.addStretch(2)
        root_lay.addWidget(scene, 1)

        # Middle-left floating rail. It never consumes the central composition.
        self.rail = QFrame(root)
        self.rail.setObjectName('leviRail')
        self.rail.setStyleSheet("""
            QFrame#leviRail { background: rgba(10,16,28,0.62); border: 1px solid rgba(255,255,255,0.08); border-radius: 15px; }
            QPushButton { color: #68758d; background: transparent; border: none; border-radius: 9px; font-size: 13px; }
            QPushButton:hover { color: #c4b5fd; background: rgba(30,22,55,0.62); }
            QPushButton:checked { color: #c4b5fd; background: rgba(4,7,14,0.76); border: 1px solid rgba(139,92,246,0.25); }
        """)
        rail_lay = QVBoxLayout(self.rail)
        rail_lay.setContentsMargins(6, 8, 6, 8)
        rail_lay.setSpacing(3)
        rail_items = [
            ('◉', 'Chat', self._toggle_chat_view),
            ('▣', 'System', lambda: self._toggle_panel('system')),
            ('◌', 'Memory', lambda: self._toggle_panel('memory')),
            ('✦', 'Tools', lambda: self._toggle_panel('tools')),
            ('⌁', 'Activity', lambda: self._toggle_panel('activity')),
            ('◒', 'Voice', lambda: self._toggle_panel('voice')),
            ('◎', 'Vision', lambda: self._toggle_panel('vision')),
        ]
        self.rail_buttons = {}
        for icon, label, callback in rail_items:
            button = QPushButton(icon)
            button.setCheckable(True)
            button.setFixedSize(32, 32)
            button.setToolTip(label)
            button.clicked.connect(callback)
            self.rail_buttons[label.lower()] = button
            rail_lay.addWidget(button)
        rail_lay.addSpacing(3)
        rail_lay.addWidget(self.briefing_icon_btn)
        self.rail.adjustSize()
        self.rail.raise_()

        # Floating contextual panel, hidden until explicitly requested.
        self.open_panel = None
        self.panel_frame = QFrame(root)
        self.panel_frame.setObjectName('leviOverlay')
        self.panel_frame.setFixedWidth(308)
        self.panel_frame.setMaximumHeight(520)
        self.panel_frame.setStyleSheet("""
            QFrame#leviOverlay { background: rgba(9,14,26,0.92); border: 1px solid rgba(255,255,255,0.10); border-radius: 17px; }
            QLabel { background: transparent; border: none; }
            QLineEdit { background: rgba(4,7,14,0.72); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; color: #e8edf7; padding: 8px 10px; }
            QScrollBar:vertical { width: 5px; background: transparent; }
            QScrollBar::handle:vertical { background: #303657; border-radius: 2px; min-height: 18px; }
        """)
        panel_lay = QVBoxLayout(self.panel_frame)
        panel_lay.setContentsMargins(0, 0, 0, 0)
        panel_lay.setSpacing(0)
        panel_header = QFrame()
        panel_header.setStyleSheet('QFrame { background: rgba(5,9,18,0.60); border: none; border-bottom: 1px solid rgba(255,255,255,0.07); border-top-left-radius: 17px; border-top-right-radius: 17px; }')
        header_lay = QHBoxLayout(panel_header)
        header_lay.setContentsMargins(14, 9, 10, 9)
        self.panel_title = QLabel('PANEL')
        self.panel_title.setStyleSheet(f"color: {TEXT_DIM}; font-size: 9px; font-weight: 800; letter-spacing: 2px;")
        header_lay.addWidget(self.panel_title)
        header_lay.addStretch()
        close_btn = QPushButton('×')
        close_btn.setFixedSize(22, 22)
        close_btn.setToolTip('Close')
        close_btn.setStyleSheet(f"QPushButton {{ color: {TEXT_MUTED}; background: rgba(18,26,43,0.55); border: 1px solid rgba(255,255,255,0.07); border-radius: 11px; font-size: 15px; }} QPushButton:hover {{ color: #ffffff; }}")
        close_btn.clicked.connect(self._close_panel)
        header_lay.addWidget(close_btn)
        panel_lay.addWidget(panel_header)
        self.panel_body = QWidget()
        self.panel_body_lay = QVBoxLayout(self.panel_body)
        self.panel_body_lay.setContentsMargins(12, 12, 12, 12)
        self.panel_body_lay.setSpacing(8)
        panel_lay.addWidget(self.panel_body)
        self.panel_frame.hide()
        self.help_btn = QPushButton('?')
        self.help_btn.setFixedSize(34, 34)
        self.help_btn.setToolTip('LEVI controls: click the core to focus; Space toggles focus; P pauses the field.')
        self.help_btn.setStyleSheet(f"QPushButton {{ color: {TEXT_PRIMARY}; background: rgba(13,18,31,0.76); border: 1px solid rgba(255,255,255,0.18); border-radius: 17px; font-size: 16px; }} QPushButton:hover {{ background: rgba(32,24,65,0.9); border-color: rgba(161,120,255,0.7); }}")
        self.help_btn.clicked.connect(lambda: QToolTip.showText(self.help_btn.mapToGlobal(QPointF(0, -8).toPoint()), self.help_btn.toolTip(), self.help_btn))
        self.open_panel = None
        self._chat_visible = False
        self._activity_has_entries = False
        for button in self.rail_buttons.values():
            button.setChecked(False)
        self._position_floating_widgets()
        self.panel_frame.raise_()

        self.conv_status = QLabel('● READY')
        self.core_status = QLabel('● ACTIVE')
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.activity_list = QTextEdit()
        self.activity_list.setReadOnly(True)
        self.activity_list.setStyleSheet(f"QTextEdit {{ background: rgba(4,7,14,0.72); border: 1px solid rgba(255,255,255,0.08); border-radius: 11px; color: {TEXT_DIM}; padding: 8px; font-size: 9px; }}")
        self.activity_list.setHtml(f"<div style='color:{TEXT_MUTED}; padding:8px;'>No recent activity</div>")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_floating_widgets()

    def _position_floating_widgets(self):
        if not hasattr(self, 'rail'):
            return
        margin_y = max(70, int((self.height() - self.rail.height()) / 2))
        self.rail.move(10, margin_y)
        self.rail.raise_()
        if hasattr(self, 'panel_frame'):
            panel_y = max(58, int((self.height() - self.panel_frame.height()) / 2))
            self.panel_frame.move(62, panel_y)
            self.panel_frame.raise_()
        if hasattr(self, 'help_btn'):
            self.help_btn.move(max(10, self.width() - 52), max(10, self.height() - 50))
            self.help_btn.raise_()
        self.help_btn.raise_()

    def _clear_panel_body(self):
        while self.panel_body_lay.count():
            item = self.panel_body_lay.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)

    def _panel_row(self, label, value, color=None):
        row = QFrame()
        row.setStyleSheet('QFrame { background: rgba(4,7,14,0.64); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; }')
        lay = QHBoxLayout(row)
        lay.setContentsMargins(10, 7, 10, 7)
        left = QLabel(str(label))
        left.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 9px; letter-spacing: 1px;")
        right = QLabel(str(value))
        right.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        right.setStyleSheet(f"color: {color or TEXT_DIM}; font-size: 9px; font-weight: 700;")
        lay.addWidget(left)
        lay.addStretch()
        lay.addWidget(right)
        return row

    def _toggle_chat_view(self):
        self.open_panel = None
        self.panel_frame.hide()
        self._chat_visible = not getattr(self, '_chat_visible', False)
        self.chat_display.setVisible(self._chat_visible)
        self.rail_buttons['chat'].setChecked(self._chat_visible)
        self._position_floating_widgets()

    def _close_panel(self):
        self.open_panel = None
        self.panel_frame.hide()
        for key, button in self.rail_buttons.items():
            if key != 'chat':
                button.setChecked(False)
        self._position_floating_widgets()

    def _toggle_panel(self, panel_name):
        if self.open_panel == panel_name:
            self._close_panel()
            return
        self.open_panel = panel_name
        self._chat_visible = False
        self.chat_display.setVisible(False)
        self.rail_buttons['chat'].setChecked(False)
        for key, button in self.rail_buttons.items():
            if key != 'chat':
                button.setChecked(key == panel_name)
        self._populate_panel(panel_name)
        self.panel_frame.show()
        self.panel_frame.adjustSize()
        self._position_floating_widgets()

    def _populate_panel(self, panel_name):
        self._clear_panel_body()
        titles = {'system': 'SYSTEM', 'memory': 'MEMORY', 'tools': 'TOOLS', 'activity': 'ACTIVITY', 'voice': 'VOICE', 'vision': 'VISION'}
        self.panel_title.setText(titles.get(panel_name, panel_name.upper()))

        if panel_name == 'system':
            rows = [('CPU', self.cpu_val.text()), ('RAM', self.ram_val.text()), ('GPU', 'N/A'), ('NETWORK', 'N/A'), ('UPTIME', self.uptime_val.text()), ('LATENCY', 'N/A')]
            for label, value in rows:
                self.panel_body_lay.addWidget(self._panel_row(label, value))
            note = QLabel('Live system values appear here only when requested.')
            note.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 9px; padding: 3px;")
            note.setWordWrap(True)
            self.panel_body_lay.addWidget(note)
        elif panel_name == 'memory':
            try:
                data = load_memory() or {}
                sessions = data.get('sessions', []) if isinstance(data, dict) else []
                projects = data.get('active_projects', []) if isinstance(data, dict) else []
                topics = data.get('monitored_topics', []) if isinstance(data, dict) else []
                recent = sessions[-3:] if isinstance(sessions, list) else []
            except Exception:
                sessions, projects, topics, recent = [], [], [], []
            self.panel_body_lay.addWidget(self._panel_row('LONG-TERM', f'{len(projects) + len(topics)} items'))
            self.panel_body_lay.addWidget(self._panel_row('RECENT', f'{len(sessions)} items'))
            search = QLineEdit()
            search.setPlaceholderText('Search memory...')
            self.panel_body_lay.addWidget(search)
            if recent:
                for item in recent:
                    text = item.get('summary', item.get('text', str(item))) if isinstance(item, dict) else str(item)
                    label = QLabel(str(text)[:120])
                    label.setWordWrap(True)
                    label.setStyleSheet(f"color: {TEXT_DIM}; font-size: 9px; padding: 3px;")
                    self.panel_body_lay.addWidget(label)
            else:
                empty = QLabel('No recent memories')
                empty.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 9px; padding: 3px;")
                self.panel_body_lay.addWidget(empty)
        elif panel_name == 'tools':
            for tool in ('BROWSER', 'DESKTOP', 'TERMINAL', 'MEMORY', 'VISION', 'VOICE'):
                self.panel_body_lay.addWidget(self._panel_row(tool, 'READY', ACCENT_GREEN))
        elif panel_name == 'activity':
            self.activity_list.setMinimumHeight(220)
            if not self._activity_has_entries:
                self.activity_list.setHtml(f"<div style='color:{TEXT_MUTED}; padding:8px;'>No recent activity</div>")
            self.panel_body_lay.addWidget(self.activity_list)
        elif panel_name == 'voice':
            try:
                from voice import get_voice_state
                voice_state = get_voice_state()
                state_text = voice_state.value if hasattr(voice_state, 'value') else str(voice_state)
            except Exception:
                state_text = 'IDLE'
            self.panel_body_lay.addWidget(self._panel_row('STATUS', state_text))
            self.panel_body_lay.addWidget(self._panel_row('VOICE', 'LEVI'))
            self.panel_body_lay.addWidget(self._panel_row('SPEED', '0.95x'))
            self.panel_body_lay.addWidget(self._panel_row('STYLE', 'Calm'))
        elif panel_name == 'vision':
            self.panel_body_lay.addWidget(self._panel_row('SCREEN CAPTURE', 'READY', ACCENT_GREEN))
            placeholder = QLabel('No capture active\n\nDetected: none')
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet(f"color: {TEXT_MUTED}; background: rgba(4,7,14,0.64); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 22px 8px;")
            self.panel_body_lay.addWidget(placeholder)

    def _toggle_voice_input(self):
        active = not getattr(self, '_voice_input_active', True)
        try:
            from voice.wake_listener import wake_listener
            if active:
                active = wake_listener.start()
            else:
                wake_listener.stop()
        except Exception:
            active = False
        self._voice_input_active = active
        self.voice_input_btn.setStyleSheet(f"QPushButton {{ color: {ACCENT_LAVENDER if active else TEXT_MUTED}; background: rgba(30,18,55,0.72); border: 1px solid {('rgba(139,92,246,0.45)' if active else 'rgba(255,255,255,0.07)')}; border-radius: 10px; font-size: 12px; }}")
        self.add_activity('Voice input enabled' if active else 'Voice input disabled')

    def _refresh_wake_status(self):
        """Reflect the background listener state without blocking the GUI."""
        try:
            from voice.wake_listener import wake_listener
            status = wake_listener.status()
            mode = status.get('mode', 'stopped')
            active = bool(status.get('running')) and mode in {'starting', 'listening', 'capturing'}
            self._voice_input_active = active
            if hasattr(self, 'voice_input_btn'):
                label = 'Voice input: listening for LEVI' if mode == 'listening' else f'Voice input: {mode}'
                if status.get('last_error'):
                    label += f" — {status['last_error']}"
                self.voice_input_btn.setToolTip(label)
                self.voice_input_btn.setStyleSheet(f"QPushButton {{ color: {ACCENT_LAVENDER if active else TEXT_MUTED}; background: rgba(30,18,55,0.72); border: 1px solid {('rgba(139,92,246,0.45)' if active else 'rgba(255,255,255,0.07)')}; border-radius: 10px; font-size: 12px; }}")
            if mode != self._last_wake_mode:
                self._last_wake_mode = mode
                if mode == 'listening':
                    self.add_activity('Wake listener ready')
                elif mode in {'unavailable', 'error'}:
                    self.add_activity(f"Wake listener unavailable: {status.get('last_error', mode)}")
        except Exception:
            pass

    def _on_wake_command(self, text: str):
        """Marshal a microphone command from the listener thread to Qt."""
        self.external_event_signal.emit({'type': 'wake_command_received', 'text': text})

    def _submit_wake_command(self, text: str):
        if self.current_state in self.BUSY_STATES or (self.worker and self.worker.isRunning()):
            self.add_activity('Wake command ignored while LEVI is busy')
            return
        self.input_field.setText(text)
        self.send_command()

    # ───────────────────────────────────────────────────────────
    #  TIMERS & TELEMETRY
    # ───────────────────────────────────────────────────────────
    def _setup_timers(self):
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)
        self._update_clock()

        self.telemetry_timer = QTimer(self)
        self.telemetry_timer.timeout.connect(self._update_telemetry)
        self.telemetry_timer.start(500)
        self._update_telemetry()

        # A short GUI heartbeat keeps the core, metrics, and pipeline visibly alive
        # even when the backend does not emit granular progress events.
        self.processing_timer = QTimer(self)
        self.processing_timer.timeout.connect(self._refresh_live_task)
        self.processing_timer.start(120)
        self._refresh_live_task()

        self.wake_status_timer = QTimer(self)
        self.wake_status_timer.timeout.connect(self._refresh_wake_status)
        self.wake_status_timer.start(500)
        self._refresh_wake_status()

        self.external_event_signal.connect(self._on_external_event)
        self._connect_event_bus()

    def _connect_event_bus(self):
        """Attach to common event-bus APIs when the host application provides one.

        The older UI imported event_bus but never subscribed to it. This adapter is
        intentionally optional: if the project exposes no supported subscription
        method, the normal timer and worker-driven UI continues to work unchanged.
        """
        callback = self._receive_external_event
        for method_name in ("subscribe", "on", "register", "add_listener"):
            subscriber = getattr(event_bus, method_name, None)
            if not callable(subscriber):
                continue
            attempts = ((callback,), ("ui", callback), ("progress", callback), ("agent", callback))
            for args in attempts:
                try:
                    self._event_bus_binding = subscriber(*args)
                    return
                except (TypeError, AttributeError):
                    continue
                except Exception:
                    return

    def _receive_external_event(self, *args, **kwargs):
        """Normalize an event-bus callback, including (name, payload) callbacks."""
        if kwargs:
            payload = dict(kwargs)
        elif len(args) == 1:
            payload = args[0]
        elif len(args) >= 2:
            payload = {"event": args[0], "data": args[-1]}
        else:
            payload = None
        self.external_event_signal.emit(payload)

    def _on_external_event(self, payload):
        """Apply optional backend progress and wake events on the Qt GUI thread."""
        if not isinstance(payload, dict):
            return
        event_type = payload.get("type") or payload.get("event")
        data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
        if event_type == "wake_command_received":
            text = str(data.get("text", "")).strip()
            if text:
                self._submit_wake_command(text)
            return
        if event_type == "wake_detected":
            self.add_activity("Wake phrase detected")
        elif event_type == "wake_transcription_started":
            self.add_activity("Listening for command")
        elif event_type == "wake_error":
            self.add_activity("Wake listener error")
        elif event_type == "voice_interrupted":
            self.add_activity("Speech interrupted by microphone input")
        state = data.get("state") or data.get("status") or data.get("phase")
        if isinstance(state, str):
            normalized = state.upper().replace(" ", "_")
            aliases = {"REASONING": "PLANNING", "DONE": "COMPLETED", "ERROR": "FAILED", "PAUSED": "WAITING_CONFIRMATION"}
            self.update_state(aliases.get(normalized, normalized))

        message = data.get("message") or data.get("text") or data.get("log")
        if message:
            self.log(str(message))
            self.add_activity(str(message))

        progress = data.get("progress") if isinstance(data.get("progress"), dict) else data
        if isinstance(progress, dict):
            self._last_metric_event = time.monotonic()
            self._set_live_metrics(
                tokens=progress.get("tokens_per_sec", progress.get("tokens")),
                context=progress.get("context_window", progress.get("context")),
                steps=progress.get("reasoning_steps", progress.get("steps")),
                depth=progress.get("thinking_depth", progress.get("depth")),
            )

    def _set_live_metrics(self, tokens=None, context=None, steps=None, depth=None):
        """Update all four reference metric cards and the context header together."""
        if tokens is not None:
            try:
                self._metric_tokens = max(0, int(float(str(tokens).replace(',', '').split('/')[0].strip())))
            except (TypeError, ValueError):
                pass

        if isinstance(context, dict):
            used = context.get("used", context.get("current", context.get("used_k")))
            limit = context.get("limit", context.get("max", context.get("limit_k")))
            try:
                if used is not None:
                    self._context_used_k = max(0, int(float(str(used).replace('K', '').strip())))
                if limit is not None:
                    self._context_limit_k = max(1, int(float(str(limit).replace('K', '').strip())))
            except (TypeError, ValueError):
                pass
        elif isinstance(context, str) and context.strip():
            cleaned = context.strip().upper().replace(' ', '')
            if '/' in cleaned:
                left, right = cleaned.split('/', 1)
                try:
                    self._context_used_k = int(float(left.replace('K', '')))
                    self._context_limit_k = int(float(right.replace('K', '')))
                except ValueError:
                    pass

        if steps is not None:
            if isinstance(steps, str) and '/' in steps:
                try:
                    steps = steps.split('/', 1)[0].strip()
                except Exception:
                    pass
            try:
                self._metric_steps = max(0, min(6, int(float(str(steps).replace(',', '').strip()))))
            except (TypeError, ValueError):
                pass
        if depth is not None and str(depth).strip():
            self._metric_depth = str(depth).strip().title()

        if self.stat_token_value is not None:
            self.stat_token_value.setText(f"{self._metric_tokens:,}")
        if self.stat_context_value is not None:
            self.stat_context_value.setText(f"{self._context_used_k}K / {self._context_limit_k}K")
        if self.context_token_tag is not None:
            self.context_token_tag.setText(f"{self._context_used_k}K / {self._context_limit_k}K")
        if self.stat_steps_value is not None:
            self.stat_steps_value.setText(f"{self._metric_steps} / 6")
        if self.stat_depth_value is not None:
            self.stat_depth_value.setText(self._metric_depth)

    def _refresh_live_task(self):
        """Refresh task metrics and phase feedback without blocking the GUI thread."""
        if self.current_state not in self.BUSY_STATES or self._active_task_started is None:
            return

        elapsed = max(0.0, time.monotonic() - self._active_task_started)
        phase_index = {
            "RECEIVING": 0,
            "PLANNING": 1,
            "EXECUTING": 2,
            "VALIDATING": 3,
            "WAITING_CONFIRMATION": 2,
        }.get(self.current_state, 0)
        if self.current_state != self._last_live_phase:
            self._last_live_phase = self.current_state
            self.add_activity(f"Live phase: {self.current_state.replace('_', ' ')}")

        # Use a smooth local fallback only when the backend has not sent a recent
        # progress event. Backend-provided values remain authoritative.
        if time.monotonic() - self._last_metric_event > 0.9:
            pulse = int(1850 + ((elapsed * 265) % 980))
            stage_steps = {"RECEIVING": 0, "PLANNING": 1, "EXECUTING": 3, "WAITING_CONFIRMATION": 3, "VALIDATING": 5}
            visible_step = min(6, stage_steps.get(self.current_state, phase_index) + int(elapsed // 5))
            depth_map = {"RECEIVING": "Listening", "PLANNING": "High", "EXECUTING": "Deep", "WAITING_CONFIRMATION": "Paused", "VALIDATING": "High"}
            used_context = min(self._context_limit_k, 24 + int(elapsed * 0.85))
            self._set_live_metrics(tokens=pulse, context={"used": used_context, "limit": self._context_limit_k}, steps=visible_step, depth=depth_map.get(self.current_state, "High"))

    def _promote_to_executing(self, token):
        if token == self._active_task_generation and self.current_state == "RECEIVING" and self.worker and self.worker.isRunning():
            self.update_state("EXECUTING")

    def _on_worker_thread_finished(self, token, worker):
        if token != self._active_task_generation or worker is not self.worker:
            return
        worker.deleteLater()
        self.worker = None

    def _schedule_idle(self, delay_ms: int, token: int):
        QTimer.singleShot(delay_ms, lambda token=token: self._reset_to_idle(token))

    def _reset_to_idle(self, token: int):
        if token != self._active_task_generation:
            return
        if self.current_state in {"COMPLETED", "FAILED"}:
            self.update_state("IDLE")

    def _update_clock(self):
        now = datetime.datetime.now()
        self.clock_lbl.setText(now.strftime("%H:%M:%S"))
        self.date_lbl.setText(now.strftime("%a, %d %b %Y").upper())
        elapsed = int(time.time() - self.start_time)
        h, m, s = elapsed // 3600, (elapsed % 3600) // 60, elapsed % 60
        self.uptime_val.setText(f"{h:02d}:{m:02d}:{s:02d}")

    def _update_telemetry(self):
        try:
            if psutil is None:
                raise RuntimeError('psutil unavailable')
            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory()
            self.cpu_val.setText(f"{cpu:.0f}%")
            self.ram_val.setText(f"{ram.used / (1024**3):.1f} GB")
        except Exception:
            pass

        try:
            from voice import get_voice_state, VoiceState
            v_state = get_voice_state()
            if v_state == VoiceState.SPEAKING:
                self.voice_lbl.setText("VOICE   Speaking ●")
                self.voice_lbl.setStyleSheet("color: #38bdf8; font-size: 9px; font-weight: bold; border: none; background: transparent;")
            elif v_state == VoiceState.PREPARING:
                self.voice_lbl.setText("VOICE   Preparing...")
                self.voice_lbl.setStyleSheet("color: #c084fc; font-size: 9px; border: none; background: transparent;")
            else:
                self.voice_lbl.setText("VOICE   Native")
                self.voice_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 9px; border: none; background: transparent;")
        except Exception:
            pass

    # ───────────────────────────────────────────────────────────
    #  HELPERS & LOGGING
    # ───────────────────────────────────────────────────────────
    def log(self, text: str):
        t = datetime.datetime.now().strftime("%H:%M:%S")
        self.console.append(f"[{t}] {text}")
        self.console.moveCursor(QTextCursor.MoveOperation.End)

    def add_activity(self, text: str):
        if not getattr(self, '_activity_has_entries', False):
            self.activity_list.clear()
            self._activity_has_entries = True
        t = datetime.datetime.now().strftime("%H:%M:%S")
        self.activity_list.append(f"<font color='{TEXT_MUTED}'>{t}</font>  {escape(str(text))}")
        self.activity_list.moveCursor(QTextCursor.MoveOperation.End)

    def _apply_state_visuals(self, new_state: str):
        """Keep all state indicators synchronized and visually distinct."""
        state_colors = {
            "IDLE": ACCENT_LAVENDER,
            "RECEIVING": ACCENT_CYAN,
            "PLANNING": ACCENT_PURPLE,
            "EXECUTING": ACCENT_LAVENDER,
            "WAITING_CONFIRMATION": ACCENT_AMBER,
            "VALIDATING": ACCENT_BLUE,
            "COMPLETED": ACCENT_GREEN,
            "FAILED": ACCENT_RED,
        }
        color = state_colors.get(new_state, ACCENT_LAVENDER)
        readable_state = new_state.replace("_", " ")
        display_state = 'Listening...' if new_state == 'IDLE' else readable_state.title()
        self.state_badge.setText(display_state)
        self.state_badge.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_MUTED if new_state == 'IDLE' else color};
                font-size: 10px;
                font-weight: 500;
                background: transparent;
                border: none;
                padding: 4px 12px;
            }}
        """)

        if new_state == "IDLE":
            conversation_text, core_text = "● READY", "● STANDBY"
        elif new_state == "WAITING_CONFIRMATION":
            conversation_text, core_text = "● APPROVAL", "● PAUSED"
        elif new_state == "FAILED":
            conversation_text, core_text = "● ATTENTION", "● ALERT"
        else:
            conversation_text, core_text = "● PROCESSING", "● ACTIVE"

        self.conv_status.setText(conversation_text)
        self.conv_status.setStyleSheet(
            f"color: {color}; font-size: 8.5px; font-weight: 800; "
            "border: none; background: transparent;"
        )
        self.core_status.setText(core_text)
        self.core_status.setStyleSheet(
            f"color: {color}; font-size: 8.5px; font-weight: 800; "
            "border: none; background: transparent;"
        )
        top_state = 'OPTIMAL' if new_state == 'IDLE' else ('PROCESSING' if new_state in self.BUSY_STATES else readable_state)
        self.status_badge.setText(f"● {top_state}")
        top_color = ACCENT_GREEN if new_state == 'IDLE' else color
        self.status_badge.setStyleSheet(f"""
            QLabel {{
                color: {top_color};
                font-size: 9.5px;
                font-weight: 800;
                background: {NEU_SUNKEN};
                border: 1px solid {color};
                border-radius: 10px;
                padding: 7px 14px;
            }}
        """)

        busy = new_state in self.BUSY_STATES
        if hasattr(self, "input_field"):
            self.input_field.setEnabled(not busy)
        if hasattr(self, "send_icon_btn"):
            self.send_icon_btn.setEnabled(not busy)
        if hasattr(self, "briefing_icon_btn"):
            self.briefing_icon_btn.setEnabled(not busy)
        if hasattr(self, "interrupt_icon_btn"):
            interrupt_visible = busy or bool(self.worker and self.worker.isRunning())
            self.interrupt_icon_btn.setEnabled(interrupt_visible)
            self.interrupt_icon_btn.setVisible(interrupt_visible)

    def _on_core_interaction(self, action: str):
        messages = {
            "focus_on": "Neural core focus lock enabled",
            "focus_off": "Neural core focus lock released",
            "paused": "Neural field animation paused",
            "resumed": "Neural field animation resumed",
            "surface": "Neural field surface selected",
            "band_1": "Fiber band 1 amplified",
            "band_2": "Fiber band 2 amplified",
            "band_3": "Fiber band 3 amplified",
            "orbit_1": "Fiber band 1 amplified",
            "orbit_2": "Fiber band 2 amplified",
            "orbit_3": "Fiber band 3 amplified",
        }
        message = messages.get(action, f"Core interaction: {action}")
        self.add_activity(message)
        self.log(message)
        if hasattr(self, "core_status"):
            self.core_status.setText("● FOCUS" if action == "focus_on" else "● ACTIVE")

    def update_state(self, new_state: str):
        previous_state = self.current_state
        self.current_state = new_state
        state_defaults = {
            "IDLE": (0, "High"), "RECEIVING": (0, "Listening"),
            "PLANNING": (1, "High"), "EXECUTING": (3, "Deep"),
            "WAITING_CONFIRMATION": (3, "Paused"), "VALIDATING": (5, "High"),
            "COMPLETED": (6, "High"), "FAILED": (0, "Alert"),
        }
        if new_state in state_defaults:
            default_steps, default_depth = state_defaults[new_state]
            self._set_live_metrics(steps=default_steps, depth=default_depth)
        if new_state in self.BUSY_STATES and self._active_task_started is None:
            self._active_task_started = time.monotonic()
        elif new_state == "IDLE":
            self._active_task_started = None
            self._last_live_phase = None
        if previous_state != new_state and hasattr(self, "activity_list"):
            self.add_activity(f"State changed: {new_state.replace('_', ' ')}")
        self.core_canvas.set_state(new_state)
        self._apply_state_visuals(new_state)

        state_map = {
            "RECEIVING": "RECEIVING", "PLANNING": "REASONING",
            "EXECUTING": "EXECUTING", "VALIDATING": "VALIDATING",
            "COMPLETED": "COMPLETED",
        }
        active_label = state_map.get(new_state, "")
        for label, widget in self.pipe_steps:
            is_active = (label == active_label)
            if is_active:
                widget.setStyleSheet(f"""
                    QFrame {{
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #7c3aed, stop:1 #4338ca);
                        border-top: 1px solid {ACCENT_LAVENDER};
                        border-left: 1px solid {ACCENT_LAVENDER};
                        border-right: 1px solid #1e1b4b;
                        border-bottom: 2px solid #1e1b4b;
                        border-radius: 10px;
                    }}
                """)
            else:
                widget.setStyleSheet(f"""
                    QFrame {{
                        background: {NEU_CARD};
                        border-top: 1px solid {NEU_SURFACE_HI};
                        border-left: 1px solid {NEU_SURFACE_HI};
                        border-right: 1px solid {NEU_SURFACE_LO};
                        border-bottom: 1px solid {NEU_SURFACE_LO};
                        border-radius: 10px;
                    }}
                """)

    # ───────────────────────────────────────────────────────────
    #  COMMAND DISPATCH & HANDLERS
    # ───────────────────────────────────────────────────────────
    def send_command(self):
        prompt = self.input_field.text().strip()
        if not prompt or self.current_state in self.BUSY_STATES:
            return
        if self.worker is not None and self.worker.isRunning():
            return

        self.input_field.clear()
        self._chat_visible = True
        self.chat_display.show()
        self._position_floating_widgets()
        safe_prompt = escape(prompt)
        t = datetime.datetime.now().strftime("%H:%M:%S")
        user_html = f"""
        <div style="margin-bottom:8px; padding:10px 12px; background:#141a2a; border-top:1px solid #222b44; border-left:1px solid #222b44; border-right:1px solid #06080e; border-bottom:1.5px solid #06080e; border-radius:10px;">
            <span style="color:#64748b; font-size:8.5px;">[{t}]</span>
            <span style="color:#c084fc; font-weight:bold; font-size:9.5px;">  You</span>
            <div style="color:#f1f5f9; margin-top:4px; font-size:10.5px;">{safe_prompt}</div>
        </div>
        """
        self.chat_display.append(user_html)
        self.chat_display.moveCursor(QTextCursor.MoveOperation.End)
        self.add_activity("User command dispatched")
        self.log(f"Received: '{prompt}'")

        self._task_generation += 1
        token = self._task_generation
        self._active_task_generation = token
        self._active_task_started = time.monotonic()
        self._interrupt_requested = False
        self.update_state("RECEIVING")

        self.worker = AgentWorker(prompt)
        self.worker.finished_signal.connect(lambda result, token=token: self.on_agent_finished(result, token))
        self.worker.error_signal.connect(lambda message, token=token: self.on_agent_error(message, token))
        self.worker.finished.connect(lambda token=token, worker=self.worker: self._on_worker_thread_finished(token, worker))
        self.worker.start()
        self.interrupt_icon_btn.setEnabled(True)

        # Let Qt paint the receiving state before moving into execution.
        QTimer.singleShot(120, lambda token=token: self._promote_to_executing(token))

    def on_agent_finished(self, result: dict, token=None):
        if token is not None and token != self._active_task_generation:
            return
        if self._interrupt_requested:
            self.log("Late agent result ignored after interrupt")
            return

        status = result.get("status") if isinstance(result, dict) else None
        pending_action = result.get("pending_action") if isinstance(result, dict) else None

        if status == "awaiting_confirmation" or pending_action:
            self.update_state("WAITING_CONFIRMATION")
            action_info = pending_action or {}
            action_id = action_info.get("action_id")
            action_type = action_info.get("action") or action_info.get("type", "Action")
            data_desc = action_info.get("command") or action_info.get("data", {})

            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("LEVI Security Checkpoint")
            msg_box.setText(f"LEVI Action Requires Confirmation:\n\nAction Type: {action_type}\nDetails: {data_desc}\n\nDo you grant permission to execute this system action?")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            approve_btn = msg_box.addButton("APPROVE [ENTER]", QMessageBox.ButtonRole.AcceptRole)
            msg_box.addButton("DENY [ESC]", QMessageBox.ButtonRole.RejectRole)
            msg_box.setStyleSheet(f"QMessageBox {{ background-color: {NEU_CARD}; color: #f1f5f9; font-family: 'Consolas'; border: 1px solid {NEU_SURFACE_HI}; border-radius: 12px; }} QLabel {{ color: #fbbf24; font-size: 11px; }} QPushButton {{ background-color: {NEU_SURFACE}; color: #c084fc; border: 1px solid {NEU_SURFACE_HI}; border-radius: 6px; padding: 6px 14px; }} QPushButton:hover {{ background-color: #7c3aed; color: #ffffff; }}")
            msg_box.exec()

            approved = msg_box.clickedButton() == approve_btn
            self._pending_action_type = action_type
            self._pending_action_approved = approved
            self.update_state("EXECUTING" if approved else "COMPLETED")
            self.pending_worker = PendingActionWorker(action_id, approved)
            self.pending_worker.finished_signal.connect(lambda res, token=token: self._on_pending_action_finished(res, token))
            self.pending_worker.error_signal.connect(lambda message, token=token: self._on_pending_action_error(message, token))
            self.pending_worker.start()
            return

        response_text = result.get("response", "Task completed.") if isinstance(result, dict) else str(result)
        safe_response = escape(str(response_text))
        t = datetime.datetime.now().strftime("%H:%M:%S")
        levi_html = f"""
        <div style="margin-bottom:8px; padding:10px 12px; background:#0e1628; border-top:1px solid #1e2e4e; border-left:1px solid #1e2e4e; border-right:1px solid #050912; border-bottom:1.5px solid #050912; border-radius:10px;">
            <span style="color:#64748b; font-size:8.5px;">[{t}]</span>
            <span style="color:#38bdf8; font-weight:bold; font-size:9.5px;">  LEVI</span>
            <div style="color:#e2e8f0; margin-top:4px; font-size:10.5px;">{safe_response}</div>
        </div>
        """
        self.chat_display.append(levi_html)
        self.chat_display.moveCursor(QTextCursor.MoveOperation.End)
        self.add_activity("Task finished successfully")
        self.log("Task completed")
        self.update_state("COMPLETED")
        self._schedule_idle(2500, self._active_task_generation)

    def _on_pending_action_finished(self, result: dict, token=None):
        if token is not None and token != self._active_task_generation:
            return
        response = result.get("message") or (f"Executed: {result.get('stdout') or result}" if self._pending_action_approved else "Action execution canceled.")
        safe_response = escape(str(response))
        t = datetime.datetime.now().strftime("%H:%M:%S")
        levi_html = f"""
        <div style="margin-bottom:8px; padding:10px 12px; background:#0e1628; border-top:1px solid #1e2e4e; border-left:1px solid #1e2e4e; border-right:1px solid #050912; border-bottom:1.5px solid #050912; border-radius:10px;">
            <span style="color:#64748b; font-size:8.5px;">[{t}]</span>
            <span style="color:#38bdf8; font-weight:bold; font-size:9.5px;">  LEVI</span>
            <div style="color:#e2e8f0; margin-top:4px; font-size:10.5px;">{safe_response}</div>
        </div>
        """
        self.chat_display.append(levi_html)
        self.chat_display.moveCursor(QTextCursor.MoveOperation.End)
        self.add_activity("Action approved" if self._pending_action_approved else "Action denied")
        self.update_state("COMPLETED")
        if self.pending_worker:
            self.pending_worker.deleteLater()
            self.pending_worker = None
        self._schedule_idle(1800, self._active_task_generation)

    def _on_pending_action_error(self, message: str, token=None):
        if token is not None and token != self._active_task_generation:
            return
        self.on_agent_error(message, token)
        if self.pending_worker:
            self.pending_worker.deleteLater()
            self.pending_worker = None

    def on_agent_error(self, err_msg: str, token=None):
        if token is not None and token != self._active_task_generation:
            return
        t = datetime.datetime.now().strftime("%H:%M:%S")
        safe_error = escape(str(err_msg))
        err_html = f"""
        <div style="margin-bottom:8px; padding:10px 12px; background:#241218; border-top:1px solid #4c1d28; border-left:1px solid #4c1d28; border-right:1px solid #0c0406; border-bottom:1.5px solid #0c0406; border-radius:10px;">
            <span style="color:#f43f5e; font-weight:bold; font-size:9.5px;">[{t}] LEVI ERROR</span>
            <div style="color:#fda4af; margin-top:4px; font-size:10px;">{safe_error}</div>
        </div>
        """
        self.chat_display.append(err_html)
        self.chat_display.moveCursor(QTextCursor.MoveOperation.End)
        self.add_activity("Error encountered")
        self.log(f"ERROR: {err_msg}")
        self.update_state("FAILED")
        self._schedule_idle(3000, self._active_task_generation)

    def on_interrupt_clicked(self):
        if self.current_state not in self.BUSY_STATES and not (self.worker and self.worker.isRunning()):
            return
        self._interrupt_requested = True
        trigger_interrupt()
        self.log("INTERRUPT triggered by user.")
        self.add_activity("Execution interrupted")
        t = datetime.datetime.now().strftime("%H:%M:%S")
        int_html = f"""
        <div style="margin-bottom:6px; padding:8px 10px; background:#200c14; border-top:1px solid #3c1420; border-left:1px solid #3c1420; border-right:1px solid #0a0306; border-bottom:1.5px solid #0a0306; border-radius:8px;">
            <span style="color:#f43f5e; font-weight:bold; font-size:9px;">[{t}] SYSTEM</span>
            <span style="color:#fda4af; font-size:9.5px;">  Action execution interrupted by user.</span>
        </div>
        """
        self.chat_display.append(int_html)
        self.chat_display.moveCursor(QTextCursor.MoveOperation.End)
        self.update_state("FAILED")
        self._schedule_idle(2000, self._active_task_generation)

    def trigger_two_phase_briefing(self):
        if self.current_state in self.BUSY_STATES or (self.b_worker and self.b_worker.isRunning()):
            return
        import asyncio
        from services.two_phase_briefing import run_two_phase_briefing

        self._task_generation += 1
        token = self._task_generation
        self._active_task_generation = token
        self._active_task_started = time.monotonic()
        self._interrupt_requested = False
        self.update_state("PLANNING")
        self.add_activity("Two-phase briefing started")
        self.log("Launching Two-Phase Morning Briefing...")

        class BriefingWorker(QThread):
            done_signal = pyqtSignal(dict)
            error_signal = pyqtSignal(str)
            def run(self):
                try:
                    res = asyncio.run(run_two_phase_briefing())
                    self.done_signal.emit(res if isinstance(res, dict) else {"phase1": str(res)})
                except Exception as exc:
                    self.error_signal.emit(str(exc))

        self.b_worker = BriefingWorker()
        self.b_worker.done_signal.connect(lambda res, token=token: self.on_briefing_finished(res, token))
        self.b_worker.error_signal.connect(lambda message, token=token: self.on_agent_error(message, token))
        self.b_worker.finished.connect(self.b_worker.deleteLater)
        self.b_worker.start()
        self.interrupt_icon_btn.setEnabled(True)

    def closeEvent(self, event):
        try:
            from voice.wake_listener import wake_listener
            wake_listener.on_command = None
            wake_listener.stop()
        except Exception:
            pass
        try:
            if self.worker and self.worker.isRunning():
                trigger_interrupt()
            if self.b_worker and self.b_worker.isRunning():
                self.b_worker.requestInterruption()
        except Exception:
            pass
        super().closeEvent(event)

    def on_briefing_finished(self, res: dict, token=None):
        if token is not None and token != self._active_task_generation:
            return
        p1 = escape(str(res.get("phase1", "")))
        p2 = escape(str(res.get("phase2", "")))
        t = datetime.datetime.now().strftime("%H:%M:%S")
        b_html = f"""
        <div style="margin-bottom:8px; padding:10px 12px; background:#0c1828; border-top:1px solid #182e4e; border-left:1px solid #182e4e; border-right:1px solid #040810; border-bottom:1.5px solid #040810; border-radius:10px;">
            <div style="color:#38bdf8; font-weight:bold; font-size:9.5px;">[{t}]  BRIEFING (Phase 1)</div>
            <div style="color:#e2e8f0; margin-top:3px;">{p1}</div>
            <div style="color:#38bdf8; font-weight:bold; font-size:9.5px; margin-top:6px;">[{t}]  BRIEFING (Phase 2)</div>
            <div style="color:#e2e8f0; margin-top:3px;">{p2}</div>
        </div>
        """
        self.chat_display.append(b_html)
        self.chat_display.moveCursor(QTextCursor.MoveOperation.End)
        self.add_activity("Two-phase briefing complete")
        self.update_state("COMPLETED")
        self._schedule_idle(2500, self._active_task_generation)
        if self.b_worker:
            self.b_worker = None


# ═══════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("LEVI OS")
    window = LEVIHUDWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
