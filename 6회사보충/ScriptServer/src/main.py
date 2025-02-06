import asyncio
import multiprocessing as mp
import signal
import sys
import threading
import time

from api_server import config as api_config
from api_server import exceptions as ex_api
from api_server.apis.routes.calc import cleanup_debug_sessions
from api_server.middleware.timing import add_timing_middleware
from config import settings
from custom_calc.customcalctag import CustomScriptManager
from data_manager.kafka_consumer import StreamDataCollector
from data_manager.kafka_producer import MessageProducer
from dbinfo import exceptions as ex_db
from utils import system as system_util
from utils.logger import logger

calc_manager = CustomScriptManager()
PROC_NAME = mp.current_process().name

STOP_CONSUMER = threading.Event()


def collect_kafka_script_values(initial_sleep: int = 5) -> None:
    time.sleep(initial_sleep)

    consumer = StreamDataCollector(
        broker=settings.kafka.brokers,
        topic=settings.kafka.topic_model_values,
    )

    while not STOP_CONSUMER.is_set():
        try:
            consumer.receive_message()
        except Exception as e:
            logger.error(e)

    consumer.close()  # Close the consumer properly
    logger.info("Consumer closed gracefully.")


def run_api_server(host: str = None, port: int = None) -> None:
    global IS_RUN_APP
    import uvicorn

    _host = api_config.get_api_ip() if host is None else host
    _port = system_util.get_available_port() if port is None else port

    from api_server.apis.routes.api import router

    api_router = router

    app = api_config.get_application()
    app.include_router(api_router)
    exclude_timing = "health"
    add_timing_middleware(
        app, record=logger.trace, prefix="app", exclude=exclude_timing
    )
    ex_api.add_exception_handlers(app)

    IS_RUN_APP = True
    uvicorn.run(
        app,
        host=_host,
        port=_port,
        log_config=api_config.get_uvicorn_logging_config(),
    )


async def calc_scripts(interval: int = 0.1) -> None:
    producer = MessageProducer(
        broker=settings.kafka.brokers,
        topic=settings.kafka.topic_pred_values,
    )
    await asyncio.sleep(5)

    async def __calc_scripts():
        calc_manager.calc_scripts()
        if (calc_cnt := calc_manager.cnt_calc) == 0:
            return
        updated_data = calc_manager.create_cacl_result_updated_only()
        updated_data_serialized = updated_data.SerializeToString
        if len(updated_data_serialized) == 0:
            return
        producer.send_message(updated_data_serialized)

        logger.trace(f"[{PROC_NAME}] model calculated: {calc_cnt}/{len(calc_manager)}")

    while True:
        asyncio.create_task(__calc_scripts())
        await asyncio.sleep(interval)


def thr_calc_script(interval: int = 0.1):
    try:
        logger.debug(f"{'Initializing':12} | Script calculator is starting...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(calc_scripts(interval))
        loop.close()
    except Exception as err:
        raise ex_db.InitializingFailError(
            "Can not initialize Script calculator thread"
        ) from err


def thr_cleanup_debug_sessions(interval: float = 5.0):
    try:
        logger.debug(
            f"{'Initializing':12} | Debug session cleanup thread is starting..."
        )
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(cleanup_debug_sessions(interval))
        loop.close()
    except Exception as err:
        raise ex_db.InitializingFailError(
            "Can not initialize debug session cleanup thread"
        ) from err


def thr_kafka_modelvalues_collector():
    logger.debug(f"{'Initializing':12} | Lastvalue collector is starting...")
    collect_kafka_script_values(initial_sleep=5)
    logger.error("Rawvalues collector is terminated")


def run_server(port: int) -> None:
    try:
        thread_api_server = threading.Thread(
            name="SubThread (API Server)",
            target=run_api_server,
            args=(None, port),
        )
        thread_rawvalues_collector = threading.Thread(
            name="SubThread (Rawvalue Collector)",
            target=thr_kafka_modelvalues_collector,
        )
        thread_script_calculator = threading.Thread(
            name="SubThread (Script Calculator)",
            target=thr_calc_script,
        )
        thread_cleanup_debug_clients = threading.Thread(
            name="SubThread (Debug Client Cleanup)",
            target=thr_cleanup_debug_sessions,
        )
        threads = [
            thread_api_server,
            thread_rawvalues_collector,
            thread_script_calculator,
            thread_cleanup_debug_clients,
        ]
        [thread.start() for thread in threads]

        # Wait for a signal to stop
        def signal_handler(sig, frame):
            logger.info("Signal received, stopping threads...")
            STOP_CONSUMER.set()
            [thread.join() for thread in threads]
            logger.info("All threads have been joined. Exiting.")
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    except Exception as e:
        logger.exception(e)


run_server(port=settings.servers["this"].port)
