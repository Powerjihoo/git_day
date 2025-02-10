"""
이 모듈은 사용자 정의 스크립트를 관리하고 실행하는 기능을 제공합니다.
주요 클래스와 함수는 다음과 같습니다:

- CustomScriptManager: 사용자 정의 스크립트를 로드, 저장, 등록, 계산 및 관리하는 클래스입니다.
- CustomScript: 개별 사용자 정의 스크립트를 나타내는 클래스입니다.
- PostgreSQLConnector: PostgreSQL 데이터베이스와 연결하고 데이터를 로드 및 저장하는 클래스입니다.
- CanNotFindTagError: 요청된 태그를 찾을 수 없을 때 발생하는 예외입니다.

이 모듈은 PostgreSQL 데이터베이스에서 스크립트 설정을 로드하고, 스크립트를 실행하여 결과를 반환하며,
필요시 스크립트를 등록, 갱신 및 삭제하는 기능을 포함합니다.
"""

import copy
import re
import sys
import types
from queue import Empty as QueueEmpty

import numpy as np
import pandas as pd

from _protobuf.script_data_pb2 import ToIPCM
from api_client.apis.tagvalue import tagvalue_api
from api_server.models.calctags import _ScriptInfo, _ScriptOutputTags
from config import settings
from data_manager.models import _TagDataFromKafka
from dbinfo.tag_value import ScriptTagValueQueue
from utils.logger import logger
from utils.postgresql_conn import PostgreSQLConnector
from utils.scheme.singleton import SingletonInstance

from .models import ScriptInputTagData

EXCLUDE_LOCAL_VAR_NAMES = ["self", "Value", "np"]

script_tag_value_queue = ScriptTagValueQueue()


def get_last_data(tagname: str) -> float:
    """
    주어진 태그 이름에 해당하는 최신 데이터를 반환합니다.

    Args:
        tagname (str): 태그 이름.

    Returns:
        float: 태그에 해당하는 최신 데이터 값. 데이터가 없으면 NaN을 반환합니다.
    """
    res = tagvalue_api.get_current_value(tagnames=[tagname])
    data = res.json()
    if not data[tagname]:
        return np.nan
    else:
        return data[tagname]["value"]


def dict_to_string(dictionary):
    """
    딕셔너리를 문자열로 변환합니다. 각 키-값 쌍은 콤마로 구분됩니다.

    Args:
        dictionary (dict): 변환할 딕셔너리.

    Returns:
        str: 변환된 문자열.
    """
    return ", ".join([f"{key}: {value}" for key, value in dictionary.items()])


def get_self_vars_from_initialization_code(initialization_code):
    """
    초기화 코드에서 self.로 시작하는 변수를 추출합니다.

    Args:
        initialization_code (str): 초기화 코드.

    Returns:
        set: self.로 시작하는 변수들의 집합.
    """
    pattern = re.compile(r"self\.(\w+)")
    matches = pattern.findall(initialization_code)
    return set(matches)


def extract_expression_name(code_line):
    """
    코드 라인에서 변수 할당, 메서드 호출, 딕셔너리 할당 등의 표현식을 추출합니다.

    Args:
        code_line (str): 코드 라인.

    Returns:
        str: 추출된 표현식 이름. 없으면 None을 반환합니다.
    """
    # 변수 할당 패턴 (일반 변수 할당 및 self. 변수 할당)
    var_pattern = re.compile(r"((self\.)?\w+)\s*=\s*(.+)")
    # 메서드 호출 패턴 (점 기준으로 좌측 변수 추출)
    method_pattern = re.compile(r"((self\.)?\w+)\.\w+\(")
    # 딕셔너리 할당 패턴 (self를 포함한 경우)
    dict_pattern = re.compile(r"((self\.\w+)|(\w+))\['[^']+'\]\s*=\s*(.+)")

    # 일반 변수 할당
    var_match = var_pattern.match(code_line.strip())
    if var_match:
        return var_match.group(1)  # 변수 이름 반환

    # 메서드 호출
    method_match = method_pattern.search(code_line.strip())
    if method_match:
        return method_match.group(1)  # 좌측 변수만 반환

    # 딕셔너리 할당
    dict_match = dict_pattern.match(code_line.strip())
    if dict_match:
        return dict_match.group(1)  # 좌측 변수 반환

    return None


