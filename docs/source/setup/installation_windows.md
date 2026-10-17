# Pegasus Simulator — Windows 11 Installation & Usage Guide

This guide walks you through installing and running Pegasus Simulator on **Windows 11** with **Isaac Sim 6.2**.

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| OS | Windows 11 (64-bit) |
| GPU | NVIDIA GPU with RTX support (RTX 20xx/30xx/40xx recommended) |
| Driver | NVIDIA Driver 550.xx or later |
| Isaac Sim | 6.2.0 via Omniverse Launcher |
| PX4-Autopilot | For PX4 backend (optional) |
| ArduPilot | For ArduPilot backend (optional) |

---

## Step 1: Install Isaac Sim 6.2

1. Download **Omniverse Launcher** from [nvidia.com/omniverse](https://www.nvidia.com/en-us/omniverse/)
2. Install and sign in with your NVIDIA account
3. Navigate to the **Exchange** tab
4. Search for **Isaac Sim**
5. Install **Isaac Sim 6.2.0**

> The default install path is typically:
> ```
> C:\Users\<YourUser>\AppData\Local\ov\pkg\isaac_sim-6.2.0
> ```

---

## Step 2: Set Environment Variables

Open **PowerShell as Administrator** and run:

```powershell
# Set the Isaac Sim installation path
setx ISAAC_HOME "C:\Users\$env:USERNAME\AppData\Local\ov\pkg\isaac_sim-6.2.0"

# Verify
echo $env:ISAAC_HOME
```

> **Important:** You must open a new PowerShell/Command Prompt window after setting environment variables for them to take effect.

---

## Step 3: Install Python Dependencies

Open a new PowerShell window and run:

```powershell
# Navigate to the Pegasus Simulator directory
cd C:\path\to\PegasusSimulator

# Install Python dependencies using Isaac Sim's bundled Python
& "$env:ISAAC_HOME\python.bat" -m pip install numpy scipy pymavlink pyyaml toml
```

---

## Step 4: Install PX4-Autopilot (Optional)

If you want to use the **PX4 backend**:

```powershell
# Clone PX4-Autopilot
git clone https://github.com/PX4/PX4-Autopilot.git C:\PX4-Autopilot

# Set the PX4 path (add to your Pegasus config later)
setx PX4_HOME "C:\PX4-Autopilot"
```

For **ArduPilot**:
```powershell
git clone https://github.com/ArduPilot/ardupilot.git C:\ardupilot
```

---

## Step 5: Configure Pegasus Simulator

1. Navigate to the Pegasus Simulator directory:
   ```powershell
   cd C:\path\to\PegasusSimulator
   ```

2. Edit the configuration file:
   ```
   extensions\pegasus.simulator\pegasus\simulator\config\configs.yaml
   ```

3. Set your PX4/ArduPilot paths:
   ```yaml
   px4_dir: "C:/PX4-Autopilot"
   px4_default_airframe: "iris"
   ardupilot_dir: "C:/ardupilot"
   ardupilot_default_airframe: "gazebo-iris"
   global_coordinates:
     latitude: 38.7368
     longitude: -9.1379
     altitude: 0.0
   ```

---

## Step 6: Launch Pegasus Simulator

### Option A: Using the Batch Launcher (Recommended)

```powershell
cd C:\path\to\PegasusSimulator
.\run_simulation.bat
```

This will:
- Validate the Isaac Sim installation
- Register the Pegasus extension
- Launch Isaac Sim with the Pegasus Simulator UI

### Option B: Manual Launch

```powershell
# Navigate to Isaac Sim directory
cd $env:ISAAC_HOME

# Launch with Pegasus extension
.\kit\isaac-sim.bat --exts "pegasus.simulator" --no-window
```

---

## Step 7: Using the Simulator

### Loading a Vehicle

1. Open the **Pegasus Simulator** window from the Isaac Sim menu
2. Select a vehicle (e.g., Iris, Pegasus)
3. Choose a backend (PX4, ArduPilot, ROS2, or Python)
4. Click **Spawn**

### Loading an Environment

1. Open the **Environment** tab
2. Select an environment (e.g., "Box Room", "Curved Gridroom")
3. Click **Load**

### Starting the Simulation

1. Click the **Play** button in the Isaac Sim toolbar
2. The vehicle will start responding to sensor data and control inputs

---

## Troubleshooting

### Extension not loading

```
Error: "pegasus.simulator" extension not found
```

**Solution:** Re-run the link script:
```powershell
cd C:\path\to\PegasusSimulator
.\tools\packman\python.bat .\tools\scripts\link_app.py --path "$env:ISAAC_HOME"
```

### Python module not found

```
ModuleNotFoundError: No module named 'omni.isaac.core'
```

**Solution:** Make sure you're using Isaac Sim's bundled Python:
```powershell
& "$env:ISAAC_HOME\python.bat" -m pip install --upgrade --force-reinstall numpy scipy pymavlink pyyaml toml
```

### Isaac Sim crashes on startup

**Solution:**
- Update NVIDIA drivers to the latest version
- Make sure `ISAAC_HOME` points to the correct Isaac Sim 6.2 directory
- Run Isaac Sim once without the extension first, then add the extension

### GPU out of memory

**Solution:**
- Reduce the simulation resolution in the extension settings
- Close other GPU-intensive applications
- Lower the physics/rendering rate in `configs.yaml`

---

## Building and Running Examples

### Run a Python Example

```powershell
# Navigate to the examples directory
cd C:\path\to\PegasusSimulator\examples

# Run using Isaac Sim's Python
& "$env:ISAAC_HOME\python.bat" 1_px4_single_vehicle.py
```

### Run a Headless Simulation

```powershell
& "$env:ISAAC_HOME\python.bat" 1_px4_single_vehicle.py --headless
```

---

## Project Structure

```
PegasusSimulator/
├── docs/                          # Documentation
├── examples/                      # Example applications
│   ├── 0_template_app.py         # Basic template
│   ├── 1_px4_single_vehicle.py   # PX4 single vehicle
│   ├── 2_px4_multi_vehicle.py    # PX4 multi vehicle
│   ├── 3_ros2_single_vehicle.py  # ROS2 single vehicle
│   ├── 4_python_single_vehicle.py # Python API control
│   └── ...
├── extensions/
│   └── pegasus.simulator/         # Main Isaac Sim Extension
│       ├── config/
│       │   └── extension.toml    # Extension configuration
│       └── pegasus/simulator/    # Main Python package
├── tools/
│   ├── packman/                  # Package manager
│   └── scripts/                  # Link scripts
├── link_app.sh                   # Unix link script
├── link_app.bat                  # Windows link script
├── run_simulation.bat            # Windows launcher (NEW)
└── README.md
```

---

## Next Steps

- Read the [API Documentation](../../source/api.md) to learn how to create custom controllers
- Check the [Examples](../../source/examples.md) for more usage patterns
- Join the [GitHub Discussions](https://github.com/PegasusSimulator/PegasusSimulator/discussions) for community support
