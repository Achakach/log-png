import argparse
import os


def generate_nested_huawei_log(router_name: str = "TUC-TYB91G01HWLEFC303-CPLEF03", filename: str = "") -> int:
    """
    Generate a Huawei VRP CLI log for a single NE where every command
    and every nested command set runs exactly once.

    Each nested command set enters system-view, does its work, then
    returns to user view before the next set begins.

    Huawei prompt hierarchy:
      <Router>                    (user view)
      [Router]                    (system view)
      [~Router]                   (system view, unsaved config)
      [*Router]                   (system view, alarm/fault)
      [Router-ospf-1]             (OSPF view)
      [Router-GigabitEthernet0/0/N] (interface view)
    """
    if not filename:
        filename = f"{router_name}.txt"
    SYSTEM_VIEW_MSG = "Enter system view, return user view with Ctrl+Z."

    lines: list[str] = []

    def write(prompt: str, cmd: str, output: list[str]):
        lines.append(f"{prompt} {cmd}")
        for out_line in output:
            lines.append(f"  {out_line}")
        lines.append("")

    def enter_system_view():
        lines.append(f"<{router_name}> system-view")
        lines.append(f"  {SYSTEM_VIEW_MSG}")
        lines.append("")

    def exit_system_view():
        lines.append(f"[{router_name}] quit")
        lines.append("")

    # ---- User-view commands (each runs once, standalone) ----
    user_commands = [
        ("display device", ["Slot  Type             State    Subslot  ", "1     S12708          Normal   0        ", "2     S12708          Normal   0        "]),
        ("display clock", ["2026-04-07 21:15:30+07:00", "Tuesday", "Time Zone : Bangkok"]),
        ("display version", ["Huawei Versatile Routing Platform Software", "VRP (R) software, Version 8.180 (S12700 V200R019C10SPC500)", f"HUAWEI {router_name} uptime is 45 days, 3 hours, 12 minutes"]),
        ("display ip interface brief", ["Interface                         IP Address/Mask      Physical   Protocol  ", "GigabitEthernet0/0/0              192.168.1.1/24       up         up        ", "GigabitEthernet0/0/1              10.10.1.1/30          up         up        ", "LoopBack0                         1.1.1.1/32            up         up(s)     "]),
        ("display ospf peer brief", ["", "          OSPF Process 1 with Router ID 1.1.1.1", "                  Neighbors ", " Area 0.0.0.0 interface 10.10.1.1(GigabitEthernet0/0/1)'s neighbors", "   Router ID: 2.2.2.2   Address: 10.10.1.2     State: Full"]),
        ("display arp table", ["IP ADDRESS      MAC ADDRESS     EXPIRE(M) TYPE  INTERFACE", "192.168.1.100   00e0-fc12-3456  18        D     GE0/0/0", "10.10.1.2       00e0-fc12-7890  15        D     GE0/0/1"]),
        ("display mac-address", ["MAC address table of slot 0:", "-------------------------------------------", "MAC Address    VLAN  Type      Interface            ", "00e0-fc12-3456 1     Dynamic   GE0/0/0              ", "00e0-fc12-7890 10    Dynamic   GE0/0/1              "]),
        ("display cpu-usage", ["CPU Usage : 12%", "CPU Utilization over last  5 seconds: 12%", "CPU Utilization over last  1 minute : 11%", "CPU Utilization over last  5 minutes: 10%"]),
        ("display memory-usage", ["Memory Usage : 35%", "Total Memory(KB)    : 4194304", "Used Memory(KB)     : 1468006", "Free Memory(KB)      : 2726298"]),
        ("ping 10.10.1.2", ["  PING 10.10.1.2: 56  data bytes, press CTRL_C to break", "    Reply from 10.10.1.2: bytes=56 Sequence=1 ttl=255 time=1 ms", "    Reply from 10.10.1.2: bytes=56 Sequence=2 ttl=255 time=1 ms", "    Reply from 10.10.1.2: bytes=56 Sequence=3 ttl=255 time=1 ms", "", "  --- 10.10.1.2 ping statistics ---", "    3 packet(s) transmitted, 3 packet(s) received, 0.00% packet loss"]),
        ("display ip routing-table | include 10.10", ["  10.10.1.0/30      Direct 0    0     10.10.1.1       GE0/0/1"]),
        ("display vlan | include common", ["1       common  enable   UT:GE0/0/0(U)   GE0/0/1(U)", "10      common  enable   TG:Eth-Trunk1(U)", "20      common  enable   UT:GE0/0/2(U)"]),
    ]

    for cmd_text, output in user_commands:
        write(f"<{router_name}>", cmd_text, output)

    # ---- System-view display commands (own session, each set returns to user view) ----
    sys_display_commands = [
        ("display current-configuration", ["#", f"sysname {router_name}", "#", "vlan batch 10 20 30", "stp mode rstp", "#"]),
        ("display ip routing-table", ["Route Flags: R - relay, D - download to fib", "-------------------------------------------", "Public routing table : Destinations : 15", "", "  Destination/Mask  Proto  Pre  Cost  NextHop         Interface", "  10.10.1.0/30      Direct 0    0     10.10.1.1       GE0/0/1", "  192.168.1.0/24    Direct 0    0     192.168.1.1     GE0/0/0"]),
        ("display vlan", ["The total number of vlans is : 3", "U: Up;   D: Down;   TG: Tagged;   UT: Untagged", "VLAN ID  Type    Status   Ports", "1       common  enable   UT:GE0/0/0(U)   GE0/0/1(U)", "10      common  enable   TG:Eth-Trunk1(U)", "20      common  enable   UT:GE0/0/2(U)"]),
        ("display interface brief", ["Interface         PHY   Protocol  InUti OutUti   Description", "GE0/0/0           up    up        0.01%  0.01%    To_LAN", "GE0/0/1           up    up        0.05%  0.03%    To_WAN", "LoopBack0         up    up(s)     0%     0%       LoopBack"]),
    ]

    enter_system_view()
    for cmd_text, output in sys_display_commands:
        write(f"[{router_name}]", cmd_text, output)
    exit_system_view()

    # ---- Interface sub-views (each interface = own system-view session) ----
    interface_configs = [
        (1, [
            ("display this", ["#", f"interface GigabitEthernet0/0/1", " description UPLINK_TO_SPINE", " ip address 10.10.1.1 255.255.255.252", " duplex full", " speed 10000", "#"]),
        ]),
        (2, [
            ("display this", ["#", f"interface GigabitEthernet0/0/2", " description TO_SWITCH_ACC_2", " ip address 10.1.2.1 255.255.255.0", " duplex full", " speed 1000", "#"]),
        ]),
        (20, [
            ("display this", ["#", f"interface GigabitEthernet0/0/20", " description TO_SWITCH_ACC_20", " ip address 10.1.20.1 255.255.255.0", " duplex full", " speed 1000", "#"]),
            ("shutdown", [f"Info: Interface GigabitEthernet0/0/20 is shutdown."]),
            ("undo shutdown", [f"Info: Interface GigabitEthernet0/0/20 is up."]),
            ("display this", ["#", f"interface GigabitEthernet0/0/20", " description TO_SWITCH_ACC_20", " ip address 10.1.20.1 255.255.255.0", " duplex full", " speed 1000", "#"]),
        ]),
        (22, [
            ("display this", ["#", f"interface GigabitEthernet0/0/22", " description TO_SWITCH_ACC_22", " ip address 10.1.22.1 255.255.255.0", " duplex full", " speed 1000", "#"]),
        ]),
        (29, [
            ("display this", ["#", f"interface GigabitEthernet0/0/29", " description TO_SWITCH_ACC_29", " ip address 10.1.29.1 255.255.255.0", " duplex full", " speed 1000", "#"]),
            ("shutdown", [f"Info: Interface GigabitEthernet0/0/29 is shutdown."]),
        ]),
        (31, [
            ("display this", ["#", f"interface GigabitEthernet0/0/31", " description TO_SWITCH_ACC_31", " ip address 10.1.31.1 255.255.255.0", " duplex full", " speed 1000", "#"]),
        ]),
        (35, [
            ("display this", ["#", f"interface GigabitEthernet0/0/35", " description TO_SWITCH_ACC_35", " ip address 10.1.35.1 255.255.255.0", " duplex full", " speed 1000", "#"]),
        ]),
    ]

    # Config-changing commands that trigger the ~ (unsaved config) or * (alarm) indicator
    config_change_keywords = ("shutdown", "undo shutdown", "network", "silent-interface", "undo silent-interface")
    # Interfaces that end in alarm state (shutdown without undo) → show * indicator
    alarm_interfaces = {29}

    for intf_id, sub_cmds in interface_configs:
        enter_system_view()
        lines.append(f"[{router_name}] interface GigabitEthernet0/0/{intf_id}")
        lines.append("")
        has_change = False
        is_alarm = intf_id in alarm_interfaces
        for cmd_text, output in sub_cmds:
            # Prompt reflects state BEFORE this command is executed
            if has_change:
                prompt = f"[*{router_name}-GigabitEthernet0/0/{intf_id}]" if is_alarm else f"[~{router_name}-GigabitEthernet0/0/{intf_id}]"
            else:
                prompt = f"[{router_name}-GigabitEthernet0/0/{intf_id}]"
            write(prompt, cmd_text, output)
            if any(kw in cmd_text for kw in config_change_keywords):
                has_change = True
        # quit from sub-view — prompt reflects current state
        if has_change:
            sub_quit_prompt = f"[*{router_name}-GigabitEthernet0/0/{intf_id}]" if is_alarm else f"[~{router_name}-GigabitEthernet0/0/{intf_id}]"
        else:
            sub_quit_prompt = f"[{router_name}-GigabitEthernet0/0/{intf_id}]"
        lines.append(f"{sub_quit_prompt} quit")
        lines.append("")
        if has_change:
            sys_quit_prompt = f"[*{router_name}]" if is_alarm else f"[~{router_name}]"
        else:
            sys_quit_prompt = f"[{router_name}]"
        lines.append(f"{sys_quit_prompt} quit")
        lines.append("")
        lines.append("")

    # ---- OSPF sub-view (own system-view session) ----
    ospf_sub_cmds = [
        ("display this", ["#", "ospf 1", " area 0.0.0.0", "  network 10.1.0.0 0.0.255.255", "  silent-interface all", "#"]),
        ("network 172.16.0.0 0.0.255.255 area 0", ["Info: Network segment configured."]),
        ("silent-interface all", ["Warning: All interfaces are silent."]),
        ("undo silent-interface all", ["Info: All interfaces are not silent."]),
    ]

    enter_system_view()
    lines.append(f"[{router_name}] ospf 1")
    lines.append("")
    has_change = False
    for cmd_text, output in ospf_sub_cmds:
        # Prompt reflects state BEFORE this command is executed
        prompt = f"[~{router_name}-ospf-1]" if has_change else f"[{router_name}-ospf-1]"
        write(prompt, cmd_text, output)
        if any(kw in cmd_text for kw in config_change_keywords):
            has_change = True
    # quit from OSPF view
    ospf_quit_prompt = f"[~{router_name}-ospf-1]" if has_change else f"[{router_name}-ospf-1]"
    lines.append(f"{ospf_quit_prompt} quit")
    lines.append("")
    lines.append(f"[~{router_name}] quit")
    lines.append("")

    # ---- Write to file ----
    with open(filename, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")

    print(f"Created {filename} ({len(lines)} lines)")
    return len(lines)


if __name__ == "__main__":
    DEVICES = [
        "TUC-TYB91G01HWLEFC303-CPLEF03",
        "TUC-TYB91G01HWLEFC303-CPLEF04",
    ]
    parser = argparse.ArgumentParser(description="Generate mock Huawei VRP nested log file(s)")
    parser.add_argument("-d", "--devices", nargs="*", default=DEVICES,
                        help="Device names to generate logs for (default: test devices)")
    parser.add_argument("-o", "--output-dir", default="logs",
                        help="Output directory for log files (default: logs/)")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    for device in args.devices:
        filepath = os.path.join(args.output_dir, f"{device}.txt")
        generate_nested_huawei_log(router_name=device, filename=filepath)