# ! FIXME: calc_interval에 따라 계산되도록 기능 추가 필요
class CustomScript:
    allowed_builtins = {"np": np}

    def __init__(
        self,
        script_id: str,
        script_name: str,
        initialization_code: str,
        calculation_code: str,
        input_tagnames: list[str],
        output_tags=list[dict],
        calc_interval: int = 1,
    ) -> None:
        """
        CustomScript 클래스의 생성자입니다.

        Args:
            script_id (str): 스크립트의 고유 ID.
            script_name (str): 스크립트의 이름.
            initialization_code (str): 초기화 코드.
            calculation_code (str): 계산 코드.
            input_tagnames (list[str]): 입력 태그 이름 목록.
            output_tags (list[dict]): 출력 태그 목록.
            calc_interval (int, optional): 계산 주기. 기본값은 1입니다.
        """
        self.script_id: str = script_id
        self.script_name: str = script_name
        self.initialization_code: str = initialization_code
        self._initializeation_code_var = {
            "self": self,
            "np": np,
            "get_last_data": get_last_data,
        }
        self.calculation_code: str = calculation_code
        self.output_code: str = None
        self.input_tagnames: list[str] = input_tagnames
        self._output_tags: list[dict] = output_tags
        self.calc_interval = calc_interval
        self._combined_code: str = None
        self.__create_output_code()
        self.__create_combine_code()
        self.execute_static_variables()
        self.compile_code()
        self.result_output = {}
        self.last_data = {}
        self.__create_last_data()
        self.last_calc_time = 0

    def __create_output_code(self) -> None:
        """
        출력 코드를 생성합니다.
        """
        _codes = []
        for output_tag in self._output_tags:
            _code = f"self.result_output['{output_tag.tagname}'] = {{'value': {output_tag.script}}}"
            _codes.append(_code)
        self.output_code = "\n".join(_codes)

    def __create_combine_code(self) -> None:
        """
        계산 코드와 출력 코드를 결합합니다.
        """
        self._combined_code = "\n".join([
            self.calculation_code,
            self.output_code,
            "None",
        ])
        
    def execute_static_variables(self) -> None:
        """
        초기화 코드를 실행합니다.
        """
        # FIXME: 객체 생성시가 아닌, 최초 계산시에 한번 실행하도록 수정 필요
        if self.initialization_code:
            exec(
                self.initialization_code,
                CustomScript.allowed_builtins,
                self._initializeation_code_var,
            )
        
    def compile_code(self) -> None:
        """
        결합된 코드를 컴파일합니다.
        """
        self.compiled_code = compile(
            source=self._combined_code, filename=str(self.script_id), mode="exec"
        )

    def __create_last_data(self) -> None:
        """
        마지막 데이터 구조를 생성합니다.
        """
        for tagname in self.input_tagnames:
            self.last_data[tagname] = ScriptInputTagData(
                timestamp=-1, value=np.nan, status_code=-1, tagname=tagname
            )
            
    def __repr__(self) -> str:
        """
        객체의 문자열 표현을 반환합니다.

        Returns:
            str: 객체의 문자열 표현.
        """
        return f"{self.__class__.__name__}({self.script_id}: {self.script_name})"

    def __get_exclude_variable_names(self) -> list[str]:
        """
        제외할 변수 이름 목록을 반환합니다.

        Returns:
            list[str]: 제외할 변수 이름 목록.
        """
        return [""].extend(list(self.allowed_builtins.keys()))

    def verify_code_rule(self) -> bool:
        """
        코드 규칙을 검증합니다.

        Returns:
            bool: 검증 결과.
        """
        # 사용불가 함수, 라이브러리 검증
        # 사용불가 변수명, 함수명 검증 (클래스 내부 속성, 메서드명 중복되지 않도록)
        # Code Syntax
        ...

    def update_last_data(self, tag_data_list: list[_TagDataFromKafka]) -> bool:
        """
        마지막 데이터를 업데이트합니다.

        Args:
            tag_data_list (list[_TagDataFromKafka]): 업데이트할 태그 데이터 목록.

        Returns:
            bool: 업데이트 성공 여부.
        """
        updated = False
        for tag_data in tag_data_list:
            input_tag_data: ScriptInputTagData = self.last_data[tag_data.tagname]

            if tag_data.timestamp == input_tag_data.timestamp:
                continue

            input_tag_data.update(
                timestamp=tag_data.timestamp,
                value=tag_data.value,
                status_code=tag_data.status_code,
            )
            updated = True
        return updated
    
    #calc.py
    def trace_execution(self, Value, specific_vars=None, line_number=None):
        """
        코드 실행을 추적합니다.

        Args:
            Value (dict): 실행 시 사용할 값.
            specific_vars (list[str], optional): 추적할 특정 변수 목록.
            line_number (int, optional): 추적할 특정 라인 번호.

        Returns:
            pd.DataFrame: 추적 결과 데이터프레임.
        """
        if specific_vars is None:
            specific_vars = []

        # Extract variables from the initialization code that belong to `self`
        self_vars_from_code = get_self_vars_from_initialization_code(
            self.initialization_code
        )

        # Split combined code into individual lines for tracing
        source_lines = self._combined_code.split("\n")
        calc_line_results = []
        recorded_lines = set()  # Set to track recorded line numbers

        def get_relevant_variables(local_vars):
            """
            Filters and returns relevant local variables excluding functions, types, and modules.
            Also includes relevant attributes from `self`.
            """
            filtered_vars = {
                var_name: var_value
                for var_name, var_value in local_vars.items()
                if not isinstance(
                    var_value, (types.FunctionType, type, types.ModuleType)
                )
                and var_name not in EXCLUDE_LOCAL_VAR_NAMES
            }

            # Include attributes from `self` if they are in the initialization code
            if "self" in local_vars:
                self_attrs = {
                    f"self.{attr}": getattr(local_vars["self"], attr)
                    for attr in dir(local_vars["self"])
                    if attr in self_vars_from_code
                    and not callable(getattr(local_vars["self"], attr))
                    and not attr.startswith("__")
                }
                filtered_vars.update(self_attrs)

            # Filter variables based on specific_vars if provided
            if specific_vars:
                relevant_vars = {
                    var_name: var_value
                    for var_name, var_value in filtered_vars.items()
                    if var_name in specific_vars
                }
            else:
                relevant_vars = filtered_vars

            # Always include `self.result_output`
            relevant_vars["self.result_output"] = local_vars[
                "self"
            ].result_output.copy()
            return relevant_vars

        def tracer(frame, event, arg):
            """
            Tracing function to capture variable states at each line of execution.
            """
            try:
                # Only trace lines from the script's combined code
                if frame.f_code.co_filename == str(self.script_id):
                    line_no = frame.f_lineno
                    source_line = source_lines[line_no - 1].strip()
                    local_vars = frame.f_locals.copy()

                    # Capture variables if the event is 'line' or 'return' and the line number matches
                    if (
                        event == "line"
                        and (line_number is None or line_no == line_number)
                    ) or event == "return":
                        calc_result_vars = get_relevant_variables(local_vars)

                        # Record the line if it hasn't been recorded yet
                        if line_no not in recorded_lines:
                            calc_line_result = [line_no, calc_result_vars, source_line]
                            calc_line_results.append(calc_line_result)
                            recorded_lines.add(line_no)

            except Exception as e:
                logger.error(e)
            return tracer

        # Set the tracer function
        sys.settrace(tracer)
        exec(
            self.compiled_code,
            CustomScript.allowed_builtins,
            self._initializeation_code_var | {"Value": Value},
        )
        sys.settrace(None)

        # Create a DataFrame from the collected trace results
        df = pd.DataFrame(calc_line_results, columns=["Line", "Variables", "Code"])

        # Annotate DataFrame with the result of the expressions
        for i in range(len(df)):
            expression_name = extract_expression_name(df.at[i, "Code"])
            if expression_name:
                next_variables = df.at[i + 1, "Variables"] if i + 1 < len(df) else ""
                variable_value = next_variables.get(expression_name)
                if variable_value is not None:
                    df.at[i, "Result"] = f"{expression_name}: {variable_value}"

        return df[df.Code != "None"]
    
    def update_result_output(self, script_data: dict):
        max_timestamp = max([tag_data.timestamp for tag_data in script_data.values()])
        for output_tag in self._output_tags:
            self.result_output[output_tag.tagname]["timestamp"] = max_timestamp
            self.result_output[output_tag.tagname]["status_code"] = 192
            
    def calc(self, script_data: dict) -> any:
        """
        계산을 수행합니다.

        Args:
            script_data (dict): 계산에 사용할 데이터.

        Returns:
            any: 계산 결과.
        """
        exec(
            self.compiled_code,
            CustomScript.allowed_builtins,
            self._initializeation_code_var | {"Value": script_data},
        )
        self.update_result_output(script_data)
        return self.result_output

    def debug_code(self, Value: dict, specific_vars=None, line_number=None) -> any:
        """
        디버그 코드를 실행합니다.

        Args:
            Value (dict): 실행 시 사용할 값.
            specific_vars (list[str], optional): 추적할 특정 변수 목록.
            line_number (int, optional): 추적할 특정 라인 번호.

        Returns:
            any: 디버그 결과.
        """
        traced_df = self.trace_execution(Value, specific_vars, line_number)
        self.update_result_output(Value)
        return traced_df

        

