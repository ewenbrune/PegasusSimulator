# AGENT.md — Isaac Sim 6.2 Migration Plan

> **This file is the single source of truth for the migration of PegasusSimulator from Isaac Sim 5.1 to Isaac Sim 6.2.**
> Any agent working on this project MUST update this file as they complete each step.

## Context

- **Project**: PegasusSimulator — a pure-Python Isaac Sim extension for multirotor drone simulation
- **Current Isaac Sim version**: 5.1.0
- **Target Isaac Sim version**: 6.2.0
- **Isaac Sim 6.2 source code**: Available locally at `../IsaacSim` (i.e., `/home/ewenb/simu/IsaacSim`)
- **No C++ extensions** — the entire project is Python, so no recompilation is needed

## Key API Mappings (Old → New)

| Old API (5.1) | New API (6.2) | Notes |
|---|---|---|
| `isaacsim.core.api.world.World` | `isaacsim.core.simulation_manager.SimulationManager` + `isaacsim.core.experimental.utils.stage` | World is gone; use SimulationManager for stepping/callbacks and stage utils for stage management |
| `isaacsim.core.api.robots.robot.Robot` | `isaacsim.core.experimental.prims.Articulation` or `RigidPrim` | Robot base class is gone; vehicles directly use Articulation/RigidPrim |
| `omni.isaac.dynamic_control._dynamic_control` | `isaacsim.core.experimental.prims.RigidPrim` / `Articulation` methods | Dynamic control is **removed**; use prim-based physics API |
| `isaacsim.core.utils.stage.*` | `isaacsim.core.experimental.utils.stage.*` | New backend system (usd/usdrt/fabric) |
| `isaacsim.core.utils.prims.define_prim` | `isaacsim.core.experimental.utils.stage.define_prim` | Moved |
| `isaacsim.core.utils.prims.get_prim_at_path` | `isaacsim.core.experimental.utils.stage.get_prim_at_path` or `pxr.Usd.Stage.GetPrimAtPath` | Moved |
| `isaacsim.core.utils.extensions.enable_extension` | `isaacsim.core.experimental.utils.app.enable_extension` | Moved |
| `isaacsim.core.utils.viewports.set_camera_view` | `omni.kit.viewport.utility.set_camera_view` | Moved to native Kit |
| `isaacsim.sensors.camera.camera.Camera` | `isaacsim.sensors.experimental.rtx.CameraSensor` | Completely rewritten |
| `omni.isaac.core.World` (examples) | `isaacsim.core.simulation_manager.SimulationManager` | Same as above |
| `omni.isaac.core.SimulationContext` | `isaacsim.core.simulation_manager.SimulationManager` | Same as above |
| `omni.isaac.core.objects.DynamicCuboid` | `isaacsim.core.experimental.objects.Cube` + `RigidPrim` | New object system |
| `isaacsim.replicator.agent.core` | External package — needs separate update | May need version bump |
| `isaacsim.storage.native` | **Unchanged** | Still active |
| `isaacsim.ros2.bridge` | **Unchanged** | Still active |
| `omni.replicator.core` | **Unchanged** | Still active (Kit built-in) |
| `omni.graph.core` | **Unchanged** | Still active (Kit built-in) |
| `isaacsim.util.debug_draw` | **Unchanged** | Still active |

## Migration Steps

### Step 0: Update `extension.toml` and project metadata

**Files:**
- `extensions/pegasus.simulator/config/extension.toml`
- `extensions/pegasus.simulator/setup.py`

**Changes:**
- Update version from `5.1.0` to `6.2.0`
- Update `python_requires` to `>=3.12` (Isaac Sim 6.2 uses Python 3.12)
- Update extension dependencies in `[dependencies]` section:
  - Replace `isaacsim.replicator.agent.core` with the correct version compatible with 6.2
  - Add `isaacsim.core.simulation_manager`
  - Add `isaacsim.core.experimental.prims`
  - Add `isaacsim.core.experimental.utils`
  - Add `isaacsim.core.experimental.objects`
  - Add `isaacsim.sensors.experimental.rtx`
  - Keep `isaacsim.storage.native`, `isaacsim.ros2.bridge`, `omni.replicator.core`, `omni.graph.core`
