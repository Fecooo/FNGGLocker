import os
import sys
import json
import asyncio
import requests

# def GenerateBearerToken(authorization_code: str) -> object:
#     reqUrl = "https://account-public-service-prod.ol.epicgames.com/account/api/oauth/token"

#     headersList = {
#         "Content-Type": "application/x-www-form-urlencoded",
#         "Authorization": "basic ZWM2ODRiOGM2ODdmNDc5ZmFkZWEzY2IyYWQ4M2Y1YzY6ZTFmMzFjMjExZjI4NDEzMTg2MjYyZDM3YTEzZmM4NGQ=" 
#     }

#     payload = f"grant_type=authorization_code&code={authorization_code}"

#     response = requests.post(reqUrl, data=payload,  headers=headersList)

#     return response.json()

def QueryProfile(accountId: str, profileId: str, bearer: str) -> object:
    reqUrl = f"https://fortnite-public-service-prod11.ol.epicgames.com/fortnite/api/game/v2/profile/{accountId}/client/QueryProfile?profileId={profileId}"

    headersList = {
        "Authorization": f"bearer {bearer}",
        "Content-Type": "application/json" 
    }

    payload = json.dumps({})

    response = requests.post(reqUrl, data=payload,  headers=headersList)

    return response.json()

def CheckBundle(bundleId, data, profileItems, fnggItems) -> int:
    countOfShould = len(data['items'])
    countOfActual = 0

    for i in data['items']:
        if type(i) is not bool and i.lower() in profileItems:
            countOfActual += 1

    if countOfShould == countOfActual:
        return fnggItems[bundleId.lower()]
    else:
        return None


def getJsonPath(filename):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, filename)

    return os.path.join(os.path.dirname(__file__), filename)



# DEVICE CODE AUTH (https://github.com/xMistt/DeviceAuthGenerator)

SWITCH_TOKEN = "OThmN2U0MmMyZTNhNGY4NmE3NGViNDNmYmI0MWVkMzk6MGEyNDQ5YTItMDAxYS00NTFlLWFmZWMtM2U4MTI5MDFjNGQ3"

async def getAccessToken(http_session) -> str:
    async with http_session.request(
        method="POST",
        url="https://account-public-service-prod.ol.epicgames.com/account/api/oauth/token",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"basic {SWITCH_TOKEN}",
        },
        data={
            "grant_type": "client_credentials",
        },
    ) as request:
        data = await request.json()

    return data["access_token"]

async def createDeviceCode(http_session, access_token) -> tuple:
    async with http_session.request(
        method="POST",
        url="https://account-public-service-prod03.ol.epicgames.com/account/api/oauth/deviceAuthorization",
        headers={
            "Authorization": f"bearer {access_token}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    ) as request:
        data = await request.json()

    return data["verification_uri_complete"], data["device_code"]

async def waitForDeviceCodeComplete(http_session, code) -> dict:
    while True:
        async with http_session.request(
            method="POST",
            url="https://account-public-service-prod03.ol.epicgames.com/account/api/oauth/token",
            headers={
                "Authorization": f"basic {SWITCH_TOKEN}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "device_code", "device_code": code},
        ) as request:
            if request.status == 200:
                auth_data = await request.json()
                break
            else:
                pass

            await asyncio.sleep(3)

    return auth_data