psql_connector = PostgreSQLConnector(settings.databases["ipcm"].db_url)




class CustomScriptManager(dict, metaclass=SingletonInstance):
    def __init__(self):
        super().__init__()
        self.load_custom_scripts()
        self.cnt_calc = 0
        
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(cnt={len(self)})"

    def load_custom_scripts(self):
        df_calc_script_setting_input = psql_connector.load_table_as_df(
            table="calc_tag_setting_input",
            index_col="script_id",
        )
        df_calc_script_setting_output = psql_connector.load_table_as_df(
            table="calc_tag_setting_output", index_col="output_tagname"
        )
        for script_id, row in df_calc_script_setting_input.iterrows():
            try:
                output_tag_data = df_calc_script_setting_output[
                    df_calc_script_setting_output.script_id == script_id
                ]
                output_tags = []
                for tagname, _data in output_tag_data.iterrows():
                    _output_tag = _ScriptOutputTags(
                        tagname=tagname, script=_data.output_tag_code
                    )
                    output_tags.append(_output_tag)

                custom_script: CustomScript = self.create_custom_tag_obj(
                    script_id=script_id,
                    script_name=row.script_name,
                    calculation_code=row.calculation_code,
                    initialization_code=row.initialization_code,
                    input_tagnames=row.input_tagnames,
                    output_tags=output_tags,
                )

                self.register_calc_tag(custom_script, logging=True)
            except Exception as e:
                logger.error(e)

    def create_custom_tag_obj(
        self,
        script_id: str,
        script_name: str,
        calculation_code: str,
        initialization_code: str,
        input_tagnames: list[str],
        output_tags: list[dict],
    ) -> CustomScript:
        return CustomScript(
            script_id=script_id,
            script_name=script_name,
            calculation_code=calculation_code,
            initialization_code=initialization_code,
            input_tagnames=input_tagnames,
            output_tags=output_tags,
        )

    def register_calc_tag(
        self, custom_script: CustomScript, logging: bool = False
    ) -> None:
        _update = False
        if custom_script.script_id in self:
            _update = True
        try:
            self[custom_script.script_id] = custom_script
            if logging:
                if _update:
                    logger.info(f"Updated custom tag ({custom_script.script_id})")
                else:
                    logger.debug(f"Registerd custom tag ({custom_script.script_id})")
        except Exception as e:
            logger.exception(e)

    def unregister_calc_tag(self, script_id: str) -> None:
        try:
            del self[script_id]
            logger.debug(f"Unregisterd custom tag ({script_id})")
        except KeyError:
            raise CanNotFindTagError(f"Requested tagname is not in {str(self)}")
   
   #script.py
    def _save_custom_tag_input(self, custom_tag: _ScriptInfo) -> dict:
        table = "calc_tag_setting_input"
        fields = [
            "script_name",
            "input_tagnames",
            "initialization_code",
            "calculation_code",
        ]
        params = [
            custom_tag.script_name,
            custom_tag.input_tagnames,
            custom_tag.initialization_code,
            custom_tag.calculation_code,
        ]
        insert_result = psql_connector.insert(
            table=table, fields=fields, params=params, returning_fields="script_id"
        )

        return insert_result

    def _save_custom_tag_output(self, script_id: int, custom_tag: _ScriptInfo) -> None:
        table = "calc_tag_setting_output"
        fields = [
            "script_id",
            "output_tagname",
            "display_tagname",
            "output_tag_code",
        ]

        params_list = []
        for output_tag in custom_tag.output_tags:
            params_list.append([
                script_id,
                output_tag.tagname,
                output_tag.tagname,
                output_tag.script,
            ])

        psql_connector.insert_many(table=table, fields=fields, params_list=params_list)

    def save_custom_tag(self, custom_tag: _ScriptInfo) -> int:
        insert_result_script_input = self._save_custom_tag_input(custom_tag)
        script_id = insert_result_script_input["script_id"]
        self._save_custom_tag_output(script_id=script_id, custom_tag=custom_tag)
        return script_id


    #main.py
    def _calc_script(self, custom_script: CustomScript) -> None:
        is_data_updated = False

        # * Update script data from script data queue
        try:
            script_tag_values = script_tag_value_queue._pop(custom_script.script_id)
            is_data_updated = custom_script.update_last_data(script_tag_values)

        except (QueueEmpty, KeyError):
            pass
        except Exception as e:
            logger.error(e)
            return

        if not is_data_updated:
            return
        custom_script.calc(script_data=custom_script.last_data)
        self.cnt_calc += 1

    def calc_scripts(self) -> None:
        self.cnt_calc = 0
        for script_key, custom_script in list(self.items()):
            try:
                self._calc_script(custom_script)
            except Exception as e:
                logger.error(f"Could not calculate script {script_key=}")
                logger.error(e)

    def create_calc_result_updated_only(self) -> dict:
        custom_script: CustomScript
        response = ToIPCM()
        for custom_script in list(self.values()):
            try:
                if custom_script.result_output:
                    script_result = response.script_data.add()
                    script_result.script_id = str(custom_script.script_id)
                    for tagname, script_tag_data in custom_script.result_output.items():
                        script_result_tag = script_result.data.add()
                        script_result_tag.tagname = tagname
                        script_result_tag.value = script_tag_data["value"]
                        script_result_tag.timestamp = script_tag_data["timestamp"]
                        script_result_tag.status_code = script_tag_data["status_code"]

            except Exception as e:
                logger.error(e)
        return response

class CanNotFindTagError(Exception):
    def __init__(self, message):
        super().__init__(message)
        logger.error(message)
