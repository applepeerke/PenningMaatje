import os

from root_functions import get_root_dir
from src.BL.Managers.ImportManager import ImportManager
from src.DL.Config import CF_IMPORT_PATH_BOOKING_CODES, CF_IMPORT_PATH_COUNTER_ACCOUNTS, \
    CF_IMPORT_PATH_SEARCH_TERMS, CF_INPUT_DIR, CF_OUTPUT_DIR, \
    COUNTER_ACCOUNTS_CSV, BOOKING_CODES_CSV, SEARCH_TERMS_CSV, CF_IMPORT_PATH_ACCOUNTS, ACCOUNTS_CSV, \
    OPENING_BALANCE_CSV, CF_IMPORT_PATH_OPENING_BALANCE
from src.DL.DBInitialize import DBInitialize
from src.VL.Controllers.MainController import MainController
from src.VL.Models.MainModel import MainModel
from src.VL.Windows.MainWindow import MainWindow
from src.GL.BusinessLayer.ConfigManager import ConfigManager
from src.GL.BusinessLayer.LogManager import Singleton as Log
from src.GL.BusinessLayer.SessionManager import Singleton as Session, UT
from src.GL.Const import EMPTY
from src.GL.Enums import LogLevel, ResultCode
from src.GL.GeneralException import GeneralException
from src.GL.Result import Result
from src.GL.Validate import normalize_dir

PGM = f'{UT}/Functions'

CM = ConfigManager(unit_test=True)
log = Log()


def get_root_sub_dir(sub_dir):
    ut_path = normalize_dir(f'{get_root_dir()}{UT}')
    return normalize_dir(f'{ut_path}{sub_dir}')


def get_base_dir():
    subdir = 'Basisfolder'
    path = get_root_sub_dir(subdir)
    if not path:
        raise GeneralException(f'{PGM}: Subfolder "{subdir}" does not exist in "{path}"')
    return path


def get_input_sub_dir(subdir):
    base_dir = get_base_dir()
    inp = 'Input'
    input_dir = normalize_dir(f'{base_dir}{inp}')
    if not input_dir:
        raise GeneralException(f'{PGM}: Folder "{inp}" does not exist in "{base_dir}"')
    input_subdir = normalize_dir(f'{input_dir}{subdir}')
    if not input_subdir:
        raise GeneralException(f'{PGM}: Folder "{subdir}" does not exist in "{input_dir}"')
    return input_subdir


def start_up(input_dir=EMPTY, build=False, auto_continue=True) -> Result:
    """ Start without using GUI Controller """

    # Session
    try:
        session = get_session(get_base_dir(), auto_continue)
    except GeneralException as e:
        return Result(ResultCode.Error, e)

    # Config - create json from session
    _create_config_from_session(session, input_dir)

    # DB
    result = start_db(build)
    if result.OK and build:
        # Log
        log.start_log(Session().log_dir, level=LogLevel.Verbose)
        # Populate DB
        IM = ImportManager()
        result = IM.start()
    return result


def get_session(base_dir=EMPTY, auto_continue=True) -> Session:
    # Validation
    if base_dir and not os.path.isdir(base_dir[:-1]):
        raise GeneralException(f'{PGM}: Dir does not exist: {base_dir[:-1]}')

    session = Session()
    session.start(unit_test=True)
    session.unit_test_auto_continue = auto_continue
    return session


def get_context(input_dir) -> (MainModel, MainController):
    """
    Creates and injects a context in the Controller
    """
    # Create json config and session
    result = start_up(input_dir)
    if not result.OK:
        return None
    # Controller (uses json config)
    W = MainWindow(unit_test=True)
    # W.display()

    # M = MainView()
    # # Import transactions in db
    # C.start_up(VMs=M.view_models, build_db=True)
    # A warning may exist (about bookings)
    if result.ER:
        return None
    controller = MainController(W.model, W, unit_test=True)
    controller.start_up()
    return W.model, controller


def _create_config_from_session(session, input_dir):
    """
    json config is the starting point of the Controller.
    base_dir from session, input_dir from parameter.
    """
    CM.unit_test = True  # Can be initialized as False (e.g. in MessageBox)
    # Base
    CM.set_config_item(CF_OUTPUT_DIR, session.output_dir)
    # Input
    CM.start_config(persist=True)
    # Csv files
    if not input_dir:
        input_dir = get_input_sub_dir('Bankafschriften')
    CM.set_config_item(CF_INPUT_DIR, input_dir)

    userdata_dir = session.userdata_dir
    CM.set_config_item(CF_IMPORT_PATH_ACCOUNTS, f'{userdata_dir}{ACCOUNTS_CSV}')
    CM.set_config_item(CF_IMPORT_PATH_BOOKING_CODES, f'{userdata_dir}{BOOKING_CODES_CSV}')
    CM.set_config_item(CF_IMPORT_PATH_COUNTER_ACCOUNTS, f'{userdata_dir}{COUNTER_ACCOUNTS_CSV}')
    CM.set_config_item(CF_IMPORT_PATH_SEARCH_TERMS, f'{userdata_dir}{SEARCH_TERMS_CSV}')
    CM.set_config_item(CF_IMPORT_PATH_OPENING_BALANCE, f'{userdata_dir}{OPENING_BALANCE_CSV}')

    # Write the json config
    CM.write_config()


def start_db(build=False) -> Result:
    DBInit = DBInitialize()
    return DBInit.start(build=build)
