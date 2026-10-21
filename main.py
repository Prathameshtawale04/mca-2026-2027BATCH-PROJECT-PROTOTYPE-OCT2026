import json
import logging

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl, field_validator

from backend.database import connection_scope, init_db
from backend.utils.url_validator import MAX_URL_LENGTH, validate_url
from backend.security.dns_checker import check_dns
from backend.security.ssl_checker import check_ssl
from backend.security.url_security import check_url_security
from backend.risk_engine import calculate_risk
from backend.information_retrieval import build_ir_analysis
from app.features.url_features import extract_url_features
from app.ml.ml_risk_evidence import ModelUnavailableError, load_model
from app.ml.ml_service import analyze_url


logger = logging.getLogger(__name__)

app = FastAPI(
    title="Phishing URL Risk Detector API",
    description="Backend API for detecting suspicious and phishing URLs.",
    version="1.0.0"
)


# Allow the frontend to communicate with the FastAPI backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=r"^http://(127\.0\.0\.1|localhost):[0-9]+$",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize database when the application starts
init_db()


def classifier_is_ready():
    try:
        model = load_model()
        feature_names = list(model.feature_names_in_)
        expected_features = list(extract_url_features("https://www.python.org"))
        model_classes = {int(value) for value in model.classes_}
        return (
            callable(getattr(model, "predict_proba", None))
            and model_classes == {0, 1}
            and feature_names == expected_features
            and model.n_features_in_ == len(expected_features)
        )
    except ModelUnavailableError:
        return False
    except Exception:
        logger.exception("Classifier readiness check failed")
        return False


class URLRequest(BaseModel):
    url: HttpUrl

    @field_validator("url", mode="before")
    @classmethod
    def limit_url_length(cls, value):
        if not isinstance(value, str) or not value.strip() or len(value.strip()) > MAX_URL_LENGTH:
            raise ValueError("Invalid URL length.")
        return value.strip()

    @field_validator("url")
    @classmethod
    def reject_url_credentials(cls, value):
        if value.username is not None or value.password is not None:
            raise ValueError("URLs containing credentials are not allowed.")
        return value


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request, error):
    return JSONResponse(
        status_code=422,
        content={"detail": "Invalid request. Enter a credential-free HTTP or HTTPS URL."},
    )


@app.get("/")
def home():
    model_available = classifier_is_ready()
    return {
        "message": "Phishing URL Risk Detector API is running!",
        "model": {
            "available": model_available,
            "message": None if model_available else "The trained classifier artifact is not installed.",
        },
    }


@app.post("/api/v1/scan")
def scan_url(request: URLRequest):
    try:
        url = str(request.url)
        is_valid = validate_url(url)
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid URL")
        domain = request.url.host
        if not domain:
            raise HTTPException(status_code=400, detail="Could not extract domain from URL")

        dns_result = check_dns(domain)
        url_security_result = check_url_security(url)
        ssl_result = {
            "valid": None,
            "checked": False,
            "expires": None,
            "issuer": None,
            "error": "SSL is only checked for HTTPS URLs",
        }

        if dns_result["resolves"] and not dns_result.get("public", False):
            partial_results = {
                "url": url,
                "valid": is_valid,
                "verifiable": False,
                "dns": dns_result,
                "ssl": ssl_result,
                "url_security": url_security_result,
                "ml": {"status": "unavailable"},
            }
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "destination_restricted",
                    "message": "This destination is restricted for security reasons.",
                    "partial_results": partial_results,
                },
            )

        if url.startswith("https://"):
            ssl_result = check_ssl(domain, dns_result.get("ip_address"))

        verifiable = bool(
            dns_result["resolves"]
            and dns_result.get("public")
            and (
                not url.startswith("https://")
                or ssl_result.get("checked") is True and ssl_result.get("valid") is True
            )
        )

        partial_results = {
            "url": url,
            "valid": is_valid,
            "verifiable": verifiable,
            "dns": dns_result,
            "ssl": ssl_result,
            "url_security": url_security_result,
            "ml": {"status": "unavailable"},
        }

        try:
            ml_result = analyze_url(url)
        except ModelUnavailableError as error:
            logger.warning("Classifier artifact unavailable for scan")
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "model_unavailable",
                    "message": "The trained classifier is unavailable; independent security checks are shown.",
                    "partial_results": partial_results,
                },
            ) from error
        except Exception as error:
            logger.exception("Machine-learning inference failed")
            raise HTTPException(
                status_code=500,
                detail={
                    "code": "ml_inference_failed",
                    "message": "Machine-learning analysis could not be completed; no ML verdict was produced.",
                    "partial_results": partial_results,
                },
            ) from error

        risk_result = calculate_risk(
            ml_prediction=ml_result["classification"],
            ml_probability=ml_result["phishing_probability"],
            ml_confidence=ml_result["confidence"],
            dns_resolves=dns_result["resolves"],
            ssl_valid=ssl_result["valid"],
            url_security=url_security_result
        )

        result = {
            "url": url,
            "valid": is_valid,
            "verifiable": verifiable,
            "classification": risk_result["classification"],
            "risk_score": risk_result["risk_score"],
            "confidence": risk_result["confidence"],
            "score_breakdown": risk_result["score_breakdown"],
            "ml": ml_result,
            "dns": dns_result,
            "ssl": ssl_result,
            "url_security": url_security_result,
            "ir_analysis": None,
            "risk_explanation": risk_result["explanation"],
            "url_security_reasons": (
                risk_result["url_security_reasons"]
            ),
            "message": "URL scanned successfully"
        }

        with connection_scope() as connection:
            history = connection.execute(
                "SELECT url, result_json FROM scan_history ORDER BY id DESC"
            ).fetchall()
            result["ir_analysis"] = build_ir_analysis(url, history)
            connection.execute(
                """
                INSERT INTO scan_history (
                    url, classification, risk_score, confidence, result_json
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    url,
                    risk_result["classification"],
                    risk_result["risk_score"],
                    risk_result["confidence"],
                    json.dumps(result),
                ),
            )

        return result

    except HTTPException:
        raise
    except Exception as error:
        logger.exception("Scan request failed")
        raise HTTPException(
            status_code=500,
            detail={"code": "scan_failed", "message": "The scan could not be completed. Please retry."},
        ) from error


@app.get("/api/v1/history")
def get_history():
    try:
        with connection_scope() as connection:
            rows = connection.execute(
                """
                SELECT id, url, classification, risk_score, confidence,
                       scan_time, result_json
                FROM scan_history
                ORDER BY id DESC
                """
            ).fetchall()
        return [
            {
                "id": row["id"],
                "url": row["url"],
                "classification": row["classification"],
                "risk_score": row["risk_score"],
                "confidence": row["confidence"],
                "scan_time": row["scan_time"],
                "result": json.loads(row["result_json"] or "{}"),
            }
            for row in rows
        ]
    except Exception as error:
        logger.exception("Scan history retrieval failed")
        raise HTTPException(
            status_code=500,
            detail={"code": "history_unavailable", "message": "Scan history could not be retrieved."},
        ) from error


@app.delete("/api/v1/history")
def clear_history():
    try:
        with connection_scope() as connection:
            connection.execute("DELETE FROM scan_history")
        return {"deleted": True}
    except Exception as error:
        logger.exception("Scan history clearing failed")
        raise HTTPException(
            status_code=500,
            detail={"code": "history_clear_failed", "message": "Scan history could not be cleared."},
        ) from error