- Update `setup.py` classifiers

**Verification:** Extension loads without import errors in Isaac Sim 6.2.

---

### Step 1: Migrate `PegasusInterface` (the core singleton)

**Files:**
- `extensions/pegasus.simulator/pegasus/simulator/logic/interface/pegasus_interface.py`

**Changes:**

1. **Replace imports:**
   ```python
   # OLD
   from isaacsim.core.api.world import World
   from isaacsim.core.utils.stage import clear_stage, create_new_stage_async, update_stage_async, create_new_stage
   from isaacsim.core.utils.viewports import set_camera_view

   # NEW
   from isaacsim.core.simulation_manager import SimulationManager, SimulationEvent
   from isaacsim.core.experimental.utils import stage as stage_utils
   from isaacsim.core.experimental.utils.app import enable_extension
   from omni.kit.viewport.utility import set_camera_view
   ```

2. **Replace `World` usage with `SimulationManager`:**
   - `self._world = World(**self._world_settings)` → `SimulationManager.setup_simulation(dt=physics_dt, device=device)`
   - `self._world.reset()` → `SimulationManager.invalidate_physics()` + `SimulationManager.initialize_physics()`
   - `self._world.scene.add_default_ground_plane()` → Use `isaacsim.core.experimental.objects.GroundPlane`
   - `self._world.add_physics_callback(name, fn)` → `SimulationManager.register_callback(fn, SimulationEvent.PHYSICS_POST_STEP)`
   - `self._world.add_render_callback(name, fn)` → Use `omni.kit.app.get_app().get_update_event_stream()` or keep as custom event
   - `self._world.add_timeline_callback(name, fn)` → `SimulationManager.register_callback(fn, SimulationEvent.SIMULATION_STARTED/SIMULATION_STOPPED)`

3. **Replace stage management:**
   - `clear_stage()` → `stage_utils.close_stage()` + `stage_utils.create_new_stage()`
   - `create_new_stage_async()` → `stage_utils.create_new_stage_async()`
   - `update_stage_async()` → `stage_utils.update_app_async()`

4. **Replace `set_camera_view`:**
   - `from omni.kit.viewport.utility import set_camera_view` (same function, new import path)

5. **Update `load_environment_async`:**
   - Replace `World` creation with `SimulationManager.setup_simulation()`
   - Replace `self._world.reset_async()` with `SimulationManager` equivalent

**Verification:** `PegasusInterface` can be instantiated and a stage can be created.

---

### Step 2: Migrate `Vehicle` base class

**Files:**
- `extensions/pegasus.simulator/pegasus/simulator/logic/vehicles/vehicle.py`

**Changes:**

1. **Replace imports:**
   ```python
   # OLD
   from isaacsim.core.utils.prims import define_prim, get_prim_at_path
   from isaacsim.core.api.robots.robot import Robot
   from omni.isaac.dynamic_control import _dynamic_control

   # NEW
   from isaacsim.core.experimental.utils.stage import define_prim, get_prim_at_path
   from isaacsim.core.experimental.prims import Articulation, RigidPrim, XformPrim
   from isaacsim.core.simulation_manager import SimulationManager, SimulationEvent
   ```

2. **Replace `class Vehicle(Robot)` with `class Vehicle(Articulation)`:**
   - The `Articulation` class provides DOF control (get/set positions, velocities, efforts)
   - For non-articulated vehicles, use `RigidPrim` instead
   - The constructor signature changes: `Articulation(paths, positions=..., orientations=...)`

3. **Replace `self._prim = define_prim(...)` + `get_prim_at_path(...)`:**
   - Use `stage_utils.define_prim(path, "Xform")` and `stage_utils.get_prim_at_path(path)`
   - Or directly use `pxr.Usd.Stage.GetPrimAtPath(path)`

4. **Replace `self._world.add_physics_callback(...)` with `SimulationManager.register_callback(...)`:**
   - `self._world.add_physics_callback(self._stage_prefix + "/state", self.update_state)` → `SimulationManager.register_callback(self.update_state, SimulationEvent.PHYSICS_POST_STEP)`
   - Same for all other physics/render/timeline callbacks

