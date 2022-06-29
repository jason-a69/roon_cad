import time

from roonapi import RoonApi, RoonDiscovery

appinfo = {
    "extension_id": "roon_ca_sense",
    "display_name": "Python program to display cover art on a sense hat",
    "display_version": "1.0.0",
    "publisher": "jason-a69",
    "email": "email@yahoo.co.uk",
}

discover = RoonDiscovery(None)
servers = discover.all()

print("Shutdown discovery")
discover.stop()

print("Found the following servers")
print(servers)
apis = [RoonApi(appinfo, None, server[0], server[1], False) for server in servers]

auth_api = []
while len(auth_api) == 0:
    print("Waiting for authorisation")
    time.sleep(1)
    auth_api = [api for api in apis if api.token is not None]

api = auth_api[0]

print("Got authorisation")
print(api.host)
print(api.core_name)
print(api.core_id)

print("Shutdown apis")
for api in apis:
    api.stop()

# This is what we need to reconnect
core_id = api.core_id
token = api.token

with open("/etc/roon/my_core_id_file", "w") as f:
    f.write(api.core_id)
with open("/etc/roon/my_token_file", "w") as f:
    f.write(api.token)
