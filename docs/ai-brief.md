# ut-raft AI Brief

> Single-file reference for AI tools working with the ut-raft framework.

## 1. Purpose

ut-raft is a Python plugin that bridges **ut-core** (C/C++ unit-test binaries running on embedded devices) and **python_raft** (the Python-based Rapid Application For Test automation framework). It lives inside the python_raft plugin directory at `framework/plugins/ut_raft/` and provides the machinery to:

- Launch a ut-core test binary on a remote device over a console session (serial or SSH).
- Navigate the CUnit or GTest interactive text menus that ut-core presents.
- Select and run individual suites or test cases by name.
- Feed prompted input values (lists, direct values, Y/N user responses) into interactive L3 tests.
- Collect pass/fail results by parsing the CUnit/GTest "Run Summary" output.
- Transfer files to/from the device (SCP, SFTP, rsync) and manage media playback for AV tests.

## 2. Dependency Chain

```
python_raft (test-runner host)
    |
    +-- ut-raft (this repo -- Python plugin inside python_raft)
    |       |
    |       +-- consoleInterface (from python_raft framework.core)
    |       +-- testController   (from python_raft framework.core)
    |       +-- logModule        (from python_raft framework.core)
    |       +-- outboundClient   (from python_raft framework.core)
    |
    +----> [console session: serial / SSH] ----> Device Under Test (DUT)
                                                    |
                                                    +-- ut-core test binary
                                                    |     (CUnit or GTest interactive menu)
                                                    |
                                                    +-- ut-control (optional WebSocket RPC
                                                          bridge for HAL calls)
```

- **python_raft** provides device management, session handling, logging, and the test-runner entry point.
- **ut-raft** is installed as a python_raft plugin; test scripts import from `framework.plugins.ut_raft`.
- **ut-core** is the C/C++ test framework on the device that presents interactive text menus over the console.
- **ut-control** is an optional component that provides a WebSocket RPC bridge so the host can invoke HAL API calls on the device.

## 3. Repository Layout

```
ut-raft/
  __init__.py                 # Exposes utHelperClass
  utSuiteNavigator.py         # Menu navigation (utCFramework + UTSuiteNavigatorClass)
  utHelper.py                 # Test helper extending python_raft testController
  configRead.py               # YAML config loader with dot-notation access
  utBaseUtils.py              # File-transfer and device utilities
  utPlayer.py                 # GStreamer media-player control
  interactiveShell.py         # Local pexpect-based shell (consoleInterface impl)
  utUserResponse.py           # Y/N user-prompt helper
  requirements.txt            # pexpect==4.9.0
  configs/
    utPlayerConfig.yml        # Per-vendor GStreamer player profiles
  examples/
    example_ut_suite.yml      # Example suite config (dsAudio)
    example_ut_menu_navigator.yml  # Example menu navigator config
    host/
      install.sh              # Clones python_raft + ut-raft, sets up venv
      activate_venv.sh        # Activates the Python virtual environment
```

## 4. Module Reference

### 4.1 utSuiteNavigator.py

This is the core module. It contains two classes.

#### 4.1.1 utCFramework

Low-level driver that talks directly to a CUnit/GTest interactive menu over a `consoleInterface` session.

| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__` | `(session: consoleInterface, log: logModule = None)` | Stores session, sets CUnit prompt patterns (`"command: "` and `") : "`). |
| `start` | `(command: str) -> str` | Writes the launch command (e.g., `./run.sh -p profile.yaml`), reads until the `command:` prompt, returns output. |
| `stop` | `() -> str` | Sends `q` to quit the menu, reads until the shell prompt `#`. |
| `select` | `(suite_name, test_name=None, promptWithAnswers=None, timeout=10, is_cunit=True) -> str` | Navigates to a suite and optionally a specific test. Sends `x`/`m` (CUnit/GTest) then `u` to reach top menu, `s` to list suites, picks by index, then either `r` (run all) or `s` again to pick a specific test. Handles interactive prompts via `inputPrompts()`. |
| `inputPrompts` | `(promptsWithAnswers: list) -> str` | Iterates over prompt/answer pairs. For `query_type: "list"`, finds the index in the menu output. For `query_type: "direct"`, sends the value directly. For `input: "user_prompt"`, asks the human operator via `utUserResponse.getUserYN()`. |
| `find_index_in_output` | `(output: str, target_name: str) -> int or None` | Regex-searches for `<number>. [target_name]` pattern in menu output, returns the number. |
| `collect_results` | `(output: str, gtest: bool = False) -> bool or None` | Parses CUnit or GTest "Run Summary" tables. Returns `True` if zero failures, `False` if failures found, `None` if output format is unexpected. |

