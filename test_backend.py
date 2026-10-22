import tempfile
from concurrent.futures import TimeoutError as FutureTimeoutError
from pathlib import Path
import json
import socket
import sqlite3
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.ml.ml_risk_evidence import MODEL_FILE, ModelUnavailableError, generate_ml_evidence
import app.ml.ml_risk_evidence as ml_evidence
import backend.database as database
import backend.security.dns_checker as dns_checker
from backend.information_retrieval import build_ir_analysis
from backend.main import app, classifier_is_ready
from backend.security.dns_checker import check_dns
from backend.security.ssl_checker import check_ssl


client = TestClient(app)


def test_root_and_docs_load():
    root = client.get("/")
    assert root.status_code == 200
    assert root.json()["model"]["available"] is classifier_is_ready()
    assert client.get("/docs").status_code == 200


def test_invalid_url_is_rejected():
    values = (
        "",
        "not a URL",
        "ftp://example.com",
        "https://user:secret@example.com",
        "https://example.com/" + "a" * 2048,
    )
    for value in values:
        response = client.post("/api/v1/scan", json={"url": value})
        assert response.status_code == 422
        assert "user:secret" not in response.text
        assert "a" * 64 not in response.text
    assert client.post("/api/v1/scan", json={}).status_code == 422


@pytest.mark.skipif(not MODEL_FILE.is_file(), reason="project LFS model is unavailable")
def test_trained_model_runs_with_current_feature_schema():
    result = generate_ml_evidence("https://www.python.org")
    assert result["classification"] in {"phishing", "legitimate"}
    assert 0 <= result["phishing_probability"] <= 1
    assert 0 <= result["confidence"] <= 1


def test_missing_model_error_does_not_expose_filesystem_path(tmp_path):
    ml_evidence.load_model.cache_clear()
    missing_path = tmp_path / "missing-model.joblib"
    with patch.object(ml_evidence, "MODEL_FILE", missing_path):
        with pytest.raises(ModelUnavailableError) as raised:
            ml_evidence.load_model()
    assert str(tmp_path) not in str(raised.value)
    ml_evidence.load_model.cache_clear()


def test_missing_model_returns_partial_security_checks():
    with (
        patch("backend.main.check_dns", return_value={"resolves": True, "public": True, "ip_address": "8.8.8.8", "error": None}),
        patch("backend.main.check_ssl", return_value={"valid": True, "checked": True, "expires": None, "issuer": None, "error": None}),
        patch("backend.main.analyze_url", side_effect=ModelUnavailableError("trained model is missing")),
    ):
        response = client.post("/api/v1/scan", json={"url": "https://www.python.org"})

    assert response.status_code == 503
    detail = response.json()["detail"]
    assert detail["code"] == "model_unavailable"
    assert "independent security checks" in detail["message"]
    assert str(MODEL_FILE) not in response.text
    assert detail["partial_results"]["dns"]["resolves"] is True
    assert detail["partial_results"]["url_security"]


def test_inference_exception_is_sanitized_and_keeps_partial_checks():
    with (
        patch("backend.main.check_dns", return_value={"resolves": True, "public": True, "ip_address": "8.8.8.8", "error": None}),
        patch("backend.main.check_ssl", return_value={"valid": True, "checked": True, "expires": None, "issuer": None, "error": None}),
        patch("backend.main.analyze_url", side_effect=RuntimeError("internal test detail")),
    ):
        response = client.post("/api/v1/scan", json={"url": "https://www.python.org"})
    assert response.status_code == 500
    detail = response.json()["detail"]
    assert detail["code"] == "ml_inference_failed"
    assert "internal test detail" not in response.text
    assert detail["partial_results"]["dns"]["public"] is True


def test_history_is_database_backed_list():
    response = client.get("/api/v1/history")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    for record in response.json():
        assert {"id", "url", "classification", "risk_score", "confidence", "scan_time", "result"} <= record.keys()


def test_http_request_does_not_run_ssl_check():
    with (
        patch("backend.main.check_dns", return_value={"resolves": True, "public": True, "ip_address": "8.8.8.8", "error": None}),
        patch("backend.main.check_ssl", side_effect=AssertionError("HTTP must not initiate TLS")),
        patch("backend.main.analyze_url", side_effect=ModelUnavailableError("missing model fixture")),
    ):
        response = client.post("/api/v1/scan", json={"url": "http://example.com"})
    assert response.status_code == 503
    ssl_result = response.json()["detail"]["partial_results"]["ssl"]
    assert ssl_result["checked"] is False
    assert ssl_result["valid"] is None


def test_local_frontend_origin_is_allowed_by_cors():
    origin = "http://127.0.0.1:5502"
    response = client.options(
        "/api/v1/history",
        headers={"Origin": origin, "Access-Control-Request-Method": "GET"},
    )
    assert response.headers.get("access-control-allow-origin") == origin


def test_empty_history_ir_is_unavailable_without_fabricated_values():
    result = build_ir_analysis("https://www.python.org", [])
    assert result["status"] == "unavailable"
    assert result["corpus_size"] == 0
    assert result["language_model"]["status"] == "unavailable"
    assert result["pagerank"]["graph_nodes"] == 1
    assert result["content_recommendations"]["recommendations"] == []


def test_ir_metrics_use_labeled_historical_urls():
    history = [
        {
            "url": "https://example.com/login/verify",
            "result_json": json.dumps({"ml": {"classification": "phishing"}}),
        },
        {
            "url": "https://example.com/docs/python",
            "result_json": json.dumps({"ml": {"classification": "legitimate"}}),
        },
    ]
    result = build_ir_analysis("https://example.com/login/account", history)
    assert result["language_model"]["status"] == "available"
    assert result["pagerank"]["status"] == "unavailable"
    assert result["pagerank"]["graph_nodes"] == 3
    assert result["pagerank"]["graph_edges"] == 0
    assert "score" not in result["pagerank"]
    assert result["content_recommendations"]["recommendations"]


def test_history_database_failure_is_reported():
    with patch("backend.main.connection_scope", side_effect=sqlite3.OperationalError("database unavailable")):
        response = client.get("/api/v1/history")
    assert response.status_code == 500
    assert response.json()["detail"]["code"] == "history_unavailable"
    assert "database unavailable" not in response.text


def test_dns_blocks_private_addresses():
    private_record = (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 0))
    with patch("backend.security.dns_checker.socket.getaddrinfo", return_value=[private_record]):
        result = check_dns("localhost")
    assert result["resolves"] is True
    assert result["public"] is False
    assert result["ip_address"] is None