5. **Replace `get_dc_interface()` method:**
   - The entire `_dynamic_control` interface is gone
   - Replace with direct `Articulation` / `RigidPrim` method calls:
     - `dc.get_rigid_body_pose(prim_path)` → `self.get_world_poses()`
     - `dc.get_rigid_body_linear_velocity(prim_path)` → `self.get_velocities()[0]`
     - `dc.get_rigid_body_angular_velocity(prim_path)` → `self.get_velocities()[1]`
     - `dc.apply_rigid_body_force(prim_path, force)` → `self.apply_forces(forces)`
     - `dc.get_articulation_dof_count(prim_path)` → `self.num_dofs`
     - `dc.set_articulation_dof_position_target(prim_path, dof_index, target)` → `self.set_dof_position_targets(targets, dof_indices=[dof_index])`
     - `dc.get_articulation_dof_position(prim_path, dof_index)` → `self.get_dof_positions(dof_indices=[dof_index])`
     - `dc.get_articulation_dof_velocity(prim_path, dof_index)` → `self.get_dof_velocities(dof_indices=[dof_index])`
     - `dc.set_articulation_dof_effort(prim_path, dof_index, effort)` → `self.set_dof_efforts(efforts, dof_indices=[dof_index])`

6. **Update `initialize()` method:**
   - Replace `self._world.add_physics_callback(...)` with `SimulationManager.register_callback(...)`
   - Replace `self._world.add_render_callback(...)` with render event stream
   - Replace `self._world.add_timeline_callback(...)` with `SimulationManager.register_callback(..., SimulationEvent.SIMULATION_STARTED/SIMULATION_STOPPED)`

**Verification:** Vehicle can be spawned and its state can be read/updated.

---

### Step 3: Migrate `Multirotor` class

**Files:**
- `extensions/pegasus.simulator/pegasus/simulator/logic/vehicles/multirotor.py`

**Changes:**

1. **Replace imports:**
   ```python
   # OLD
   from omni.isaac.dynamic_control import _dynamic_control

   # NEW
   from isaacsim.core.experimental.prims import Articulation
   ```

2. **Replace all `_dynamic_control` usage:**
   - `dc = _dynamic_control.acquire_dynamic_control_interface()` → Use `self` (the Articulation) directly
   - `dc.get_articulation_dof_count(self._prim_path)` → `self.num_dofs`
   - `dc.get_articulation_dof_position(self._prim_path, i)` → `self.get_dof_positions(dof_indices=[i])`
   - `dc.get_articulation_dof_velocity(self._prim_path, i)` → `self.get_dof_velocities(dof_indices=[i])`
   - `dc.set_articulation_dof_effort(self._prim_path, i, effort)` → `self.set_dof_efforts(efforts, dof_indices=[i])`
   - `dc.set_articulation_dof_velocity_target(self._prim_path, i, vel)` → `self.set_dof_velocity_targets(velocities, dof_indices=[i])`

3. **Update `update()` method:**
   - Replace force/torque application via dynamic control with `self.apply_forces()` and `self.apply_forces_and_torques_at_pos()`

**Verification:** Multirotor can be controlled (thrust commands produce motion).

---

### Step 4: Migrate sensors

**Files:**
- `extensions/pegasus.simulator/pegasus/simulator/logic/graphical_sensors/monocular_camera.py`
- `extensions/pegasus.simulator/pegasus/simulator/logic/graphical_sensors/lidar.py`
- `extensions/pegasus.simulator/pegasus/simulator/logic/sensors/imu.py`
- `extensions/pegasus.simulator/pegasus/simulator/logic/sensors/gps.py`
- `extensions/pegasus.simulator/pegasus/simulator/logic/sensors/barometer.py`
- `extensions/pegasus.simulator/pegasus/simulator/logic/sensors/magnetometer.py`

**Changes:**

