import sys
import time
import threading
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                             QLabel, QSpinBox, QMessageBox, QHBoxLayout, QDialog)
from PyQt6.QtCore import (pyqtSignal, QObject, Qt, QThread, pyqtSlot, QEvent, 
                          QTimer, QMetaObject, Q_ARG)
from pynput import mouse, keyboard
import Quartz
from AppKit import (NSEvent, NSKeyDownMask, NSCommandKeyMask, NSAlternateKeyMask, 
                    NSControlKeyMask, NSShiftKeyMask)

# --- Quartz Helper Functions (Unchanged) ---
def quartz_move(x, y):
    move_event = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventMouseMoved, (int(x), int(y)), 0
    )
    Quartz.CGEventPost(Quartz.kCGSessionEventTap, move_event)

def quartz_click(x, y, button='left', pressed=True):
    btn_map = {
        'left': (Quartz.kCGEventLeftMouseDown, Quartz.kCGEventLeftMouseUp, Quartz.kCGMouseButtonLeft),
        'right': (Quartz.kCGEventRightMouseDown, Quartz.kCGEventRightMouseUp, Quartz.kCGMouseButtonRight),
        'middle': (Quartz.kCGEventOtherMouseDown, Quartz.kCGEventOtherMouseUp, Quartz.kCGMouseButtonCenter)
    }
    
    if button not in btn_map:
        button = 'left'
        
    down_type, up_type, btn_code = btn_map[button]
    event_type = down_type if pressed else up_type
    
    event = Quartz.CGEventCreateMouseEvent(
        None, event_type, (int(x), int(y)), btn_code
    )
    Quartz.CGEventPost(Quartz.kCGSessionEventTap, event)

def quartz_scroll(dx, dy):
    scroll_event = Quartz.CGEventCreateScrollWheelEvent(
        None, Quartz.kCGScrollEventUnitLine, 2, int(dy), int(dx)
    )
    Quartz.CGEventPost(Quartz.kCGSessionEventTap, scroll_event)

# --- Logic Classes ---

class MouseRecorder:
    def __init__(self):
        self.events = []
        self.start_time = 0
        self.listener = None
        self.recording = False

    def start(self):
        self.events = []
        self.start_time = time.time()
        self.recording = True
        print("Starting recording...")
        self.listener = mouse.Listener(
            on_move=self.on_move,
            on_click=self.on_click,
            on_scroll=self.on_scroll
        )
        self.listener.start()

    def stop(self):
        self.recording = False
        if self.listener:
            self.listener.stop()
            self.listener = None
        print(f"Stopped recording. Total events: {len(self.events)}")

    def on_move(self, x, y):
        if self.recording:
            self.events.append(('move', time.time() - self.start_time, x, y))

    def on_click(self, x, y, button, pressed):
        if self.recording:
            btn_str = str(button).replace('Button.', '')
            self.events.append(('click', time.time() - self.start_time, x, y, btn_str, pressed))

    def on_scroll(self, x, y, dx, dy):
        if self.recording:
            self.events.append(('scroll', time.time() - self.start_time, x, y, dx, dy))

class MousePlayer(QThread):
    finished_signal = pyqtSignal()
    status_signal = pyqtSignal(str)

    def __init__(self, events, repetitions):
        super().__init__()
        self.events = events
        self.repetitions = repetitions
        self.running = False

    def run(self):
        self.running = True
        self.status_signal.emit("Status: Running...")
        
        try:
            for i in range(self.repetitions):
                if not self.running:
                    break
                
                self.status_signal.emit(f"Status: Running iteration {i+1}/{self.repetitions}")
                start_time = time.time()
                
                for event in self.events:
                    if not self.running:
                        break
                    
                    action, delay, *args = event
                    
                    target_time = start_time + delay
                    current_time = time.time()
                    wait_time = target_time - current_time
                    
                    if wait_time > 0:
                        time.sleep(wait_time)
                    
                    if action == 'move':
                        x, y = args
                        quartz_move(x, y)
                    elif action == 'click':
                        x, y, button, pressed = args
                        quartz_click(x, y, button, pressed)
                    elif action == 'scroll':
                        x, y, dx, dy = args
                        quartz_scroll(dx, dy)
                
                time.sleep(0.5)

        except Exception as e:
            self.status_signal.emit(f"Error: {str(e)}")
            print(f"Playback Error: {e}")
        
        self.running = False
        self.finished_signal.emit()

    def stop(self):
        self.running = False

