import uuid
import requests
import logging

from keys import FLW_TEST_KEY

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

def generate_payment_reference() -> str:
    reference = str(uuid.uuid4())
    return reference


async def generate_payment_link(payment_reference:str, amount:str) -> str:
    # POST
    URL = "https://api.flutterwave.com/v3/payments"
    HEADERS = {
        "Authorization": f"Bearer {FLW_TEST_KEY}",
        "Content-Type": "application/json",
        "Accept": "*/*",
        "Accept-Encoding": "gzip,deflate,br",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.90 Safari/537.36",
        }
    PAYLOAD = {
        "amount":amount,
        "tx_ref": payment_reference,
        "customer": {
        "email": "vipforexmonster@gmail.com",
        "phone_number": "",
        "name": ""
        },
        "currency":"UGX",
        "redirect_url":"https://kabokisi.com",
        "customization": {
            "title": "Forex Monsters",
            "logo": ""
        }
    }
    try:
        response = requests.post(URL,headers=HEADERS,json=PAYLOAD)
        status_code = response.status_code
        # logger.info(response.headers)
        if status_code == 200:
            result = response.json()
            payment_url = result["data"]["link"]
            return payment_url
        else:
            # logger.info(response.json())
            response.raise_for_status()
            return "https://google.com"
    except requests.exceptions.RequestException as err:
        logger.error(err)
        return "https://google.com"
    
async def verify_payment(payment_reference):
    # GET
    URL = f"https://api.flutterwave.com/v3/transactions/verify_by_reference?tx_ref={payment_reference}"
    HEADERS = {
        "Authorization": f"Bearer {FLW_TEST_KEY}",
        "Content-Type": "application/json",
        "Accept": "*/*",
        "Accept-Encoding": "gzip,deflate,br",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.90 Safari/537.36",
        }
    try:
        response = requests.get(URL,headers=HEADERS)
        status_code = response.status_code
        logger.info(response.headers)
        if status_code == 200:
            result = response.json()
            # successful, failed, pending
            status = result["data"]["status"]
            return status
        else:
            logger.info(response.json())
            response.raise_for_status()
    except requests.exceptions.RequestException as err:
        logger.error(err)
        return "wrong"
    