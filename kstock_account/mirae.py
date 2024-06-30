from datetime import date, datetime
from typing import Callable, Optional

import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait

from kstock_account.exceptions import LoginFailedException
from kstock_account.schemas import (
    HeldAsset,
    HeldCash,
    HeldCashEquivalent,
    HeldEquity,
    HeldGoldSpot,
    HoldingPeriodRecord,
)
from kstock_account.utils import convert_to_yfinance_symbol, create_headless_edge_webdriver, weekrange


class MiraeAccount:
    """Represents a Mirae Asset Securities account.

    Attributes:
        access_token (str): The access token for the account API.
    """

    @staticmethod
    def login(
        user_id: str,
        user_password: str,
        webdriver_fn: Callable[[], webdriver.Remote] = create_headless_edge_webdriver,
    ) -> "MiraeAccount":
        """Logs in to Mirae Asset Securities website using the provided user credentials.

        Args:
            user_id (str): The user ID for the Mirae Asset account.
            user_password (str): The password for the Mirae Asset account.
            webdriver_fn (Callable[[], webdriver.Remote], optional):
                A function that creates a webdriver instance. Defaults to
                `create_headless_edge_webdriver`.

        Returns:
            MiraeAccount: An instance of the MiraeAccount class with the
            access token.

        Raises:
            LoginFailedException: If the login attempt fails.
        """
        try:
            driver = webdriver_fn()
            driver.get("https://securities.miraeasset.com/mw/login.do")

            driver.execute_script(f"document.querySelector('#usid').value = '{user_id}';")
            driver.execute_script(f"document.querySelector('#clt_ecp_pwd').value = '{user_password}';")
            driver.execute_script("doSubmit();")
            _ = WebDriverWait(driver, 5).until(
                lambda x: x.current_url == "https://securities.miraeasset.com/mw/main.do",
            )

            if cookie := driver.get_cookie("MIREADW_D"):
                access_token = cookie["value"]
            else:
                raise LoginFailedException
        except TimeoutException:
            raise LoginFailedException
        finally:
            driver.close()
        return MiraeAccount(access_token)

    def __init__(self, access_token: str) -> None:
        """Constructs a MiraeAccount instance.

        Args:
            access_token (str): The access token for the account.
        """
        self.access_token = access_token

    def get_account_numbers(self) -> list[str]:
        """Returns the account numbers of the user's accounts.

        Returns:
            list[str]: A list of account numbers.
        """
        return [self._prettify_account_number(account_number) for account_number in self._get_raw_account_numbers()]

    def _get_raw_account_numbers(self) -> list[str]:
        r = requests.post(
            "https://securities.miraeasset.com/banking/getMyAccountListData.json",
            cookies={"MIREADW_D": self.access_token},
        )
        account_numbers = [row["acno"] for row in r.json()["grid01"]]
        return account_numbers

    def get_assets(self) -> list[HeldAsset]:
        """Returns the assets held by the user.

        The list includes cash assets, equities, and gold spots.

        Returns:
            list[HeldAsset]: A list of held assets.
        """
        return [*self.get_cash_assets(), *self.get_equity_assets(), *self.get_gold_spot_assets()]

    def get_cash_assets(self) -> list[HeldCash]:
        """Returns the cash assets held by the user.
        
        Returns:
            list[HeldCash]: A list of held cash assets.
        """
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

        return [*foreign_currencies, *cash_equivalents]

    def get_equity_assets(self) -> list[HeldEquity]:
        """Returns the equities held by the user.
        
        Returns:
            list[HeldEquity]: A list of held equities.
        """
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
                symbol=convert_to_yfinance_symbol(row["itm_no"]),
                quantity=float(row["hldg_q"]),
                entry_value=float(row["pchs_a1"]),
            )
            for row in r.json()["grid01"]
        ]
        return equities

    def get_gold_spot_assets(self) -> list[HeldGoldSpot]:
        """Returns the gold spots held by the user.
        
        Returns:
            list[HeldGoldSpot]: A list of held gold spots.
        """
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

    def get_history(self, start_date: date, end_date: Optional[date] = None) -> list[HoldingPeriodRecord]:
        """Returns the history of the weekly performance of the user's assets.

        Args:
            start_date (date): The start date of the history.
            end_date (Optional[date]): The end date of the history. Defaults to today.

        Returns:
            List[HoldingPeriodRecord]: The history of the weekly performance of the user's assets.
        """
        if end_date is None:
            end_date = datetime.now().date()
        account_numbers = self._get_raw_account_numbers()
        history = [
            self._get_account_holding_period_record(target_start_date, target_end_date, account_numbers)
            for (target_start_date, target_end_date) in weekrange(start_date, end_date)
        ]
        return history

    def get_holding_period_record(self, start_date: date, end_date: Optional[date] = None) -> HoldingPeriodRecord:
        """Returns the record of PnL of the user's assets.
        
        Args:
            start_date (date): The start date of the history.
            end_date (Optional[date]): The end date of the history. Defaults to today.
        
        Returns:
            HoldingPeriodRecord: The record of PnL of the user's assets.
        """
        if end_date is None:
            end_date = datetime.now().date()
        account_numbers = self._get_raw_account_numbers()
        record = self._get_account_holding_period_record(start_date, end_date, account_numbers)
        return record

    def _get_account_holding_period_record(
        self,
        start_date: date,
        end_date: date,
        raw_account_numbers: list[str],
    ) -> HoldingPeriodRecord:
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

    def _prettify_account_number(self, account_number: str) -> str:
        return account_number[0:3] + "-" + account_number[3:5] + "-" + account_number[5:]