**CUnit menu navigation sequence:**
```
command: x        (return to top -- CUnit)
command: u        (go up)
command: s        (list suites)
  1. [Suite A]
  2. [Suite B]
) : 2             (select suite by index)
command: s        (list tests in suite)
  1. [Test 1]
  2. [Test 2]
) : 1             (select test by index)
... test runs ... prompts may appear ...
command:          (back at prompt when done)
```

For GTest menus, `m` is sent instead of `x` to return to the top menu.

#### 4.1.2 UTSuiteNavigatorClass

Higher-level navigator that combines config validation with `utCFramework`.

| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__` | `(config: str, startKey: str, session: consoleInterface, log: logModule = None)` | Loads YAML config via `ConfigRead`, selects framework type (`UT-C` or `C` -> `utCFramework`). |
| `start` | `() -> None` | Reads the `execute` command from config and calls `framework.start()`. |
| `stop` | `() -> None` | Delegates to `framework.stop()`. |
| `select` | `(suite_name, test_name=None, promptWithAnswers=None, timeout=10, is_cunit=True) -> str` | Validates the test name exists in the config's suite list, then delegates to `framework.select()`. |
| `collect_results` | `(output: str, gtest: bool = False) -> bool` | Delegates to `framework.collect_results()`. |
| `run` | `(suite_name, test_name=None) -> bool` | Convenience: calls `start()`, `select()`, and `collect_results()` in sequence. |

### 4.2 utHelper.py

Extends `testController` from python_raft. This is the base class that HAL test scripts typically inherit from.

| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__` | `(testName: str, qcId: str, log: logModule = None)` | Calls `super().__init__()`, creates `utBaseUtils` instance. |
| `waitForBoot` | `() -> bool` | Pings the DUT, logs boot time. |
| `reboot` | `(commandLine: bool = False) -> bool` | Reboots DUT via shell command or power control. |
| `writeCommands` | `(commands: str, session=None, logOutput=True) -> str` | Splits multi-line string into individual commands, sends each, logs output. |
| `writeCommandsOnPrompt` | `(commands: list, prompt=None, session=None) -> str` | Sends commands and waits for prompt between each. Uses device's configured prompt if none given. |
| `createDirectoryOnDevice` | `(dirPath: str, device="dut")` | Runs `mkdir` on the target device. |
| `copyFolder` | `(sourcePath, destinationPath, session=None)` | Runs `cp -r` on the target device. |
| `changeFolderPermission` | `(permission, path, session=None)` | Runs `chmod` on the target device. |
| `copyFileFromHost` | `(sourcePath, destinationPath, targetDevice="dut", use_sftp=False) -> str` | Copies a file from host to device via SCP or SFTP. |
| `downloadToDevice` | `(urls: list, target_directory: str, device="dut", use_sftp=False)` | Downloads files via `outboundClient`, then copies to device. |
| `deleteFromDevice` | `(files: list, device="dut", logOutput=True)` | Runs `rm -rf` for each file path. |
| `catFile` | `(filePath, prompt=None, session=None) -> str` | Reads a file on the device using `cat`. |
| `saveLogForAnalysis` | `(inputLog: list, filename: str)` | Writes log lines to a local file. |
| `dump_stepResults` | `(input_file, output_file)` | Parses STEP_RESULT lines from a log file and writes a CSV summary. |
| `testEndFunction` | `(powerOff=True) -> bool` | Cleanup override: calls parent cleanup, dumps step summary CSV. |
| `isStringInList` | `(string, searchList) -> bool` | Simple substring search across a list. |

### 4.3 configRead.py

`ConfigRead` loads YAML data (from a file path, a YAML string, or a dict) and exposes values via dot-notation attribute access.

| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__` | `(data=None, start_key=None)` | Loads YAML, optionally scoping to a sub-key. Sets `self.fields` (dict) and creates nested `ConfigRead` attributes. Numeric YAML keys are prefixed with `_` (e.g., key `0` becomes `._0`). |
| `get` | `(field_path: str = None)` | Dot-separated path lookup (e.g., `"test.suites"`). Supports integer indices for lists. Returns `None` if not found. |
| `fields` | attribute | Raw dict of the loaded YAML data at the current scope. |

**Access patterns:**
```python
config = ConfigRead("path/to/config.yml", "dsAudio")
config.description          # "dsAudio Device Settings testing profile for UT"
config.test.execute         # "cd bin;./run.sh"
config.test.type            # "UT-C"
config.fields['test']['suites'][0]['name']  # "L1 dsAudio - Sink"
```

### 4.4 utBaseUtils.py

Utility class for file transfer and remote device operations.

| Method | Signature | Description |
|--------|-----------|-------------|
| `scpCopy` | `(session, sourcePath, destinationPath, isRemoteSource=False) -> str` | SCP file transfer between host and device. Direction controlled by `isRemoteSource`. |
| `sftpCopy` | `(session, sourcePath, destinationPath) -> str` | SFTP upload via Paramiko with 3 retries. |
| `rsync` | `(session, sourcePath, destinationPath) -> str` | rsync over SSH; falls back to SCP if rsync is unavailable on device. |
| `untar` | `(session, tar_gz_path, extract_path) -> bool` | Extracts a .tar.gz on the remote device. |
| `change_directory` | `(session, directory_path) -> bool` | `cd` on remote device with verification. |
| `restart_process_by_name` | `(session, process_name, binary_dir="/usr/bin") -> bool` | Kills and restarts a named process on the device. |

### 4.5 utPlayer.py

Controls GStreamer media playback on the device for AV testing scenarios.

| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__` | `(session, vendor: str, log=None)` | Loads vendor-specific player config from `configs/utPlayerConfig.yml`. Runs prerequisite commands (env vars, westeros init, etc.). |
| `setMixerInput` | `(mixer_input: MixerInputTypes)` | Selects primary or secondary audio mixer input configuration. |
| `play` | `(streamFile: str)` | Launches `gst-play-1.0` with vendor-specific flags and mixer config. |
| `stop` | `()` | Sends the stop command (typically Ctrl-C `\x03`). |

`MixerInputTypes` enum: `MIXER_INPUT_PRIMARY` (1), `MIXER_INPUT_SECONDARY` (2).

### 4.6 interactiveShell.py

`InteractiveShell` implements `consoleInterface` using `pexpect` to spawn a local `/bin/bash` process. Used for local/host-side testing and as a session stand-in during development.

| Method | Signature | Description |
|--------|-----------|-------------|
| `open` | `() -> str` | Spawns bash via pexpect, waits for prompt. |
| `write` | `(command: str)` | Sends a command line (with newline). |
| `read_until` | `(message: str) -> str` | Blocks until the regex pattern appears in output (10s timeout, 2 attempts). |
| `read_all` | `() -> str` | Non-blocking read of all available output (1s timeout). |
| `close` | `()` | Terminates the shell process. |

### 4.7 utUserResponse.py

| Method | Signature | Description |
|--------|-----------|-------------|
| `getUserYN` | `(query="Please Enter Y or N :") -> bool` | Prompts the human operator for Y/N input via `input()`. Returns `True` for Y, `False` for N. Loops on invalid input. |

Used during L3 interactive tests when the test binary asks a question that requires a human judgment call (e.g., "Did you hear audio? Y/N").

## 5. Configuration Format

### 5.1 Suite Configuration (YAML)

Used by `UTSuiteNavigatorClass`. The top-level key is a module name that serves as `startKey`.

```yaml
dsAudio:                              # startKey
    description: "dsAudio testing"
    test:
        execute: "cd bin;./run.sh -p ../profiles/Sink_AudioSettings.yaml"
        type: UT-C                    # "UT-C" or "C" for CUnit, "UT-G" planned for GTest
        suites:
            0:
                name: "L1 dsAudio - Sink"
                tests:                # Optional; omit for suites run as a whole
                    - None
            1:
                name: "L2 dsAudio - Sink"
            2:
                name: "L3 dsAudio - Sink"
                tests:
                    - "Initialize dsAudio"
                    - "Enable Audio Port"
                    - "Terminate dsAudio"
```

Key fields:
- `execute`: Shell command to launch the ut-core binary on the device.
- `type`: Test framework type. `UT-C` / `C` = CUnit-based ut-core. `UT-G` planned for GTest.
- `suites`: Numbered dict of suites. Each has a `name` matching the CUnit suite name and optional `tests` list.

### 5.2 Player Configuration (utPlayerConfig.yml)

Per-vendor GStreamer configuration keyed by platform name:

```yaml
amlogic:
  gstreamer:
    prerequisites:              # Shell commands run before playback
      - export XDG_RUNTIME_DIR="/tmp"
      - export WAYLAND_DISPLAY=wayland-0
      - westeros-init &
    play_command: gst-play-1.0
    stop_command: "\x03"        # Ctrl-C
    primary_mixer_input_config: ""
    secondary_mixer_input_config: '--audiosink "amlhalasink direct-mode=0"'
```

Supported vendors in the shipped config: `amlogic`, `realtek`, `mediatek`, `amlogic_polaris`, `vdevice`.

### 5.3 Prompt/Answer Format

For interactive L3 tests, `promptWithAnswers` is a list of dicts:

```python
promptWithAnswers = [
    {
        "query_type": "list",       # Menu selection -- finds index by name
        "query": "Select dsAudio Port:",
        "input": "dsAUDIOPORT_TYPE_SPEAKER"
    },
    {
        "query_type": "direct",     # Direct value entry
        "query": "Select Port Index[0-10]:",
        "input": "0"
    },
    {
        "query_type": "direct",
        "query": "Did you hear audio?",
        "input": "user_prompt"      # Special value: asks the human operator
    }
]
```

## 6. Typical Usage Flow

A python_raft test script for a HAL component follows this pattern:

```python
# 1. Test class inherits from utHelperClass
class dsAudioL3Test(utHelperClass):
    def __init__(self):
        super().__init__("dsAudioL3", qcId="QC001")

    def testFunction(self):
        # 2. Get the console session to the DUT
        session = self.session  # From python_raft device management

        # 3. Create the suite navigator with a YAML config
        navigator = UTSuiteNavigatorClass(
            config="dsAudio_test_config.yml",
            startKey="dsAudio",
            session=session
        )

        # 4. Start the test binary on the device
        navigator.start()   # Sends the 'execute' command from config

        # 5. Select and run a specific test
        output = navigator.select(
            suite_name="L3 dsAudio - Sink",
            test_name="Enable Audio Port",
            promptWithAnswers=[
                {"query_type": "list", "query": "Select dsAudio Port:", "input": "dsAUDIOPORT_TYPE_SPEAKER"},
                {"query_type": "direct", "query": "Select Port Index[0-10]:", "input": "0"}
            ],
            timeout=30
        )

        # 6. Check results
        result = navigator.collect_results(output)
        assert result == True, "Test failed"

        # 7. Stop the test binary
        navigator.stop()
```

## 7. Key Design Patterns

- **Console-driven test execution**: All interaction with the device happens through text-based console I/O. ut-raft reads menu output, parses numbered items with regex, and writes the appropriate index.
- **Plugin architecture**: ut-raft is installed into `python_raft/framework/plugins/ut_raft/`. It imports from `framework.core` (consoleInterface, testController, logModule).
- **Config-as-code**: Suite definitions, player profiles, and prompt sequences are all YAML-driven, allowing test configurations to live alongside test code in HAL test repos.
- **L1/L2/L3 test levels**: L1 = positive/negative unit tests. L2 = functional state tests. L3 = interactive tests requiring human operator input (Y/N judgments, visual/audio verification).
- **Vendor abstraction**: The `utPlayer` and `utPlayerConfig.yml` abstract platform-specific GStreamer setup (Amlogic, Realtek, MediaTek, etc.) behind a common play/stop interface.
