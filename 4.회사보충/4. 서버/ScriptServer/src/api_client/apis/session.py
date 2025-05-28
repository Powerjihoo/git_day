# session.py

import datetime
import os
import pickle
from typing import Tuple

import requests
from requests.adapters import HTTPAdapter, Retry

from config import settings

# http://daplus.net/python-python-%EC%9A%94%EC%B2%AD-%EB%B0%8F-%EC%98%81%EA%B5%AC-%EC%84%B8%EC%85%98/


class APISession:
    """
    a class which handles and saves login sessions. It also keeps track of proxy settings.
    It does also maintine a cache-file for restoring session data from earlier script executions.
    """

    def __init__(
        self,
        host: str = settings.servers["ipcm-server"].host,
        port: str = settings.servers["ipcm-server"].port,
        login_usr=None,
        login_pwd=None,
        session_file_appendix="_session.dat",
        max_session_time_seconds=30 * 60,
        proxies=None,
        user_agent="Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1",
        force_login=False,
        is_apply_retry: bool = True,
        **kwargs,
    ):
        """
        save some information needed to login the session

        you'll have to provide 'loginTestString' which will be looked for in the
        responses html to make sure, you've properly been logged in

        'proxies' is of format { 'https' : 'https://user:pass@server:port', 'http' : ...
        'maxSessionTimeSeconds' will be used to determine when to re-login.
        """
        self.host = host
        self.port = port
        self.set_baseurl()
        self.proxies = proxies
        self.login_usr = login_usr
        self.login_pwd = login_pwd
        self.session_file = f"{self.host}_{self.port}{session_file_appendix}"
        self.user_agent = user_agent

        self.login(force_login, **kwargs)
        if is_apply_retry:
            self.apply_retry(3, 5, 1, (400, 403, 500, 503), is_https=False)

    def set_baseurl(self) -> None:
        self.baseurl = f"http://{self.host}:{self.port}"

    def login(self, force_login=False):
        """
        login to a session. Try to read last saved session from cache file. If this fails
        do proper login. If the last cache access was too old, also perform a proper login.
        Always updates session cache file.
        """
        try:
            was_read_from_cache = False
            if os.path.exists(self.session_file) and not force_login:
                time = self.modification_date(self.session_file)

                # only load if file less than 30 minutes old
                last_modification = (datetime.datetime.now() - time).seconds
                if last_modification < self.maxSessionTime:
                    with open(self.session_file, "rb") as f:
                        self.session = pickle.load(f)
                        was_read_from_cache = True
                        if self.debug:
                            print(
                                "loaded session from cache (last access %ds ago) "
                                % last_modification
                            )
            if not was_read_from_cache:
                self.session = requests.Session()
                self.session.headers.update({"user-agent": self.user_agent})

                if self.debug:
                    print("created new session with login")
                self.save_session_to_cache()
        except Exception:
            self.session = requests.session()

    def apply_retry(
        self,
        connect: int,
        read: int,
        backoff_factor: int,
        RETRY_STATUS: Tuple[int],
        is_https: bool = False,
    ) -> None:
        retry = Retry(
            total=connect + read,
            connect=connect,
            read=read,
            backoff_factor=backoff_factor,
            status_forcelist=RETRY_STATUS,
        )
        adapter = HTTPAdapter(max_retries=retry)
        if is_https:
            self.session.mount("https://", adapter)
        else:
            self.session.mount("http://", adapter)

    def save_session_to_cache(self):
        """
        save session to a cache file
        """
        # always save (to update timeout)
        with open(self.session_file, "wb") as f:
            pickle.dump(self.session, f)

    def request_get(self, url, **kwargs):
        """
        method: GET
        return the content of the url with respect to the session.
        """
        response = self.session.get(url, proxies=self.proxies, **kwargs)

        # the session has been updated on the server, so also update in cache
        self.save_session_to_cache()

        return response

    def request_post(
        self,
        url,
        data=None,
        **kwargs,
    ):
        """
        method: POST
        return the content of the url with respect to the session.
        """

        response = self.session.post(url, data=data, proxies=self.proxies, **kwargs)
        self.save_session_to_cache()
        return response

    def request_delete(
        self,
        url,
        **kwargs,
    ):
        """
        method: DELETE
        return the content of the url with respect to the session.
        """

        response = self.session.delete(url, proxies=self.proxies, **kwargs)
        self.save_session_to_cache()
        return response
