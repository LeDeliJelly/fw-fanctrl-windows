# -*- coding: utf-8 -*-
import sys
import threading
from time import sleep
import json
import clr
import subprocess
import os
import tempfile

from PIL import Image
import pystray

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

LAST_STRATEGY_FILE = "last_strategy.txt"
CONFIG_FILE_PATH = resource_path("config.json")
ECTOOL_PATH = resource_path("ectool.exe")
DLL_PATH = resource_path("LibreHardwareMonitorLib.dll")
ICON_PATH = resource_path("icon.png")

try:
    clr.AddReference(DLL_PATH)
    from LibreHardwareMonitor.Hardware import Computer, HardwareType, SensorType
except Exception as e:
    print(f"Fatal Error: Could not load LibreHardwareMonitorLib.dll. Error: {e}")
    sys.exit(1)

class SharedState:
    def __init__(self):
        self.lock = threading.Lock()
        self.temperature = 0
        self.fan_speed = 0
        self.current_strategy = ""
        self.strategies = []
        self.command = None
        self.running = True
        self.active = True

class FanController:
    def __init__(self, configPath, shared_state):
        self.state = shared_state
        self.handle = Computer()
        self.handle.IsCpuEnabled = True
        self.handle.Open()
        self.fan_speed = 0
        with open(configPath, "r") as fp:
            self.config = json.load(fp)
        
        self.default_strategy_name = self.config["defaultStrategy"]
        
        with self.state.lock:
            self.state.strategies = list(self.config["strategies"].keys())

        try:
            with open(LAST_STRATEGY_FILE, "r") as f:
                strategy_name = f.read().strip()
                if strategy_name not in self.config["strategies"] and strategy_name != "Automatic":
                    strategy_name = self.default_strategy_name
        except FileNotFoundError:
            strategy_name = self.default_strategy_name
        
        if strategy_name == "Automatic":
            self.state.active = False
            self.state.current_strategy = "Automatic"
            subprocess.run(f'"{ECTOOL_PATH}" autofanctrl', stdout=subprocess.PIPE, shell=True)
        else:
            self.setStrategy(self.config["strategies"][strategy_name], strategy_name)

    def setStrategy(self, strategy_obj, strategy_name):
        self.speedCurve = strategy_obj["speedCurve"]
        self.fanSpeedUpdateFrequency = strategy_obj["fanSpeedUpdateFrequency"]
        self.movingAverageInterval = strategy_obj["movingAverageInterval"]
        self.temps = [40.0] * 100
        self._tempIndex = 0
        with self.state.lock:
            self.state.current_strategy = strategy_name
            self.state.active = True

    def updateTemperature(self):
        core_temps = []
        for hardware in self.handle.Hardware:
            if hardware.HardwareType == HardwareType.Cpu:
                hardware.Update()
                for sensor in hardware.Sensors:
                    if sensor.SensorType == SensorType.Temperature and sensor.Value is not None:
                        core_temps.append(sensor.Value)
                break
        measurement = sum(core_temps) / len(core_temps) if core_temps else (self.temps[self._tempIndex - 1] if self._tempIndex > 0 else 40.0)
        self._tempIndex = (self._tempIndex + 1) % len(self.temps)
        self.temps[self._tempIndex] = measurement
        with self.state.lock:
            self.state.temperature = measurement

    def getMovingAverageTemperature(self):
        if self.movingAverageInterval <= 0: return self.temps[self._tempIndex]
        if self._tempIndex < self.movingAverageInterval:
             temps_slice = self.temps[:self._tempIndex+1]
        else:
             temps_slice = self.temps[self._tempIndex - self.movingAverageInterval + 1 : self._tempIndex+1]
        return sum(temps_slice) / len(temps_slice) if temps_slice else 0

    def setSpeed(self, speed):
        with self.state.lock:
            self.state.fan_speed = speed
        subprocess.run(f'"{ECTOOL_PATH}" fanduty {speed}', stdout=subprocess.PIPE, shell=True)

    def adaptSpeed(self):
        currentTemp = self.getMovingAverageTemperature()
        minPoint, maxPoint = self.speedCurve[0], self.speedCurve[-1]
        for e in self.speedCurve:
            if currentTemp > e["temp"]: minPoint = e
            else: maxPoint = e; break
        if minPoint == maxPoint or maxPoint["temp"] == minPoint["temp"]:
            newSpeed = minPoint["speed"]
        else:
            slope = (maxPoint["speed"] - minPoint["speed"]) / (maxPoint["temp"] - minPoint["temp"])
            newSpeed = int(minPoint["speed"] + (currentTemp - minPoint["temp"]) * slope)
        self.setSpeed(newSpeed)

    def handle_command(self, command):
        if command == "Automatic":
            with self.state.lock:
                self.state.active = False
            print("Reverting to automatic fan control...")
            subprocess.run(f'"{ECTOOL_PATH}" autofanctrl', stdout=subprocess.PIPE, shell=True)
        elif command in self.config["strategies"]:
            self.setStrategy(self.config["strategies"][command], command)
        
        with open(LAST_STRATEGY_FILE, "w") as f:
            f.write(self.state.current_strategy)

    def run(self):
        while self.state.running:
            with self.state.lock:
                command = self.state.command
                self.state.command = None

            if command:
                self.handle_command(command)
                continue
            
            with self.state.lock:
                is_active = self.state.active

            if is_active:
                self.updateTemperature()
                if self._tempIndex % self.fanSpeedUpdateFrequency == 0:
                    self.adaptSpeed()
            
            sleep(1)
        self.handle.Close()
        print("Backend thread has finished.")

