# Setup Checklist

## 1. GitHub and IDE

- Confirm Git user identity:
  - `git config --global user.name`
  - `git config --global user.email`
- Create a new GitHub repository.
- Add the remote:
  - `git remote add origin <github-repo-url>`
- Push the first branch:
  - `git add .`
  - `git commit -m "Initialize multi-UAV Marine City workspace"`
  - `git push -u origin master`

## 2. Visual Studio / VS Code

- Visual Studio 2022 Professional is installed.
- VS Code is installed and available through `code`.
- Recommended VS Code extensions:
  - Python
  - Pylance
  - YAML
  - GitHub Pull Requests
  - NVIDIA Omniverse / USD-related extensions if available

## 3. NVIDIA Isaac Sim

- Install Isaac Sim through NVIDIA Omniverse/Launcher or the current NVIDIA distribution route.
- Verify that Isaac Sim opens successfully on the RTX 4080.
- Record the Isaac Sim install path in `isaac/README.md`.
- Confirm Python scripting works inside Isaac Sim.

## 4. Cesium

- Create a Cesium ion account.
- Create a Cesium ion access token.
- Store the token outside Git, for example in `.env`:
  - `CESIUM_ION_TOKEN=...`
- Use WGS84 coordinates for Haeundae Marine City as the scene origin.

## 5. First Simulation

- Load the Marine City geospatial environment.
- Add three UAV camera actors with synchronized timestamps.
- Export RGB images, depth if available, camera intrinsics, camera extrinsics, and WGS84 poses.
- Run the first object-detection pass.