# --- Hotkey Management ---

class HotkeyListener:
    def __init__(self, hotkey_str, target_widget):
        self.hotkey_str = hotkey_str
        self.target = target_widget
        self.global_monitor = None
        self.local_monitor = None
        
        self.cmd_needed = False
        self.alt_needed = False
        self.ctrl_needed = False
        self.shift_needed = False
        self.char_needed = None
        
        self.parse_hotkey()
        self.start_listener()

    def parse_hotkey(self):
        parts = self.hotkey_str.split('+')
        self.cmd_needed = '<cmd>' in parts
        self.alt_needed = '<alt>' in parts
        self.ctrl_needed = '<ctrl>' in parts
        self.shift_needed = '<shift>' in parts
        
        self.char_needed = None
        for p in parts:
            if not p.startswith('<') and not p.endswith('>'):
                self.char_needed = p.lower()
                break

    def matches(self, event):
        flags = event.modifierFlags()
        
        has_cmd = bool(flags & NSCommandKeyMask)
        has_alt = bool(flags & NSAlternateKeyMask)
        has_ctrl = bool(flags & NSControlKeyMask)
        has_shift = bool(flags & NSShiftKeyMask)
        
        if has_cmd != self.cmd_needed: return False
        if has_alt != self.alt_needed: return False
        if has_ctrl != self.ctrl_needed: return False
        if has_shift != self.shift_needed: return False
        
        chars = event.charactersIgnoringModifiers()
        if not chars: return False
        if chars.lower() != self.char_needed: return False
        
        return True

    def on_event(self, event):
        if self.matches(event):
            print("Native Hotkey Triggered!")
            QMetaObject.invokeMethod(self.target, "stop_all_safe", Qt.ConnectionType.QueuedConnection)

    def start_listener(self):
        self.stop_listener()
        try:
            # Global monitor
            self.global_monitor = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
                NSKeyDownMask, self.on_event
            )
            
            # Local monitor
            def local_handler(event):
                if self.matches(event):
                    print("Native Hotkey Triggered (Local)!")
                    QMetaObject.invokeMethod(self.target, "stop_all_safe", Qt.ConnectionType.QueuedConnection)
                    return event
                return event
                
            self.local_monitor = NSEvent.addLocalMonitorForEventsMatchingMask_handler_(
                NSKeyDownMask, local_handler
            )
            print(f"Native listener started for: {self.hotkey_str}")
        except Exception as e:
            print(f"Failed to bind native hotkey: {e}")

    def stop_listener(self):
        if self.global_monitor:
            NSEvent.removeMonitor_(self.global_monitor)
            self.global_monitor = None
        if self.local_monitor:
            NSEvent.removeMonitor_(self.local_monitor)
            self.local_monitor = None

    def update_hotkey(self, new_hotkey):
        self.hotkey_str = new_hotkey
        self.parse_hotkey()
        self.start_listener()

class HotkeyRecorderDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Set Hotkey")
        self.setFixedSize(300, 150)
        self.layout = QVBoxLayout()
        
        self.lbl_instruction = QLabel("Press the desired key combination...")
        self.lbl_instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.lbl_instruction)
        
        self.lbl_current = QLabel("")
        self.lbl_current.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.lbl_current.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.lbl_current)
        
        self.btn_save = QPushButton("Save")
        self.btn_save.clicked.connect(self.accept)
        self.btn_save.setEnabled(False)
        self.layout.addWidget(self.btn_save)
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        self.layout.addWidget(self.btn_cancel)
        
        self.setLayout(self.layout)
        
        self.current_keys = set()
        self.detected_hotkey = None
        self.listener = None

    def showEvent(self, event):
        self.start_listening()
        super().showEvent(event)

    def closeEvent(self, event):
        self.stop_listening()
        super().closeEvent(event)

    def start_listening(self):
        self.current_keys = set()
        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener.start()

    def stop_listening(self):
        if self.listener:
            self.listener.stop()
            self.listener = None

    def get_key_name(self, key):
        if hasattr(key, 'name'):
            # Special keys (cmd, alt, ctrl, etc.)
            return f"<{key.name}>"
        elif hasattr(key, 'char') and key.char:
            # Character keys
            return key.char.lower()
        else:
            return str(key)

    def on_press(self, key):
        key_name = self.get_key_name(key)
        self.current_keys.add(key_name)
        
        # Build hotkey string for display
        # Order: cmd, ctrl, alt, shift, others
        sorted_keys = []
        if '<cmd>' in self.current_keys: sorted_keys.append('<cmd>')
        if '<ctrl>' in self.current_keys: sorted_keys.append('<ctrl>')
        if '<alt>' in self.current_keys: sorted_keys.append('<alt>')
        if '<shift>' in self.current_keys: sorted_keys.append('<shift>')
        
        for k in self.current_keys:
            if k not in ['<cmd>', '<ctrl>', '<alt>', '<shift>']:
                sorted_keys.append(k)
        
        hotkey_str = '+'.join(sorted_keys)
        
        # Use invokeMethod to update UI safely
        QMetaObject.invokeMethod(self, "update_hotkey_label", 
                                 Qt.ConnectionType.QueuedConnection, 
                                 Q_ARG(str, hotkey_str))

    def on_release(self, key):
        if len(self.current_keys) > 0:
            QMetaObject.invokeMethod(self, "enable_save", Qt.ConnectionType.QueuedConnection)
        
        key_name = self.get_key_name(key)
        if key_name in self.current_keys:
            self.current_keys.remove(key_name)

    # Slots for thread-safe UI updates
    @pyqtSlot(str)
    def update_hotkey_label(self, text):
        self.lbl_current.setText(text)

    @pyqtSlot()
    def enable_save(self):
        self.detected_hotkey = self.lbl_current.text()
        self.btn_save.setEnabled(True)
        self.lbl_instruction.setText("Combination captured. Press Save.")

