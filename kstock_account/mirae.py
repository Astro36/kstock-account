from datetime import datetime
import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from kstock_account.exceptions import LoginFailedException
from kstock_account.schemas import HeldCash, HeldCashEquivalent, HeldEquity, HeldGoldSpot


class MiraeAccount:
    def login(user_id: str, user_password: str):
        try:
            options = Options()
            options.add_argument("--headless=new")

            driver = webdriver.Edge(options=options, service=Service(EdgeChromiumDriverManager().install()))
            driver.get("https://securities.miraeasset.com/mw/login.do")

            driver.execute_script(f"document.querySelector('#usid').value = '{user_id}';")
            driver.execute_script(f"document.querySelector('#clt_ecp_pwd').value = '{user_password}';")
            driver.execute_script("doSubmit();")
            _ = WebDriverWait(driver, 5).until(
                lambda x: x.current_url == "https://securities.miraeasset.com/mw/main.do"
            )

            access_token = driver.get_cookie("MIREADW_D")["value"]
        except TimeoutException:
            raise LoginFailedException
        finally:
            driver.close()

        return MiraeAccount(access_token)

    def __init__(self, access_token) -> None:
        self.access_token = access_token

    def get_cash_assets(self) -> list[HeldCash]:
        r = requests.post(
            "https://securities.miraeasset.com/hkd/hkd1003/a11.json",
            data={"qry_tcd": "1"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            cookies={"MIREADW_D": self.access_token},
        )
        foreign_currencies = [
            HeldCash(
                account_number=self._prettify_account_number(row["acno"]),
                name=row["curr_cd"],
                currency=row["curr_cd"],
                exchange_rate=float(row["bas_exr"]),
                market_value=float(row["mnyo_abl_a"]) / float(row["bas_exr"]),
            )
            for row in r.json()["GRID01"]
        ]

        r = requests.post(
            "https://securities.miraeasset.com/hkd/hkd1003/a05.json",
            cookies={"MIREADW_D": self.access_token},
        )
        cash_equivalents = [
            HeldCashEquivalent(
                account_number=self._prettify_account_number(row["acno"]),
                name=row["rp_pd_nm"],
                currency=row["curr_cd"],
                exchange_rate=float(row["ea"]) / float(row["frc_ea"]),
                market_value=float(row["frc_ea"]),
                maturity_date=datetime.strptime(row["rpc_parg_dt"], "%Y%m%d").date(),
                entry_value=float(row["frc_rp_ctrt_a"]),
            )
            for row in r.json()["grid01"]
        ]

        return foreign_currencies + cash_equivalents

    def get_equity_assets(self) -> HeldEquity:
        r = requests.post(
            "https://securities.miraeasset.com/hkd/hkd1003/a03.json",
            data={"pd_tcd": "01"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            cookies={"MIREADW_D": self.access_token},
        )
        equities = [
            HeldEquity(
                account_number=self._prettify_account_number(row["admn_acno"]),
                name=row["itm_nm1"],
                currency=row["curr_cd"],
                exchange_rate=float(row["ea"]) / float(row["pitm_ea"]),
                market_value=float(row["pitm_ea"]),
                symbol=row["itm_no"],
                quantity=float(row["hldg_q"]),
                entry_value=float(row["pchs_a1"]),
            )
            for row in r.json()["grid01"]
        ]
        return equities

    def get_gold_spot_assets(self) -> HeldGoldSpot:
        r = requests.post(
            "https://securities.miraeasset.com/hkd/hkd1003/a03.json",
            data={"pd_tcd": "04"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            cookies={"MIREADW_D": self.access_token},
        )
        golds = [
            HeldGoldSpot(
                account_number=self._prettify_account_number(row["admn_acno"]),
                name=row["itm_nm1"],
                currency=row["curr_cd"],
                exchange_rate=float(row["ea"]) / float(row["pitm_ea"]),
                market_value=float(row["pitm_ea"]),
                symbol=row["itm_no"],
                quantity=float(row["hldg_q"]),
                entry_value=float(row["pchs_a1"]),
            )
            for row in r.json()["grid01"]
        ]
        return golds

    def _prettify_account_number(self, account_number) -> str:
        return account_number[0:3] + "-" + account_number[3:5] + "-" + account_number[5:]
