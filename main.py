import zlib
import base64
import aiohttp
import requests
import webbrowser
from colored import fg
from colorama import Fore

from helpers import *

zold=fg('green')

# setting acceptable cosmetic types
ACCEPTED_COSMETIC_TYPES = [
    "AthenaCharacter",
    "AthenaDance",
    "AthenaPickaxe",
    "AthenaBackpack",
    "AthenaGlider",
    "AthenaItemWrap",
    "AthenaLoadingScreen",
    "AthenaMusicPack",
    "AthenaSkyDiveContrail",
    "BannerToken",
    "HomebaseBannerIcon",
    "SparksSong",
    "SparksGuitar",
    "SparksBass",
    "SparksDrums",
    "SparksKeyboard",
    "SparksMicrophone",
    "SparksAura",
    "VehicleCosmetics_Body",
    "VehicleCosmetics_Skin",
    "VehicleCosmetics_Wheel",
    "VehicleCosmetics_DriftTrail",
    "VehicleCosmetics_Booster",
    "JunoBuildingProp",
    "JunoBuildingSet",
    "CosmeticShoes"
]

class User:
    AccountId = ""
    UserName = ""
    AccessToken = ""

async def main():
    # Start the authentication process
    async with aiohttp.ClientSession() as http_session:
        access_token = await getAccessToken(http_session)

        # Create device code
        device_url, device_code = await createDeviceCode(http_session, access_token)
        #webbrowser.open(device_url, new=1)
        print(Fore.WHITE + "--> Please log in to your account by opening this link: " + Fore.LIGHTGREEN_EX + device_url)

        # Wait for device code completion
        auth_data = await waitForDeviceCodeComplete(http_session, device_code)

    # Update User class with new data
    User.AccountId = auth_data["account_id"]
    User.UserName = auth_data["displayName"]
    User.AccessToken = auth_data["access_token"]

    print(Fore.WHITE + f"\n--> Username: " + Fore.LIGHTBLUE_EX + User.UserName)

    # Requesting athena
    print(Fore.WHITE + "\n--> Requesting" + Fore.LIGHTMAGENTA_EX + " athena profile " + Fore.WHITE + "of " + Fore.LIGHTBLUE_EX + User.UserName)
    JSONDATA = QueryProfile(User.AccountId, "athena", User.AccessToken)

    # Requesting common_core
    print(Fore.WHITE + "--> Requesting" + Fore.LIGHTMAGENTA_EX + " common_core profile " + Fore.WHITE + "of " + Fore.LIGHTBLUE_EX + User.UserName)
    JSONDATA_CC = QueryProfile(User.AccountId, "common_core", User.AccessToken)

    # RMT packs
    packsDataReq = requests.get("https://api.fecooo.hu/fngg/offers")
    if packsDataReq.status_code == 200:
        PACKSDATA = packsDataReq.json()
    else:
        with open(getJsonPath("offergrants.json"), 'r') as json_file:
            PACKSDATA = json.load(json_file)

    # Built-in emotes
    builtinsDataReq = requests.get("https://api.fecooo.hu/fngg/builtins")
    if builtinsDataReq.status_code == 200:
        BUILTINS = builtinsDataReq.json()
    else:
        with open(getJsonPath("builtinemotes.json"), 'r') as json_file:
            BUILTINS = json.load(json_file)

    # getting the items from profile as objects
    print(Fore.WHITE + "\n--> Processing data")
    PROFILE_ITEMS = [JSONDATA['profileChanges'][0]['profile']['items'][i] for i in JSONDATA['profileChanges'][0]['profile']['items'].keys()]
    PROFILE_ITEMS_CC = [JSONDATA_CC['profileChanges'][0]['profile']['items'][i] for i in JSONDATA_CC['profileChanges'][0]['profile']['items'].keys()]

    # filtering items based on the ACCEPTED_COSMETIC_TYPES
    filteredItems = list(filter(lambda x: x['templateId'].split(":")[0] in ACCEPTED_COSMETIC_TYPES, PROFILE_ITEMS))
    filteredItems_cc = list(filter(lambda x: x['templateId'].split(":")[0] in ACCEPTED_COSMETIC_TYPES, PROFILE_ITEMS_CC))

    # cosmetic names from the objects
    cosmeticsNames = [i['templateId'].split(":")[1].lower() for i in filteredItems]
    builtIns = list(set([BUILTINS[i].lower() for i in BUILTINS.keys() if i.lower() in cosmeticsNames]))
    banners = [i['templateId'].split(":")[1].lower() for i in filteredItems_cc]

    packs = list(set([PACKSDATA[i] for i in PACKSDATA.keys() if i in cosmeticsNames]))

    cosmeticsNames += banners
    cosmeticsNames += builtIns

    # ----- WORKING WITH THE PREPARED DATA -----

    # requesting fngg ids
    print(Fore.WHITE + "\n--> Requesting data from " + Fore.LIGHTGREEN_EX + "https://fortnite.gg")
    fnggDataRequest = requests.get("https://fortnite.gg/api/items.json").json()
    fnggBundleData = requests.get("https://fortnite.gg/api/bundles.json").json()

    print(Fore.WHITE + "\n--> Processing data")
    FNGG_DATA = {i.lower(): int(fnggDataRequest[i]) for i in fnggDataRequest.keys()}
    ATHENA_CREATION_DATE = JSONDATA['profileChanges'][0]['profile']['created']

    ownedBundles = list(set([CheckBundle(i, fnggBundleData[i], cosmeticsNames, FNGG_DATA) for i in fnggBundleData.keys()]))
    ownedBundles = list(filter(lambda x: x is not None, ownedBundles))

    # getting the fngg ids of the items
    ints = sorted([i for i in ([FNGG_DATA[it] for it in cosmeticsNames if it in FNGG_DATA] + packs + ownedBundles) if i is not None])

    # ----- COMPRESSING DATA -----

    diff = list(map(lambda e: str(e[1] - ints[e[0] - 1]) if e[0] > 0 else str(e[1]), enumerate(ints)))

    compress = zlib.compressobj(
        level=-1, 
        method=zlib.DEFLATED, 
        wbits=-9,
        memLevel=zlib.DEF_MEM_LEVEL, 
        strategy=zlib.Z_DEFAULT_STRATEGY
    )
    compressed = compress.compress(f"{ATHENA_CREATION_DATE},{','.join(diff)}".encode())
    compressed += compress.flush()

    # encoding the compressed data to base64
    print(Fore.WHITE + "\n--> Encoding data")
    encoded = base64.urlsafe_b64encode(compressed).decode().rstrip("=")

    print(Fore.WHITE + "\n\n--> Your locker: " + Fore.LIGHTGREEN_EX + f"https://fortnite.gg/my-locker?items={encoded}" + Fore.WHITE)

    with open("locker.txt", "w", encoding="utf-8") as f:
        f.write(f"https://fortnite.gg/my-locker?items={encoded}")

    input()

if __name__ == "__main__":
    asyncio.run(main())