# --- Main App ---

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.recorder = MouseRecorder()
        self.player = None
        
        # Default Hotkey
        self.current_hotkey = '<cmd>+<alt>+t'
        
        self.initUI()
        
        # Start global hotkey listener
        # Pass self as target for invokeMethod
        self.hotkey_listener = HotkeyListener(self.current_hotkey, self)

    def initUI(self):
        self.setWindowTitle('Mouse Recorder')
        self.setGeometry(300, 300, 350, 320)
        
        # Check permissions on UI init (safe here)
        try:
            options = {Quartz.kAXTrustedCheckOptionPrompt: True}
            is_trusted = Quartz.AXIsProcessTrustedWithOptions(options)
        except:
            is_trusted = False

        layout = QVBoxLayout()
        
        if not is_trusted:
            perm_label = QLabel('⚠️ PERMISSION REQUIRED ⚠️')
            perm_label.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
            perm_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(perm_label)
            
            help_label = QLabel('Please allow "Accessibility" in System Settings')
            help_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(help_label)

        # Status
        self.status_label = QLabel('Status: Idle')
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Hotkey Configuration
        hk_layout = QHBoxLayout()
        self.lbl_hotkey = QLabel(f"Stop Hotkey: {self.current_hotkey}")
        hk_layout.addWidget(self.lbl_hotkey)
        
        self.btn_set_hotkey = QPushButton("Change")
        self.btn_set_hotkey.setFixedWidth(80)
        self.btn_set_hotkey.clicked.connect(self.change_hotkey)
        hk_layout.addWidget(self.btn_set_hotkey)
        layout.addLayout(hk_layout)

        # Controls
        self.btn_record = QPushButton('Start Recording')
        self.btn_record.clicked.connect(self.toggle_recording)
        self.btn_record.setMinimumHeight(40)
        layout.addWidget(self.btn_record)

        rep_layout = QHBoxLayout()
        rep_layout.addWidget(QLabel('Repetitions:'))
        self.spin_repeats = QSpinBox()
        self.spin_repeats.setRange(1, 9999)
        self.spin_repeats.setValue(1)
        rep_layout.addWidget(self.spin_repeats)
        layout.addLayout(rep_layout)

        self.btn_play = QPushButton('Play')
        self.btn_play.clicked.connect(self.start_playback)
        self.btn_play.setMinimumHeight(40)
        layout.addWidget(self.btn_play)

        # Test Button
        self.btn_test = QPushButton('Test Mouse (Quartz)')
        self.btn_test.clicked.connect(self.test_mouse)
        layout.addWidget(self.btn_test)

        self.setLayout(layout)

    def change_hotkey(self):
        # Stop current listener to avoid conflicts
        self.hotkey_listener.stop_listener()
        
        dialog = HotkeyRecorderDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.detected_hotkey:
            self.current_hotkey = dialog.detected_hotkey
            self.lbl_hotkey.setText(f"Stop Hotkey: {self.current_hotkey}")
            # Update and restart listener
            self.hotkey_listener.update_hotkey(self.current_hotkey)
        else:
            # If cancelled, just restart the old one
            self.hotkey_listener.start_listener()

    def toggle_recording(self):
        if not self.recorder.recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        self.status_label.setText('Status: Recording...')
        self.status_label.setStyleSheet("color: red; font-size: 14px; font-weight: bold;")
        self.btn_record.setText('Stop Recording')
        self.btn_play.setEnabled(False)
        self.recorder.start()

    def stop_recording(self):
        self.recorder.stop()
        count = len(self.recorder.events)
        self.status_label.setText(f'Status: Recorded {count} events')
        self.status_label.setStyleSheet("color: black; font-size: 14px; font-weight: bold;")
        self.btn_record.setText('Start Recording')
        self.btn_play.setEnabled(True)
        
        if count == 0:
            QMessageBox.warning(self, "No Events Recorded", 
                "0 events were captured.\n\n"
                "Please check Accessibility permissions.")

    def start_playback(self):
        if not self.recorder.events:
            QMessageBox.warning(self, "No Data", "Please record some actions first.")
            return

        repeats = self.spin_repeats.value()
        self.player = MousePlayer(self.recorder.events, repeats)
        self.player.status_signal.connect(self.update_status)
        self.player.finished_signal.connect(self.on_playback_finished)
        
        self.btn_record.setEnabled(False)
        self.btn_play.setEnabled(False)
        self.player.start()

    def on_playback_finished(self):
        self.btn_record.setEnabled(True)
        self.btn_play.setEnabled(True)
        if "Stopped" not in self.status_label.text():
            self.status_label.setText('Status: Finished')

    def update_status(self, text):
        self.status_label.setText(text)

    def test_mouse(self):
        try:
            self.status_label.setText("Testing Quartz Move...")
            quartz_move(200, 200)
            time.sleep(0.5)
            quartz_move(300, 300)
            QMessageBox.information(self, "Test Complete", "Attempted to move mouse. Did it work?")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Quartz failed: {str(e)}")

    @pyqtSlot()
    def stop_all_safe(self):
        # This slot is invoked from the background thread via QMetaObject.invokeMethod
        # It guarantees execution on the main thread.
        print("Stop All Triggered (Main Thread via invokeMethod)")
        
        if self.recorder.recording:
            self.stop_recording()
            self.status_label.setText("Status: Recording Stopped (Hotkey)")
        
        if self.player and self.player.isRunning():
            self.player.stop()
            # self.player.wait() # Avoid blocking
            self.status_label.setText("Status: Playback Stopped (Hotkey)")
            self.on_playback_finished()

    def closeEvent(self, event):
        if self.hotkey_listener:
            self.hotkey_listener.stop_listener()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())