1. **MonocularCamera — replace `isaacsim.sensors.camera.camera.Camera` with `isaacsim.sensors.experimental.rtx.CameraSensor`:**
   ```python
   # OLD
   from isaacsim.sensors.camera.camera import Camera
   self._camera = Camera(prim_path=..., resolution=..., frequency=...)

   # NEW
   from isaacsim.sensors.experimental.rtx import CameraSensor
   self._camera = CameraSensor(path=..., resolution=(height, width), annotators=["rgb"])
   ```
   - Update all `self._camera.get_*()` calls to new API
   - `get_rgba()` → `self._camera.get_data("rgb")`
   - `get_depth()` → `self._camera.get_data("distance_to_image_plane")`
   - `get_current_frame()` → `self._camera.get_data(annotator)`

2. **Lidar — update render product creation:**
   ```python
   # OLD
   hydra_texture = rep.create.render_product(self._sensor.GetPath(), [1, 1], name="Isaac")

   # NEW
   # Use the new RTX sensor API or keep omni.replicator.core for render products
   ```
   - Check if `omni.kit.commands.execute("IsaacSensorCreateRtxLidar", ...)` still works or needs update

3. **Physics sensors (IMU, GPS, Barometer, Magnetometer):**
   - These likely use `omni.isaac.sensor` or dynamic control — check each one
   - Replace any `_dynamic_control` usage with `Articulation`/`RigidPrim` methods
   - IMU: `dc.get_rigid_body_linear_velocity()` → `self.get_velocities()`
   - GPS: `dc.get_rigid_body_pose()` → `self.get_world_poses()`

**Verification:** All sensors produce data at expected rates.

---

### Step 5: Migrate ROS2 backend and graphs

**Files:**
- `extensions/pegasus.simulator/pegasus/simulator/logic/backends/ros2_backend.py`
- `extensions/pegasus.simulator/pegasus/simulator/logic/graphs/ros2_camera_graph.py`
- `extensions/pegasus.simulator/pegasus/simulator/logic/people_backends/ros2_people_backend.py`

**Changes:**

1. **Replace `enable_extension` import:**
   ```python
   # OLD
   from isaacsim.core.utils.extensions import enable_extension

   # NEW
   from isaacsim.core.experimental.utils.app import enable_extension
   ```

2. **Update OmniGraph node types in `ros2_camera_graph.py`:**
   - `isaacsim.core.nodes.IsaacCreateViewport` → Check if this node still exists in 6.2
   - `isaacsim.core.nodes.IsaacGetViewportRenderProduct` → Check if this node still exists
   - These may have been renamed — check `../IsaacSim/source/extensions/isaacsim.core.nodes/` for available nodes

3. **Update `omni.isaac.sensor.Camera` import:**
   ```python
   # OLD
   from omni.isaac.sensor import Camera

   # NEW
   from isaacsim.sensors.experimental.rtx import CameraSensor
   ```

4. **Update replicator writer usage:**
   - `rep.writers.get("LdrColorSDROS2PublishImage")` → Check if writer names changed in 6.2
   - `rep.writers.get("RtxLidarROS2PublishPointCloud")` → Check if writer names changed
   - `read_camera_info()` from `isaacsim.ros2.bridge` → Check if API changed

5. **Update `og.Controller.attribute()` usage:**
   - The gate path pattern may have changed — verify against 6.2 source

**Verification:** ROS2 topics are published with correct data.

---

### Step 6: Migrate people/person simulation

**Files:**
- `extensions/pegasus.simulator/pegasus/simulator/logic/people/person.py`

**Changes:**

1. **Replace `omni.isaac.core.SimulationContext`:**
   ```python
   # OLD
   from omni.isaac.core import SimulationContext

   # NEW
   from isaacsim.core.simulation_manager import SimulationManager
   ```

2. **Replace `isaacsim.core.utils.prims`:**
   ```python
   # OLD
   from isaacsim.core.utils import prims

   # NEW
   from isaacsim.core.experimental.utils import stage as stage_utils
   ```

3. **Replace `isaacsim.replicator.agent.core`:**
   - This is an external package from the "metrosim" repository
   - Check if a 6.2-compatible version exists
   - Update imports: `PrimPaths`, `CharacterUtil` — check if API changed

