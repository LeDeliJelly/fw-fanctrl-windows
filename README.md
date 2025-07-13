# Framework Fan Control for Windows

This is a fully-featured Windows port and continuation of the original `fw-fanctrl` project, providing a simple and powerful way to manage your Framework Laptop's fan behavior. It runs as a clean, standalone tray application.

This fork fixes and modernizes the project after the original author stopped development.

![Application Screenshot](pic1.png)

## Features

*   **System Tray Control:** Runs silently in the system tray. Right-click the icon to get a full menu of fan modes.
*   **Customizable Fan Curves:** All fan strategies are defined in a simple `config.json` file. You can easily edit them or add your own, from completely silent to full performance.
*   **True Automatic Mode:** The "Automatic (Built-in)" option instantly and reliably hands fan control back to the laptop's default firmware.
*   **Remembers Your Last Setting:** The application saves your last used strategy (including "Automatic") and loads it the next time it starts.
*   **Safe by Design:** Automatically restores the default system fan control when the application is closed, ensuring your laptop is never left without proper thermal management.
*   **Standalone Application:** Packaged as a single `.exe` file that requires no installation of Python or any other dependencies.

## Compatibility

*   **Laptops:** Framework Laptop 13 and 16 (All variants, Intel and AMD)
*   **Operating System:** Windows 10 (64-bit) and Windows 11 (64-bit)

## Installation & Usage

1.  Go to the **Releases** page of this repository.
2.  Download the latest `Framework-Fan-Control.exe` from the "Assets" section.
3.  Place the `.exe` file in a permanent location on your computer (e.g., in a folder like `C:\Program Files\FrameworkFanControl`).
4.  Double-click the `.exe` to run it. Windows will ask for **Administrator permission**, which is required for the application to control the hardware fans.
5.  A new fan icon will appear in your system tray. **Right-click the icon** to select your desired fan mode. Please be patient, as it may take a few seconds for a new curve to apply.

### Running on Startup (Optional)

To make the fan controller start automatically when you log in:
1.  Press `Win + R` to open the Run dialog.
2.  Type `shell:startup` and press Enter. This will open your personal Startup folder.
3.  Create a shortcut to `Framework-Fan-Control.exe` and place it in this folder.

## Configuration

You can fully customize the fan behavior by editing the `config.json` file with a text editor.

*   `"defaultStrategy"`: The name of the fan curve that will be loaded by default when the application first runs.
*   `"strategies"`: A list of all available fan curves. You can edit the `speedCurve` points for any strategy or create entirely new ones. Each point maps a `temp` (in Celsius) to a fan `speed` (in percent).

## Future Plans

*   Improve the user interface.
*   Add support for creating and saving custom fan curves directly from the UI.
*   Include a built-in option to have the application launch on startup.

## Acknowledgements & Licensing

This project would not be possible without the foundational work of others.

*   This project is a continuation of the work started by **wzqvip**.
*   The original concept and fan logic is based on **[fw-fanctrl](https://github.com/TamtamHero/fw-fanctrl)** by **TamtamHero**.
*   Hardware communication is handled by **[ectool](https://github.com/DHowett/FrameworkWindowsUtils)** by **DHowett**.
*   Temperature sensing is provided by the **[LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor)** library, which is licensed under the Mozilla Public License 2.0.

This application is distributed under the **MIT License**.

## Disclaimer

This software modifies your laptop's fan control system. Use it at your own risk. While it is designed to be safe, the author is not responsible for any potential damage to your hardware.