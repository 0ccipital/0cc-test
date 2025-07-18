## [Switch: Flex 2.5G PoE](https://store.ui.com/us/en/category/all-switching/products/usw-flex-2-5g-8-poe)

## [Power: poe++ 60w adapter](https://store.ui.com/us/en/category/accessories-poe-power/collections/pro-store-poe-and-power-adapters/products/uacc-poe-plus-plus-10g?variant=uacc-poeplusplus-10g) 
### (between server and 2.5gbe switch 10gbe port)

# #1
# Complete High-Speed Home Network Upgrade Guide (Updated)

## Phase 1: Purchase Equipment

**Buy:**
- UniFi Flex 2.5G PoE switch (USW-Flex-2.5G-8-PoE) - $199
- Raspberry Pi 4 (for backup access)
- MicroSD card for Pi
- Ethernet cables as needed (Cat6A recommended for 2.5GbE+)

## Phase 2: Physical Setup

**Connections:**
1. **Server motherboard 1GbE port** → Raspberry Pi ethernet port
2. **Server 10GbE Port 1** → Switch 10GbE port
3. **Server 10GbE Port 2** → Express 7 2.5GbE LAN port
4. **Access points** → Switch PoE ports (UAP-AC-LR, U6-IW)
5. **Other wired devices** → Remaining switch 2.5GbE ports
6. **Express 7 WAN port** → Internet (unchanged)
7. **Raspberry Pi WiFi** → Express 7 WiFi network

## Phase 3: Raspberry Pi Setup

**Install and configure Pi:**
1. Flash Raspberry Pi OS to SD card
2. Enable SSH in boot config
3. Connect Pi to Express 7 WiFi network
4. Configure static IP on ethernet interface for server connection

**Pi network configuration:**
```bash
# Configure static IP for server connection
sudo nano /etc/dhcpcd.conf
# Add:
interface eth0
static ip_address=192.168.100.1/24
static routers=192.168.100.1
```

**Install backup access tools:**
```bash
sudo apt update
sudo apt install openssh-server tightvncserver nginx
```

## Phase 4: Unraid Configuration

**Enable virtualization:**
1. Settings → VM Manager → Enable VMs: Yes
2. Settings → VM Manager → Enable VFIO: Yes
3. Reboot