def test_dns_rejects_mixed_public_and_private_answers():
    public_record = (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 0))
    private_record = (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.5", 0))
    with patch("backend.security.dns_checker.socket.getaddrinfo", return_value=[public_record, private_record]):
        result = check_dns("mixed.example")
    assert result["public"] is False
    assert result["ip_address"] is None


def test_dns_resolution_timeout_is_reported():
    future = MagicMock()
    future.result.side_effect = FutureTimeoutError()
    future.add_done_callback.side_effect = lambda callback: callback(future)
    with patch.object(dns_checker.DNS_RESOLVER, "submit", return_value=future):
        result = check_dns("slow.example")
    assert result["resolves"] is False
    assert result["error"] == "DNS resolution timed out"


def test_ssl_does_not_connect_to_nonpublic_address():
    with patch("backend.security.ssl_checker.socket.create_connection", side_effect=AssertionError("connection attempted")):
        result = check_ssl("localhost", "127.0.0.1")
    assert result["valid"] is False
    assert "skipped" in result["error"].lower()


def test_ssl_pins_public_ip_and_keeps_hostname_for_sni():
    connection = MagicMock()
    connection.__enter__.return_value = connection
    ssl_socket = MagicMock()
    ssl_socket.getpeercert.return_value = {
        "notAfter": "Jun 21 21:00:00 2030 GMT",
        "issuer": [[("commonName", "Example CA")]],
    }
    tls_context = MagicMock()
    tls_context.wrap_socket.return_value.__enter__.return_value = ssl_socket
    with (
        patch("backend.security.ssl_checker.ssl.create_default_context", return_value=tls_context),
        patch("backend.security.ssl_checker.socket.create_connection", return_value=connection) as connect,
    ):
        result = check_ssl("example.com", "8.8.8.8")
    assert result["valid"] is True
    connect.assert_called_once_with(("8.8.8.8", 443), timeout=5)
    tls_context.wrap_socket.assert_called_once_with(connection, server_hostname="example.com")


def test_private_dns_result_is_never_passed_to_ssl():
    with (
        patch("backend.main.check_dns", return_value={"resolves": True, "public": False, "ip_address": None, "error": "private"}),
        patch("backend.main.check_ssl", side_effect=AssertionError("private target reached SSL")) as ssl_check,
        patch("backend.main.analyze_url", side_effect=AssertionError("private target reached inference")),
    ):
        response = client.post("/api/v1/scan", json={"url": "http://127.0.0.1"})
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "destination_restricted"
    assert response.json()["detail"]["partial_results"]["verifiable"] is False
    assert response.json()["detail"]["partial_results"]["dns"]["ip_address"] is None
    ssl_check.assert_not_called()


def test_successful_scan_is_saved_to_database_history():
    ml_result = {
        "classification": "legitimate",
        "phishing_probability": 0.05,
        "legitimate_probability": 0.95,
        "confidence": 0.95,
        "threshold": 0.95,
        "ml_evidence_level": "low",
        "signals": [],
        "explanation": "Test inference result.",
    }
    with tempfile.TemporaryDirectory() as temporary_directory:
        test_database = Path(temporary_directory) / "history.sqlite3"
        with patch.object(database, "DATABASE_PATH", test_database):
            database.init_db()
            with (
                patch("backend.main.check_dns", return_value={"resolves": True, "public": True, "ip_address": "8.8.8.8", "error": None}),
                patch("backend.main.check_ssl", return_value={"valid": True, "checked": True, "expires": None, "issuer": None, "error": None}),
                patch("backend.main.analyze_url", return_value=ml_result),
            ):
                response = client.post("/api/v1/scan", json={"url": "https://www.python.org"})
                assert response.status_code == 200, response.text
                result = response.json()
                assert result["verifiable"] is True
                assert result["risk_score"] == pytest.approx(3.0)
                history = client.get("/api/v1/history").json()
                assert len(history) == 1
                assert history[0]["result"]["url"] == result["url"]
                cleared = client.delete("/api/v1/history")
                assert cleared.json() == {"deleted": True}
                assert client.get("/api/v1/history").json() == []


def test_invalid_tls_keeps_https_scan_unverified(tmp_path):
    ml_result = {
        "classification": "legitimate",
        "phishing_probability": 0.05,
        "legitimate_probability": 0.95,
        "confidence": 0.95,
        "threshold": 0.95,
        "ml_evidence_level": "low",
        "signals": [],
        "explanation": "Test inference result.",
    }
    with patch.object(database, "DATABASE_PATH", tmp_path / "history.sqlite3"):
        database.init_db()
        with (
            patch("backend.main.check_dns", return_value={"resolves": True, "public": True, "ip_address": "8.8.8.8", "error": None}),
            patch("backend.main.check_ssl", return_value={"valid": False, "checked": True, "expires": None, "issuer": None, "error": "verification failed"}),
            patch("backend.main.analyze_url", return_value=ml_result),
        ):
            response = client.post("/api/v1/scan", json={"url": "https://www.python.org"})
    assert response.status_code == 200
    assert response.json()["risk_score"] == pytest.approx(13.0)
    assert response.json()["verifiable"] is False
