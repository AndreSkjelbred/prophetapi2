from fastapi import FastAPI, Query ,HTTPException , Request
from fastapi.middleware.cors import CORSMiddleware
from icecream import ic
import base64, json 
from web3 import Web3
from hexbytes import HexBytes
from eth_account.messages import encode_defunct
import uuid
from fastapi import Response
from pymongo import MongoClient

import requests

Cluser = MongoClient('mongodb+srv://ant:7KDcdOtZC5ZlgQE2@cluster0.zw2lr.mongodb.net')


UserData={"address": ""
    "nonce": ""
    "signature": ""
    "telegram_id": 0
    "username": "" }
    
async def checkProphetBalance(address):
    headers = {'accept': 'application/json','content-type': 'application/json',}

    json_data = {'id': 1,'jsonrpc': '2.0','method': 'alchemy_getTokenBalances','params': [address,[address],],}
    try:
        response = requests.post('https://eth-mainnet.g.alchemy.com/v2/GeSLUXHRFHWjao3wGiYYlZM6Dq04datp', headers=headers, json=json_data)
    except:
        return False, 0, "ERROR_1"
    if '"contractAddress":"0xa9fbcc25435ad713a9468d8c89dd7baae8914e3a"'in response.text:
        balance = int(response.json()["result"]["tokenBalances"][0]["tokenBalance"], 16) / 1000000000000000000
        if balance >= 3000:
            return True, balance, "TIER_3"
        elif balance >= 2000:
            return True, balance, "TIER_2"
        elif balance >= 1000:
            return True, balance, "TIER_1"
        else:
            return True, balance, "NO_ACCESS"
    else:
        return False, 0, "ERROR_2"


async def Eth_check(address,sign,token,username):

    w3 = Web3(Web3.HTTPProvider(""))
    msg = f"""We need you to connect your Metamask account in order to access ProphetBots.
By signing this message we can confirm ownership of this wallet.
Signing this message does not give ProphetBots access to your wallet.

Address: {address}
Telegram: {username}
Nonce: {token}

ProphetBots"""
    mesage= encode_defunct(text=msg)
    re_address = w3.eth.account.recover_message(mesage,signature=HexBytes(sign))
    if re_address.lower() == address.lower():
        return True
    else:
        return False
    

app = FastAPI()


@app.get("/verify")
async def read_root(data: str = Query(None)):
    decoded_bytes = base64.b64decode(data)
    decoded_string = decoded_bytes.decode('utf-8')

    Data = json.loads(decoded_string)
    print("Received request to /verify with data:", Data)
    if isinstance(Data, UserData):
        r = await Eth_check(Data['address'],Data['signature'],Data['nonce'],Data['username'])
        if r is True:
            bll , balance , status  = await checkProphetBalance(Data['address'])
            if bll is False:
                return {'meesage':True}
            UserDataID = Cluser['ProphetVerify']['telegram_user_db'].find_one({'telegram_id':int(Data['telegram_id'])})
            UserDataAddy = Cluser['ProphetVerify']['telegram_user_db'].find_one({'address':str(Data['address'])})

            if UserDataID != None and  UserDataAddy == None:
                if UserDataID['address'] == Data['address']:
                    return {'meesage':True}
                elif UserDataID['address'] != Data['address']:
                    Cluser['ProphetVerify']['telegram_user_db'].update_one({'telegram_id':int(Data['telegram_id'])},{'$set':{'address':Data['address']}})
                    return {'meesage':True}
                
            elif UserDataAddy and UserDataID == None:
                if UserDataAddy['telegram_id'] == Data['telegram_id']:
                    return {'meesage':True}
                elif UserDataAddy['telegram_id'] != Data['telegram_id']:
                    Cluser['ProphetVerify']['telegram_user_db'].update_one({'address':int(Data['address'])},{'$set':{'telegram_id':Data['telegram_id']}})
                    return {'meesage':True}

                
            elif UserDataAddy and UserDataID:
                if UserDataAddy == UserDataID:
                    if UserDataAddy['address'] != Data['address']:
                        Cluser['ProphetVerify']['telegram_user_db'].update_one({'address':str(Data['address'])},{'$set':{'address':Data['address']}})  
                        return {'meesage':True}
                
                elif UserDataAddy != UserDataID:
                    if UserDataID['address'] == Data['address']:
                        Cluser['ProphetVerify']['telegram_user_db'].delete_one({'telegram_id':int(Data['telegram_id'])})
                        Cluser['ProphetVerify']['telegram_user_db'].update_one({'address':str(Data['address'])},{'$set':{'telegram_id':Data['telegram_id']}})
                        return {'meesage':True}
                    
            elif UserDataAddy == None and UserDataID == None:
                Cluser['ProphetVerify']['telegram_user_db'].insert_one({'telegram_id':int(Data['telegram_id']),'address':str(Data['address'])})
        else:
            return {'meesage':False}


@app.get('/nonce', status_code=200)
async def return_nonce(response: Response):
    new_uuid = uuid.uuid4()
    response.headers['Token'] = str(new_uuid)
    response.headers['Access-Control-Expose-Headers'] = 'Token'