**Configure VFIO passthrough:**
1. Tools → System Devices → Find dual 10GbE NIC
2. Bind both ports to VFIO at boot
3. Reboot (removes NIC from Unraid's direct control)

**Configure motherboard NIC for Pi connection:**
1. Settings → Network Settings
2. Set motherboard NIC to static IP: 192.168.100.2/24
3. No gateway needed (local connection only)

**Create virtual bridge:**
1. Settings → Network Settings → Create bridge (br0)
2. Assign static IP on high-speed network segment
3. Leave bridge members empty initially

## Phase 5: pfSense VM Setup

**Create VM:**
1. VMs tab → Add VM → Linux
2. CPU: 2-4 dedicated cores, RAM: 2-4GB
3. Network: Connect to br0 bridge
4. PCI Devices: Add both 10GbE ports from VFIO list
5. Install pfSense from ISO

**Configure pfSense:**
1. **WAN interface:** 10GbE Port 2 (to Express 7)
2. **LAN interface:** 10GbE Port 1 (to switch)
3. **Routing mode:** Pure routing (no DHCP, no firewall)
4. **Bridge/route:** Include Unraid host traffic via br0
5. **Gateway:** Point to Express 7's IP

## Phase 6: Network Configuration

**Unraid routing:**
1. Settings → Network Settings → Set gateway to pfSense VM IP
2. Configure Unraid to route high-speed traffic through br0
3. Motherboard NIC remains for Pi backup access

**Express 7 settings:**
1. Remains DHCP server for all devices
2. Continues as internet gateway
3. Provides WiFi coverage
4. No configuration changes needed

## Phase 7: Backup Access Configuration

**Configure Pi for server access:**
```bash
# Set up port forwarding for Unraid web interface
sudo nano /etc/nginx/sites-available/unraid-proxy
# Add nginx config to proxy Unraid web interface

# Set up SSH tunnel script
nano ~/tunnel-to-server.sh
#!/bin/bash
ssh -L 8080:192.168.100.2:80 -N pi@localhost &
```

**Test backup access:**
1. Connect your device to Express 7 WiFi
2. SSH to Pi: `ssh pi@pi-wifi-ip`
3. From Pi, access server: `ssh root@192.168.100.2`
4. Or browse to Unraid: `http://192.168.100.2`

## Phase 8: Testing & Verification

**Test normal operation:**
1. Verify internet access from all devices
2. Test file transfers to server (should see 2.5GbE+ speeds)
3. Confirm multiple simultaneous transfers work

**Test failover scenarios:**

### Scenario 1: pfSense VM Failure
**Access method:**
1. Connect device to Express 7 WiFi
2. SSH to Pi: `ssh pi@pi-wifi-ip`
3. From Pi, access Unraid web interface: `http://192.168.100.2`
4. Or SSH to server: `ssh root@192.168.100.2`

### Scenario 2: Complete Server Failure
**Fallback:**
1. Express 7 WiFi still provides internet access
2. Other household members unaffected
3. Wired devices on switch lose connectivity

### Scenario 3: Express 7 Failure
**Result:**
1. High-speed wired network continues locally
2. No internet access until Express 7 restored
3. Pi backup access unavailable

## Final Result

**Normal Performance:**
- Device-to-device on switch: 2.5GbE
- Multiple devices to server: Each gets 2.5GbE simultaneously
- Server to wireless: 2.5GbE (Express 7 limitation)
- Access points: 2.5GbE each (major upgrade from shared 1GbE)

**Backup Access:**
- Pi provides independent path to server management
- Works when pfSense VM fails
- Accessible via Express 7 WiFi from any device
- Can access Unraid web interface, SSH, file shares, etc.

**Reliability:**
- Server failure: Express 7 maintains internet + WiFi
- pfSense failure: Pi provides server access + Express 7 WiFi works
- Express 7 failure: High-speed wired network continues locally
---
---
---
---
---
---
---
---
---
---
---
---
---
------
---
---
---
---
---
---
# #2
---
---
---
---
---
---
------
---
---
---
---
---
---
---
---
---
---
---
---
---


# Network Topology Diagram

## Internet & Core Infrastructure
```
Internet
   |
   | (WAN - 10GbE)
   |
┌──▼──────────────────┐
│  UniFi Express 7    │ ◄── Main Gateway + WiFi AP
│  (Gateway/WiFi AP)  │     DHCP Server
└──┬──────────────────┘
   │ (2.5GbE LAN - ONLY PORT)
   │
   │
   │ ┌─────────────────────────────────────────┐
   │ │              Server                     │
   │ │  ┌─────────────────────────────────┐    │
   │ │  │         pfSense VM              │    │
   │ │  │    (Routing between networks)   │    │
   │ │  └─────────────────────────────────┘    │
   │ │                 │                       │
   │ │                 │ (Virtual Bridge)      │
   │ │  ┌─────────────────────────────────┐    │
   │ │  │         Unraid Host             │    │
   │ │  │    (File Server/Plex/etc)       │    │
   │ │  └─────────────────────────────────┘    │
   │ │                                         │
   │ │  [1GbE Mgmt]  [10GbE Port 1] [10GbE Port 2] │
   │ │       │              │            │       │
   │ └───────┼──────────────┼────────────┼───────┘
   │         │              │            │
   └─────────┼──────────────┼────────────┘
             │              │
             │              │ (10GbE)
             │              │
             │              ▼
             │    ┌─────────────────────┐
             │    │  Flex 2.5G PoE      │
             └────┤  Switch             │ ◄── Management connection
                  │  (8x 2.5GbE PoE++)  │     (1GbE to 2.5GbE port)
                  │  (1x 10GbE)         │
                  └─┬─┬─┬─┬─┬─┬─┬─┬─────┘
                    │ │ │ │ │ │ │ │
                    │ │ │ │ │ │ │ └── Other 2.5GbE devices
                    │ │ │ │ │ │ └──── Other 2.5GbE devices  
                    │ │ │ │ │ └────── Other 2.5GbE devices
                    │ │ │ │ └──────── Other 2.5GbE devices
                    │ │ │ └────────── Other 2.5GbE devices
                    │ │ └──────────── Other 2.5GbE devices
                    │ └────────────── U6 In-Wall (U6-IW)
                    └──────────────── UAP-AC-LR
```

## Traffic Flow Summary

**High-Speed Path:**
```
Wired Device ◄──► Switch ◄──► pfSense VM ◄──► Express 7 ◄──► Internet
    (2.5GbE)      (10GbE)        (2.5GbE)
```

**Server Access:**
```
Any Device ◄──► Switch ◄──► pfSense VM ◄──► Unraid (via virtual bridge)
  (2.5GbE)       (10GbE)        (10GbE internal)
```

**Backup Management:**
```
Unraid ◄──► Switch ◄──► pfSense VM ◄──► Express 7
(1GbE)     (2.5GbE)      (2.5GbE)
```

## Key Features
- **Express 7:** DHCP server, internet gateway, WiFi AP (single 2.5GbE LAN port)
- **pfSense VM:** Pure routing between networks (no DHCP/firewall)
- **Switch:** 2.5GbE to all devices, PoE++ for access points
- **Server:** 1GbE management + 10GbE aggregate for file transfers
- **Failover:** Management access maintained through switch if pfSense fails
---
---
---
---
---
---
---
---
---
---
---
---
---
------
---
---
---
---
---
---
# #3
---
---
---
---
---
---
------
---
---
---
---
---
---
---
---
---
---
---
---
---
# Complete High-Speed Home Network Upgrade Guide

## Phase 1: Purchase Equipment

**Buy:**
- UniFi Flex 2.5G PoE switch (USW-Flex-2.5G-8-PoE) - $199
- Ethernet cables as needed (Cat6A recommended for 2.5GbE+)

## Phase 2: Physical Setup

**Connections:**
1. **Server motherboard 1GbE port** → Express 7 (backup management)
2. **Server 10GbE Port 1** → Switch 10GbE port
3. **Server 10GbE Port 2** → Express 7 2.5GbE LAN port
4. **Access points** → Switch PoE ports (UAP-AC-LR, U6-IW)
5. **Other wired devices** → Remaining switch 2.5GbE ports
6. **Express 7 WAN port** → Internet (unchanged)

## Phase 3: Unraid Configuration

**Enable virtualization:**
1. Settings → VM Manager → Enable VMs: Yes
2. Settings → VM Manager → Enable VFIO: Yes
3. Reboot

**Configure VFIO passthrough:**
1. Tools → System Devices → Find dual 10GbE NIC
2. Bind both ports to VFIO at boot
3. Reboot (removes NIC from Unraid's direct control)

**Create virtual bridge:**
1. Settings → Network Settings → Create bridge (br0)
2. Assign static IP on high-speed network segment
3. Leave bridge members empty initially

## Phase 4: pfSense VM Setup

**Create VM:**
1. VMs tab → Add VM → Linux
2. CPU: 2-4 dedicated cores, RAM: 2-4GB
3. Network: Connect to br0 bridge
4. PCI Devices: Add both 10GbE ports from VFIO list
5. Install pfSense from ISO

**Configure pfSense:**
1. **WAN interface:** 10GbE Port 2 (to Express 7)
2. **LAN interface:** 10GbE Port 1 (to switch)
3. **Routing mode:** Pure routing (no DHCP, no firewall)
4. **Bridge/route:** Include Unraid host traffic via br0
5. **Gateway:** Point to Express 7's IP

## Phase 5: Network Configuration

**Unraid routing:**
1. Settings → Network Settings → Set gateway to pfSense VM IP
2. Configure Unraid to route high-speed traffic through br0
3. Keep motherboard NIC for backup management

**Express 7 settings:**
1. Remains DHCP server for all devices
2. Continues as internet gateway
3. Provides WiFi coverage
4. No configuration changes needed

## Phase 6: Testing & Verification

**Test connectivity:**
1. Verify internet access from all devices
2. Test file transfers to server (should see 2.5GbE+ speeds)
3. Confirm multiple simultaneous transfers work
4. Test failover (server down = Express 7 WiFi still works)

## Final Result

**Performance:**
- Device-to-device on switch: 2.5GbE
- Multiple devices to server: Each gets 2.5GbE simultaneously
- Server to wireless: 2.5GbE (Express 7 limitation)
- Access points: 2.5GbE each (major upgrade from shared 1GbE)

**Reliability:**
- Server failure: Express 7 maintains internet + WiFi
- Express 7 failure: High-speed wired network continues locally
- Backup management via motherboard NIC
You're absolutely right! The Express 7 only has one 2.5GbE LAN port, which is already used by pfSense. Here's the corrected diagram: