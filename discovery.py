import sys
import time
import tomli_w

from roonapi import RoonApi, RoonDiscovery

running_mode = sys.argv[1].strip()

#print(f"running_mode is {running_mode}")

if running_mode == "L":
    appinfo = {
        "extension_id": "roon_cad_local",
        "display_name": "Python program to display cover art on a local display",
        "display_version": "1.0.0",
        "publisher": "jason-a69",
        "email": "email@yahoo.co.uk",
    }
elif running_mode == "P":
    appinfo = {
        "extension_id": "roon_cad_pico",
        "display_name": "Python program to display cover art on a Pi Pico display",
        "display_version": "1.0.0",
        "publisher": "jason-a69",
        "email": "email@yahoo.co.uk",
    }

def authorise_extension():

    discover = RoonDiscovery(None)
    time.sleep(3)

    discovered_cores = discover.all()
    discover.stop()
    
    if not discovered_cores:
        print("[-] Error: No Roon Core found. Are you on the same Wi-Fi/LAN?")
        return

    core_ip, core_port = discovered_cores[0]
    print(f"[+] Found Core at {core_ip}:{core_port}")

    print("Waiting for you to enable the extension in Roon...")

    api = RoonApi(
        appinfo,
        token=None,
        host=core_ip,
        port=core_port,
        blocking_init=False
    )

    # Poll until the user hits "Enable" in the Roon app
    while not api.token:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            print("\n[-] Cancelled by user.")
            api.stop()
            return

    api.stop()

    print("Received authorisation")
    print(api.host)
    print(api.core_name)
    print(api.core_id)

    config_data = {
        "server": {
        "host": api.host,
        "core_name": api.core_name,
        "core_id": api.core_id,
        "token": api.token
        }
    }

    print(f"config_data is {config_data}")

    with open("/etc/roon/config.toml", "wb") as toml_file:
        tomli_w.dump(config_data, toml_file)

if __name__ == "__main__":
    authorise_extension()
