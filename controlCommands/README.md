# controlCommands — YAML Command Templates

## Overview

The YAML files in this directory are **command templates** used by host-side Python controllers to send control-plane messages to a running vcomponent (virtual HAL stub) on the Device Under Test (DUT) during automated L3 testing.

Each file describes a single command that can be injected into the vcomponent — for example, simulating an HDMI cable plug event, setting an HDCP authentication state, or triggering a deep sleep wakeup.

---

## Architecture

```
Host (test machine)
│
│   Python controller (virtualHdmiController, virtualDeepSleep, …)
│   1. loads YAML template  ──►  controlCommands/<module>/<command>.yaml
│   2. patches param fields
│   3. yaml.dump() → YAML string
│   4. sends via utPlaneController.sendMessage() or curl over SSH
│
└──► DUT (SSH)
         │
         └──► vcomponent HTTP control-plane
              POST http://localhost:<control-plane-port>/api/postKVP
              Content-Type: application/x-yaml
              <YAML payload>
```

The vcomponent parses the YAML, identifies the command from the root node and `command:` key, and fires the corresponding HAL callback into the HAL under test.

---

## YAML File Structure

Every command file follows the same three-level layout:

```yaml
<root_node>:              # identifies the target vcomponent module
  command: <name>         # the command to invoke
  description: ...        # human-readable only; ignored by the stub
  params:                 # (or device:/message:/config: depending on the module)
    <field>: <value>      # typed parameters — see field comments for types/enums
```

| Layer | Purpose |
|---|---|
| `root_node` | Routes the message to the correct vcomponent (e.g. `hdmiinput`, `deepsleep`, `HdmiCec`) |
| `command` | Selects the handler within that vcomponent |
| `params` / `device` / `message` / `config` | Carries the typed arguments for the command |

---

## Sending a Control Command to Control Plane

Edit the YAML file to the desired parameter values, then POST it directly to the vcomponent control-plane:

```bash
curl -X POST \
  -H "Content-Type: application/x-yaml" \
  --data-binary @controlCommands/<module>/<yaml-file-name>.yaml \
  "http://<DUT_IP>:<control-plane-port>/api/postKVP"
```

Replace `<DUT_IP> <module> <yaml-file-name>` with the device address and the file path with whichever command YAML you want to send.

---

## Directory Structure

```
controlCommands/
├── bootreason/
│   └── bootreason_external_triggers.yaml     # inject a boot reason
├── compositeinput/
│   ├── compositeinput_connection_status.yaml  # plug / unplug composite cable
│   ├── compositeinput_signal_status.yaml      # set signal state (STABLE, NO_SIGNAL, …)
│   └── compositeinput_video_mode.yaml         # report detected video mode change
├── deepsleep/
│   ├── deepsleep_trigger.yaml                 # simulate wakeup event (RCU_BT, LAN, CEC, …)
│   └── deepsleep_simulate_error.yaml          # inject error into sleep sequence
├── hdmicec/
│   ├── hdmicec_device_add.yaml                # add device to CEC network
│   ├── hdmicec_device_remove.yaml             # remove device from CEC network
│   ├── hdmicec_device_status.yaml             # update power/fault state of a device
│   ├── hdmicec_device_bus_status.yaml         # set bus to idle or busy
│   ├── hdmicec_device_print.yaml              # dump CEC device map to stub log
│   ├── hdmicec_device_cec_message.yaml        # send named CEC opcode message
│   ├── hdmicec_device_cec_message_userdef.yaml# send raw byte CEC message
│   ├── hdmicec_device_config.yaml             # initialise CEC network (single device)
│   └── hdmicec_device_config_add_network.yaml # initialise full CEC network topology
├── hdmiinput/
│   ├── hdmiinput_connection_status.yaml       # plug / unplug HDMI source
│   ├── hdmiinput_signal_status.yaml           # set signal state (LOCKED, NO_SIGNAL, …)
│   ├── hdmiinput_hdcp_status.yaml             # set HDCP auth state and version
│   ├── hdmiinput_videoformat_change.yaml      # inject VIC video format change
│   ├── hdmiinput_vrr_status.yaml              # inject VRR (Variable Refresh Rate) event
│   ├── hdmiinput_aviinfo_frame.yaml           # inject AVI InfoFrame bytes
│   ├── hdmiinput_audioinfo_frame.yaml         # inject Audio InfoFrame bytes
│   ├── hdmiinput_drminfo_frame.yaml           # inject DRM (HDR) InfoFrame bytes
│   ├── hdmiinput_spdinfo_frame.yaml           # inject SPD InfoFrame bytes
│   └── hdmiinput_vendorspecificinfo_frame.yaml# inject Vendor Specific InfoFrame bytes
├── hdmioutput/
│   ├── hdmioutput_hotplug_state.yaml          # assert / deassert HPD line
│   ├── hdmioutput_hdcp_status.yaml            # set HDCP auth state and version
│   ├── hdmioutput_frame_rate_changed.yaml     # signal frame rate change event
│   └── hdmioutput_edid_read.yaml              # inject EDID binary blob
├── motionsensor/
│   └── motionsensor_trigger.yaml              # fire MOTION or NO_MOTION event
└── thermalsensor/
    └── thermalsensor_trigger.yaml             # inject a temperature reading
```

---

## Field Type Annotations

Each field comment in the YAML files includes its type to make the template self-describing and to assist controller authors in constructing correct payloads:

| Annotation | Meaning |
|---|---|
| `integer` | Signed integer (e.g. port index) |
| `uint` | Unsigned integer (e.g. port_id, number_of_ports) |
| `uint64` | 64-bit unsigned integer (e.g. timestamp in ms) |
| `float` | Floating-point number (e.g. frame rate, temperature) |
| `boolean` | `true` or `false` |
| `string` | Free-form text |
| `string (enum)` | String constrained to a named set of values listed in the comment |
| `list[uint8]` | List of byte values as hex strings (e.g. InfoFrame / EDID payloads) |
| `list[string]` | List of string values (e.g. CEC message payload tokens) |
| `list` | Generic list (e.g. CEC device `children`) |

---

## Adding a New Command

1. Create a new YAML file in the appropriate `controlCommands/<module>/` subdirectory following the existing structure.
2. Set the `root_node` to match the vcomponent's registered name.
3. Set `command` to the handler name expected by the vcomponent.
4. Add each parameter under `params:` (or the appropriate sub-block) with an inline comment stating its **type**, valid range / enum values, and a brief description.
5. Copy the file into the `commands/` directory of the host-side controller module that will use it, or construct the equivalent dict inline in the controller code.
