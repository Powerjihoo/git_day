import ctypes
import os
import sys
import time
import traceback
from pathlib import Path
from typing import List, Union

import numpy as np
import psutil

from utils.logger import logger


def add_path(upper_path_level: int = 1):
    if upper_path_level == 1:
        sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
    elif upper_path_level == 2:
        sys.path.append(
            os.path.dirname(
                os.path.abspath(
                    os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
                )
            )
        )
    else:
        return


def check_program_running(program_name):
    return program_name in (p.name() for p in psutil.process_iter())


def get_admin_previleges():

    try:
        if ctypes.windll.shell32.IsUserAnAdmin():
            return
        else:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
    except Exception:
        traceback.print_exc()


def get_local_ip_address():
    import socket

    return socket.gethostbyname(socket.gethostbyname(socket.gethostname()))


def validate_ip_address(ip_address):
    if ip_address is None:
        return False
    import re

    __number_exp = r"""
        (
                [0-9]
                |[1-9][0-9]
                |1[0-9]{2}
                |2[0-4][0-9]
                |25[0-5]
            )
            """
    __expression = f"^({__number_exp}.{__number_exp}.{__number_exp}.{__number_exp})$"
    ip_validation = re.compile(__expression, re.VERBOSE)

    return re.search(ip_validation, ip_address) != None


def validate_port_number(port_number):
    return False if type(port_number) is not int else 1023 < port_number < 65536


def convert_unixtime(date_time):
    """Convert datetime to unixtime"""
    import datetime

    unixtime = datetime.datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S,%f").timestamp()
    return unixtime * 1000


def convert_unixtime2datetime(unixtime: str):
    return time.strftime("%Y%m%d%H%M%S", time.localtime(unixtime))


def find_procs_by_name(name: str) -> List[str]:
    """Return a list of processes matching 'name'."""
    assert name, name
    ls = []
    for p in psutil.process_iter():
        name_, exe, cmdline = "", "", []
        try:
            name_ = p.name()
            cmdline = p.cmdline()
            exe = p.exe()
        except (psutil.AccessDenied, psutil.ZombieProcess):
            pass
        except psutil.NoSuchProcess:
            continue
        if name == name_ or cmdline[0] == name or os.path.basename(exe) == name:
            ls.append(name)
    return ls


def kill_process(message: str = "Process terminated unexpectedly"):
    logger.exception(message)
    pid = os.getpid()
    os.kill(pid, 2)


def save_temp_file(filename: str):
    """ Application of temporary directory """
    """ NOT IMPLEMENTED """
    import tempfile

    with tempfile.TemporaryDirectory() as fd:

        file_path = f"{fd}/{filename}"
        np.save_txt(file_path)
        ...


def save_temp_csv_file(prefix: str, data, header=None):
    from tempfile import NamedTemporaryFile

    with NamedTemporaryFile(delete=False, prefix=prefix, suffix=".csv") as tmp:
        temp_path = Path(tmp.name)
        np.savetxt(temp_path, data, delimiter=",", header=header, comments="")


def get_available_port(ports:List[int]=list(range(50100,60000)))->int:
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    for port in ports:
        try:
            s.bind(("",port))
            s.listen(1)
        except OSError:
            continue
        return s.getsockname()[1]
        
def get_open_port()->int:
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("",0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return port



def memory_usage()->str:
    """Return current process memory usage"""
    
    def __bytes2human(n):
        # http://code.activestate.com/recipes/578019
        # >>> bytes2human(10000)
        # '9.8K'
        # >>> bytes2human(100001221)
        # '95.4M'
        symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
        prefix = {}
        for i, s in enumerate(symbols):
            prefix[s] = 1 << (i + 1) * 10
        for s in reversed(symbols):
            if n >= prefix[s]:
                value = float(n) / prefix[s]
                return '%.1f%s' % (value, s)
        return "%sB" % n
    
    p = psutil.Process()
    __memory_info = p.memory_info()
    rss = __memory_info.rss
    vms = __memory_info.vms
    result = f"PID: {p.pid} | Memory usage: {__bytes2human(rss)}, Memory usage(virtual): {__bytes2human(vms)}"
    return result