4. **Replace `self._world.add_physics_callback(...)` with `SimulationManager.register_callback(...)`**

**Verification:** People can be spawned and animated.

---

### Step 7: Migrate example scripts

**Files:**
- `examples/0_template_app.py`
- `examples/1_px4_single_vehicle.py`
- `examples/2_px4_multi_vehicle.py`
- `examples/3_ros2_single_vehicle.py`
- `examples/4_python_single_vehicle.py`
- `examples/5_python_multi_vehicle.py`
- `examples/6_paper_results.py`
- `examples/8_camera_vehicle.py`
- `examples/9_people.py`
- `examples/10_graphs.py`
- `examples/11_ardupilot_multi_vehicle.py`

**Changes (apply to all examples):**

1. **Replace `from omni.isaac.core.world import World` / `from omni.isaac.core import World`:**
   ```python
   # OLD
   from omni.isaac.core.world import World

   # NEW
   from isaacsim.core.simulation_manager import SimulationManager
   ```

2. **Replace `from omni.isaac.core.objects import DynamicCuboid`:**
   ```python
   # OLD
   from omni.isaac.core.objects import DynamicCuboid

   # NEW
   from isaacsim.core.experimental.objects import Cube
   from isaacsim.core.experimental.prims import RigidPrim
   ```

3. **Replace `isaacsim.core.utils.prims as prim_utils`:**
   ```python
   # OLD
   import isaacsim.core.utils.prims as prim_utils

   # NEW
   from isaacsim.core.experimental.utils import stage as stage_utils
   ```

4. **Replace `World()` instantiation:**
   ```python
   # OLD
   self.world = World()
   self.world.scene.add_default_ground_plane()

   # NEW
   from isaacsim.core.experimental.objects import GroundPlane
   SimulationManager.setup_simulation(dt=1.0/60.0, device="cuda:0")
   ground_plane = GroundPlane(paths="/World/ground_plane")
   ```

5. **Replace `self.world.add_physics_callback(...)`:**
   ```python
   # OLD
   self.world.add_physics_callback('name', self.callback)

   # NEW
   from isaacsim.core.simulation_manager import SimulationEvent
   SimulationManager.register_callback(self.callback, SimulationEvent.PHYSICS_POST_STEP)
   ```

6. **Replace `self.world.add_render_callback(...)`:**
   ```python
   # OLD
   self.world.add_render_callback('name', self.callback)

   # NEW
   import omni.kit.app
   self._render_sub = omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(self.callback)
   ```

7. **Replace `self.world.add_timeline_callback(...)`:**
   ```python
   # OLD
   self.world.add_timeline_callback('name', self.callback)

   # NEW
   from isaacsim.core.simulation_manager import SimulationEvent
   SimulationManager.register_callback(self.callback, SimulationEvent.SIMULATION_STARTED)
   ```

8. **Replace `self.world.reset()`:**
   ```python
   # OLD
   self.world.reset()

   # NEW
   SimulationManager.invalidate_physics()
   SimulationManager.initialize_physics()
   ```

9. **Replace `enable_extension` import:**
   ```python
   # OLD
   from isaacsim.core.utils.extensions import enable_extension

   # NEW
   from isaacsim.core.experimental.utils.app import enable_extension
   ```

**Verification:** Each example runs without errors.

---

### Step 8: Update `params.py` and asset paths

**Files:**
- `extensions/pegasus.simulator/pegasus/simulator/params.py`

**Changes:**

1. **Update asset root path handling:**
   - `nucleus.get_assets_root_path()` — check if this still returns the correct path
   - Default asset root in 6.2 is `https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.2`
   - Update `NVIDIA_SIMULATION_ENVIRONMENTS` dict if asset paths changed

2. **Update vehicle USD asset paths:**
   - Check if `/Isaac/Robots/` paths still exist or moved to `/Isaac/Robots_Multiphysics/`
   - Update `IRIS_USD_PATH` and other vehicle paths accordingly

**Verification:** Assets load correctly from Nucleus.

---

