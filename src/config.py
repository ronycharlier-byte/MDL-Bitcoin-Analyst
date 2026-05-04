from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CORPUS_ROOT = PROJECT_ROOT.parent

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
FEATURES_DIR = DATA_DIR / "features"
BACKTESTS_DIR = DATA_DIR / "backtests"
SIMULATIONS_DIR = DATA_DIR / "simulations"
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge_base"
CORPUS_RAW_DIR = KNOWLEDGE_DIR / "corpus_raw"
CORPUS_CHUNKS_DIR = KNOWLEDGE_DIR / "corpus_chunks"
METADATA_DIR = KNOWLEDGE_DIR / "metadata"
CLAIMS_DIR = KNOWLEDGE_DIR / "claims"
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"
LOGS_DIR = PROJECT_ROOT / "logs"
DB_PATH = DATA_DIR / "quant_model.db"
LOG_PATH = LOGS_DIR / "system.log"

STATUS_REAL = "real"
STATUS_MOCK = "mock"
STATUS_MISSING = "missing"

DEFAULT_SEED = 42
TRADING_DAYS = 365

REQUIRED_DIRS = [
    DATA_DIR,
    RAW_DIR,
    PROCESSED_DIR,
    FEATURES_DIR,
    BACKTESTS_DIR,
    SIMULATIONS_DIR,
    KNOWLEDGE_DIR,
    CORPUS_RAW_DIR,
    CORPUS_CHUNKS_DIR,
    METADATA_DIR,
    CLAIMS_DIR,
    MODELS_DIR,
    REPORTS_DIR,
    LOGS_DIR,
]

TEXT_EXTENSIONS = {".md", ".txt", ".json", ".csv", ".html", ".htm"}

RELEVANCE_KEYWORDS = {
    "bitcoin",
    "btc",
    "crypto",
    "market",
    "marche",
    "macro",
    "volatil",
    "volatility",
    "risk",
    "risque",
    "hypothese",
    "hypothesis",
    "nasdaq",
    "dxy",
    "taux",
    "rates",
    "liquidation",
    "funding",
    "drawdown",
    "correlation",
    "regime",
}

FUNDAMENTAL_COLUMNS = [
    "etf_flows",
    "funding_rate",
    "open_interest",
    "liquidations",
    "hash_rate",
    "exchange_reserves",
    "stablecoins_supply",
    "dxy",
    "us_rates",
    "nasdaq",
]


def ensure_directories() -> None:
    for directory in REQUIRED_DIRS:
        directory.mkdir(parents=True, exist_ok=True)
