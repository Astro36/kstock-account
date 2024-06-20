import re
import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from stock_account.exceptions import LoginFailedException
from stock_account.schemas import HeldAsset, HeldCash, HeldEquity
import time


class SamsungAccount:
    def login(user_id: str, user_password: str):
        try:
            options = Options()
            # options.add_argument("--headless=new")
            options.add_argument(
                f"--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1 Edg/126.0.0.0"
            )

            driver = webdriver.Edge(options=options, service=Service(EdgeChromiumDriverManager().install()))
            driver.get("https://www.samsungpop.com/login/login.pop")

            driver.execute_script(f"document.querySelector('#inpCustomerUseridText').value = '{user_id}';")
            driver.execute_script("$.page.dummyText('frmLoginCustomer', 'customerUserid');")

            driver.execute_script("tk.onKeyboard(document.querySelector('#customerPasswd'));")
            _ = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//img[@alt='q']")))
            time.sleep(1)
            driver.execute_script(
                f"""
                const pressKey = (char) => document.querySelector('img[alt="' + char + '"]').parentNode.parentNode.onmousedown();
                for (const char of '{user_password}') {{
                    if (char == '!') {{ pressKey('특수키');pressKey('느낌표');pressKey('특수키') }}
                    else if (char == '?') {{ pressKey('특수키');pressKey('물음표');pressKey('특수키') }}
                    else if (char == '.') {{ pressKey('특수키');pressKey('마침표');pressKey('특수키') }}
                    else pressKey(char)
                }}
                pressKey('입력완료');
                """
            )

            driver.execute_script("document.querySelector('#btnLogin').click();")
            _ = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "layerLoginCompleteClose")))

            access_token = driver.get_cookie("JSESSIONID")["value"]

            # while True:
            #     pass
        except TimeoutException:
            raise LoginFailedException
        finally:
            driver.close()

        return SamsungAccount(access_token)

    def __init__(self, access_token) -> None:
        self.access_token = access_token

    def get_assets(self) -> list[HeldAsset]:
        r = requests.post(
            "https://www.samsungpop.com/ux/kor/banking/balance/general/getInfoForJongMokData.do",
            data={"ACNT_N_BLNC_DISP_CODE": "2", "A_INTS_N_BLNC_DISP_CODE": "2"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            cookies={"JSESSIONID": self.access_token},
        )
        assets = []
        for row in r.json()["result"]["outRec2"]:
            if row["STND_PRDT_CLSN_CODE"] == "A1011":  # 해외주식
                quantity = self._parse_padded_number(row["DCPN_BLNC_QNTY"])
                market_value = float(row["A_STCK_AVG_PRIC_CTNT"]) * quantity
                symbol = row["ISCD"].strip()
                currency = "USD"
                if ".T" in currency:
                    currency = "JPY"
                elif ".DE" in currency:
                    currency = "EUR"
                assets.append(
                    HeldEquity(
                        account_number=self._prettify_account_number(row["ACNT_NO"].strip()),
                        name=row["ISUS_NAME"].strip(),
                        currency=currency,
                        exchange_rate=self._parse_padded_number(row["A_VLTN_AMNT21"]) / market_value,
                        market_value=market_value,
                        symbol=symbol,
                        quantity=quantity,
                        entry_value=float(row["A_LTR_BU_UNIT_PRIC"]) * quantity,
                    )
                )
        return assets

    def _prettify_account_number(self, account_number: str) -> str:
        return account_number[:-2] + "-" + account_number[-2:]

    def _parse_padded_number(self, number: str) -> float:
        return float(re.sub("^0*|0*$", "", number) + "0")