### Step 9: Update `extension.py` (the IExt entry point)

**Files:**
- `extensions/pegasus.simulator/pegasus/simulator/extension.py`

**Changes:**

1. **Check if `omni.ext.IExt` API changed** — likely unchanged
2. **Update any deprecated imports** used in the extension lifecycle
3. **Update `on_startup` / `on_shutdown`** if they use deprecated APIs

**Verification:** Extension loads and unloads cleanly.

---

### Step 10: Testing and validation

**Tasks:**

1. **Test basic startup:**
   - Launch Isaac Sim 6.2 with the PegasusSimulator extension
   - Verify no import errors or deprecation warnings

2. **Test vehicle spawning:**
   - Spawn an Iris vehicle
   - Verify it appears in the scene

3. **Test physics:**
   - Apply thrust commands
   - Verify the vehicle moves correctly

4. **Test sensors:**
   - Verify IMU, GPS, Barometer, Magnetometer produce data
   - Verify camera produces images
   - Verify lidar produces point clouds

5. **Test PX4 backend:**
   - Launch PX4 SITL
   - Verify MAVLink communication works

6. **Test ROS2 backend:**
   - Verify ROS2 topics are published
   - Verify sensor data is correct

7. **Test all examples:**
   - Run each example script
   - Verify expected behavior

---

## Progress Tracking

- [x] Step 0: Update `extension.toml` and project metadata
- [x] Step 1: Migrate `PegasusInterface`
- [x] Step 2: Migrate `Vehicle` base class
- [x] Step 3: Migrate `Multirotor` class
- [x] Step 4: Migrate sensors
- [x] Step 5: Migrate ROS2 backend and graphs
- [x] Step 6: Migrate people/person simulation
- [x] Step 7: Migrate example scripts
- [x] Step 8: Update `params.py` and asset paths (no changes needed — uses `nucleus.get_assets_root_path()` dynamically)
- [x] Step 9: Update `extension.py` (no changes needed — uses only active `omni.*` APIs)
- [ ] Step 10: Testing and validation

## Windows 11 Support

The project now supports Windows 11 with the following changes:

1. **`tools/packman/bootstrap/configure.bat`** — Updated Python version from 3.7.9 to 3.12.13 (matching Isaac Sim 6.2's bundled Python)
2. **`setup.py`** — Now checks for `ISAAC_HOME` env var (used by Isaac Sim 6.2) with fallback to `ISAACSIM_PATH`
3. **`run_simulation.bat`** — New Windows launcher script that:
   - Validates `ISAAC_HOME` is set
   - Registers the extension with Isaac Sim
   - Launches Isaac Sim with the Pegasus extension enabled

### Windows 11 Prerequisites
- Isaac Sim 6.2 installed via Omniverse Launcher
- `ISAAC_HOME` environment variable set to the Isaac Sim 6.2 install path
- NVIDIA GPU with latest drivers

## Notes for Agents

1. **Always check the Isaac Sim 6.2 source at `../IsaacSim`** when unsure about an API:
   - New APIs: `../IsaacSim/source/extensions/`
   - Deprecated APIs: `../IsaacSim/source/deprecated/`
   - Migration skill: `../IsaacSim/source/skills/isaac-sim-migration/SKILL.md`

2. **The `isaacsim.core.experimental.prims` API uses Warp arrays** (`wp.array`) instead of NumPy arrays. You may need to convert between them using `wp.from_numpy()` and `.numpy()`.

3. **The `SimulationManager` is a singleton** — use `SimulationManager.method()` directly, no instantiation needed.

4. **Callbacks registered with `SimulationManager.register_callback()`** receive different arguments than the old `World.add_physics_callback()`. Check the signature.

5. **The `Articulation` class** is the replacement for `Robot`. It provides DOF-level control. For simple rigid bodies, use `RigidPrim`.

6. **Update this file** as you complete each step — check off boxes, add notes, and document any deviations from the plan.

7. **When in doubt**, look at the Isaac Sim 6.2 examples in `../IsaacSim/source/examples/` and `../IsaacSim/source/standalone_examples/` for reference implementations.
