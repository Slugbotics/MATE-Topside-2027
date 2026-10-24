# Photogrammetry Pipeline Manual

This document outlines the 3D reconstruction pipeline MATE software is using for photogrammetry-related tasks in relation to the 2026 MATE global championship. The system is designed to provide a path to generate 3D assets via photogrammetry without requiring a local CUDA-enabled GPU.

## System Architecture

The architecture is split into two distinct execution environments: **High-Performance Vision (Python/Shared Memory)** and **The Reconstruction Pipeline (Docker/OpenMVS) for non linux enviornments**.

## 1. Reconstruction Layer (Hybrid COLMAP/OpenMVS)

Because COLMAP requires NVIDIA CUDA for dense reconstruction, we use a hybrid approach:

1.  **COLMAP (Sparse):** Extracts features and matches images to determine camera positions. We run this with `--dense 0` to allow CPU-only execution.
2.  **Model Converter:** Converts COLMAP's binary output to `.txt` for interoperability.
3.  **OpenMVS:** A secondary Docker container takes the sparse map and performs Dense Point Cloud generation, Meshing, and Texturing.

---

## 2. Environment Setup & Execution

The pipeline is containerized to ensure consistency, but interaction with the host display (OpenCV) varies by OS.

### Prerequisites (All Platforms)

- **Docker Desktop** (Mac/Windows) or **Docker Engine** (Linux).
- **Python 3.10+** (for local testing/script management).

### Mac (Intel & Apple Silicon)

Macs use the `linux/amd64` platform flag in the Dockerfile to ensure compatibility with the toolchains.

1.  **XQuartz:** You must install [XQuartz](https://www.xquartz.org/) to see the OpenCV window from inside Docker.
2.  **Permissions:** Run `xhost +localhost`.
3.  **Run:**
    ```bash
    docker build --platform linux/amd64 -t vision-pipeline .
    ./run_pipeline.sh
    ```

### Windows (WSL2)

1.  **WSL2:** Ensure you are running Ubuntu 22.04 inside WSL2.
2.  **GWSL:** Install [GWSL](https://opticos.github.io/gwsl/) from the Microsoft Store to handle the GUI display.
3.  **Run:**
    ```bash
    docker build -t vision-pipeline .
    sh run_pipeline.sh
    ```

### Linux (Native)

1.  **Display:** No extra configuration needed as Docker can share the `:0` X11 socket.
2.  **Run:**
    ```bash
    docker build -t vision-pipeline .
    chmod +x run_pipeline.sh
    ./run_pipeline.sh
    ```

---

## 4. Next Steps - Running w/ out Docker

If we want to run the pipeline natively on the topside host machine to bypass Docker virtualization overhead, we need (i think) to do these steps.

### A. System Binaries Setup

- **Mac (Homebrew):**
  ```bash
  brew install python@3.10 colmap openmvs
  ```
- **Windows (Scoop):**
  ```powershell
  scoop bucket add science
  scoop install colmap openmvs python
  ```
- **Linux (Ubuntu/Debian Native):**
  ```bash
  sudo apt update
  sudo apt install -y python3 python3-pip colmap openmvs libgl1-mesa-glx libglib2.0-0
  ```

### B. Python Environment Setup

Navigate to the project root directory and install the required core computer vision and data modules:

```
pip3 install opencv-python ultralytics numpy
```

## 5. Post-Processing & Model Viewing (MeshLab)

Once the shell script reaches `=== PIPELINE COMPLETE ===`, the 3D asset is exported to the `output/` folder as a standard wavefront cluster: `final_model.obj`, `final_model.mtl`, and its associated texture maps.

### Importing the Asset

1. Download and open [MeshLab](https://www.meshlab.net/).
2. Go to **File -> Import Mesh...** and select `output/final_model.obj`.
3. MeshLab parses the `.mtl` file alongside the object definitions automatically. If the model looks untextured or flat, toggle the **Render -> Color -> User-Defined/Texture** setting in the top toolbar.

## 6. TODO List

- [ ] **Shared Memory Cleanup:** Implement a watchdog to ensure `/dev/shm` handles are unlinked if the script crashes unexpectedly.
- [ ] **OpenMVS Optimization:** Fine-tune `DensifyPointCloud` parameters to reduce RAM usage during large-scale captures.
- [ ] **Test on Actual Topside/Linux Environment:** Test on the actual laptop/topside w/ native Linux.
