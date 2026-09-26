from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from pydantic import BaseModel
import main_config
from tracing_config import configure_tracing


from database import Repository


configure_tracing("dictionary-service")

app = FastAPI(root_path="/db")
FastAPIInstrumentor.instrument_app(app, excluded_urls="healthz")


app.add_middleware(
    CORSMiddleware,
    allow_origins=main_config.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class hintModel(BaseModel):
    word: str


@app.post("/hint")
def hint(_hintModel: hintModel):
    hintWord = _hintModel.word.strip()
    if hintWord == "":
        return []
    if hintWord.__contains__(" "):
        # 搭配詞 pattern 查詢已經不存在（改用字典 schema，見
        # scripts/import_wiktionary.py）；多字輸入先當作 prefix 查詢，
        # 之後如果要做逐字元 autocomplete，可以讓單字輸入也走這條路。
        return Repository.getWithPrefix(hintWord)
    return Repository.getWithTerm(hintWord)


@app.get("/healthz/live")
def healthz_live():
    return {"status": "ok"}


@app.get("/healthz/ready")
def healthz_ready():
    # 借用既有查詢路徑順便驗證 Redis／MongoDB 都能連上，不另外接觸底層 client。
    try:
        Repository.getWithTerm(hintWord="__healthz__")
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return {"status": "ok"}



