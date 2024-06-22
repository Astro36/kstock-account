from datetime import date, datetime
import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from kstock_account.exceptions import LoginFailedException
from kstock_account.schemas import (
    HeldAsset,
    HeldCash,
    HeldCashEquivalent,
    HeldEquity,
    HeldGoldSpot,
    HoldingPeriodRecord,
)
from kstock_account.utils import weekrange


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
            _ = WebDriverWait(driver, 5).until(lambda x: x.current_url == "https://securities.miraeasset.com/mw/main.do")

            access_token = driver.get_cookie("MIREADW_D")["value"]
        except TimeoutException:
            raise LoginFailedException
        finally:
            driver.close()

        return MiraeAccount(access_token)

    def __init__(self, access_token) -> None:
        self.access_token = access_token

    def get_assets(self) -> list[HeldAsset]:
        return self.get_cash_assets() + self.get_equity_assets() + self.get_gold_spot_assets()

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

    def get_history(self, start_date: date, end_date: date = None) -> list[HoldingPeriodRecord]:
        if end_date is None:
            end_date = datetime.now().date()
        account_numbers = self._get_raw_account_numbers()
        history = [self._get_account_holding_period_record(target_start_date, target_end_date, account_numbers) for (target_start_date, target_end_date) in weekrange(start_date, end_date)]
        return history

    def get_holding_period_record(self, start_date: date, end_date: date = None) -> HoldingPeriodRecord:
        if end_date is None:
            end_date = datetime.now().date()
        account_numbers = self._get_raw_account_numbers()
        record = self._get_account_holding_period_record(start_date, end_date, account_numbers)
        return record

    def _get_raw_account_numbers(self) -> list[str]:
        r = requests.post(
            "https://securities.miraeasset.com/banking/getMyAccountListData.json",
            cookies={"MIREADW_D": self.access_token},
        )
        account_numbers = [row["acno"] for row in r.json()["grid01"]]
        return account_numbers

    def _get_account_holding_period_record(self, start_date: date, end_date: date, raw_account_numbers: list[str]) -> HoldingPeriodRecord:
        r = requests.post(
            "https://securities.miraeasset.com/hkd/hkd1005/a01.json",
            data={
                "ivst_pca_tp": "3",
                "bns_tlex_mtd_tp": "2",
                "strt_dt": start_date.strftime("%Y%m%d"),
                "end_dt": end_date.strftime("%Y%m%d"),
                "grid_cnt01": len(raw_account_numbers),
                **{f"GRID01_IN_acno_{i}": account_number for (i, account_number) in enumerate(raw_account_numbers)},
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            cookies={"MIREADW_D": self.access_token},
        )
        data = r.json()
        return HoldingPeriodRecord(
            start_date=start_date,
            end_date=end_date,
            initial_value=int(data["bss_ea"]),
            closing_value=int(data["eot_ea"]),
            cash_inflow=int(data["mnyi_a"]) + int(data["inq_a"]),
            cash_outflow=int(data["mnyo_a"]) + int(data["outq_a"]),
        )

    def _prettify_account_number(self, account_number) -> str:
        return account_number[0:3] + "-" + account_number[3:5] + "-" + account_number[5:]