def create_tray_icon(state):
    try:
        image = Image.open(ICON_PATH)
    except FileNotFoundError:
        print(f"Fatal Error: {ICON_PATH} not found.")
        state.running = False
        return

    def on_strategy_clicked(icon, item):
        strategy_name = str(item)
        if strategy_name == "Automatic (Built-in)":
            internal_name = "Automatic"
        else:
            internal_name = strategy_name

        with state.lock:
            state.command = internal_name
            state.current_strategy = internal_name
        
        print(f"Command set to: {internal_name}")
        icon.update_menu()

    def on_exit_clicked(icon, item):
        print("Exit command received. Shutting down gracefully...")
        with state.lock:
            state.running = False
        
        sleep(1.2) 
        
        print("Reverting to automatic fan control...")
        subprocess.run(f'"{ECTOOL_PATH}" autofanctrl', stdout=subprocess.PIPE, shell=True)
        
        icon.stop()

    def get_menu_items():
        with state.lock:
            current = state.current_strategy
            strategies = state.strategies
        
        yield pystray.MenuItem(
            "Automatic (Built-in)",
            on_strategy_clicked,
            checked=lambda item: current == "Automatic",
            radio=True
        )
        yield pystray.Menu.SEPARATOR

        for name in strategies:
            yield pystray.MenuItem(
                name,
                on_strategy_clicked,
                checked=lambda item, name=name: current == name,
                radio=True
            )
        
        yield pystray.Menu.SEPARATOR
        yield pystray.MenuItem("Exit", on_exit_clicked)

    def update_title_thread(icon):
        while state.running:
            with state.lock:
                temp = state.temperature
                speed = state.fan_speed
                is_active = state.active
            
            if is_active:
                icon.title = f"Temp: {temp:.1f}°C | Fan: {speed}%"
            else:
                icon.title = "Fan Control: Automatic"
            sleep(2)

    icon = pystray.Icon("fw-fanctrl", image, "Framework Fan Control", menu=pystray.Menu(get_menu_items))
    
    title_updater = threading.Thread(target=update_title_thread, args=(icon,), daemon=True)
    
    def setup(icon):
        icon.visible = True
        title_updater.start()

    icon.run(setup=setup)


if __name__ == "__main__":
    try:
        lock_file_path = os.path.join(tempfile.gettempdir(), "fw-fanctrl.lock")
        lock_file = open(lock_file_path, "w")
        lock_file.write(str(os.getpid()))
        lock_file.flush()
    except IOError:
        print("Another instance of Framework Fan Control is already running.")
        sys.exit(1)

    shared_state = SharedState()
    try:
        fan_controller = FanController(configPath=CONFIG_FILE_PATH, shared_state=shared_state)
        backend_thread = threading.Thread(target=fan_controller.run, daemon=True)
        backend_thread.start()
    except Exception as e:
        print(f"Fatal Error on startup: {e}")
        sys.exit(1)

    print("Starting tray application... Right-click the icon in your system tray to control.")
    create_tray_icon(shared_state)
    print("Exiting application.")