"use strict";

/* =========================================================
   PHISHGUARD - FRONTEND JAVASCRIPT
   ========================================================= */

const API_BASE_URL = String(
    window.PHISHGUARD_API_BASE_URL || "http://127.0.0.1:8000"
).replace(/\/+$/, "");
const MAX_URL_LENGTH = 2048;
let historyRecords = [];
let latestScanResult = null;
let historyUnavailable = false;
let scanInProgress = false;

/* =========================================================
   HELPER FUNCTIONS
   ========================================================= */

function $(id) {
    return document.getElementById(id);
}

function safeNumber(value, fallback = 0) {
    const n = Number(value);
    return Number.isFinite(n) ? n : fallback;
}

function formatDate(date = new Date()) {
    return date.toLocaleString();
}

function escapeHTML(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function isShortenedURL(url) {
    if (!url) return false;

    try {
        const host = new URL(url).hostname.toLowerCase();

        const shorteners = [
            "bit.ly",
            "tinyurl.com",
            "t.co",
            "goo.gl",
            "is.gd",
            "ow.ly",
            "buff.ly",
            "rebrand.ly",
            "cutt.ly",
            "shorturl.at",
            "tiny.cc"
        ];

        return shorteners.some(
            domain => host === domain || host.endsWith("." + domain)
        );
    } catch {
        return false;
    }
}

function isRestrictedDestination(hostname) {
    const host = String(hostname || "").toLowerCase().replace(/^\[|\]$/g, "");
    if (host === "localhost" || host.endsWith(".localhost") || host.endsWith(".local") || host.endsWith(".internal")) {
        return true;
    }

    const octets = host.split(".").map(Number);
    if (octets.length === 4 && octets.every(value => Number.isInteger(value) && value >= 0 && value <= 255)) {
        const [first, second, third] = octets;
        return first === 0
            || first === 10
            || first === 127
            || (first === 169 && second === 254)
            || (first === 172 && second >= 16 && second <= 31)
            || (first === 192 && (second === 0 || second === 168))
            || (first === 198 && (second === 18 || second === 19 || second === 51 && third === 100))
            || (first === 203 && second === 0 && third === 113)
            || (first === 100 && second >= 64 && second <= 127)
            || first >= 224;
    }

    if (host.includes(":")) {
        return host === "::"
            || host === "::1"
            || host.startsWith("::ffff:")
            || /^[f][c-d]/.test(host)
            || /^fe[89ab]/.test(host)
            || host.startsWith("ff")
            || host.startsWith("2001:db8:");
    }
    return false;
}

function validateURL(value) {
    const raw = String(value || "").trim();
    if (!raw) {
        return { valid: false, message: "Please enter a URL." };
    }
    if (raw.length > MAX_URL_LENGTH) {
        return { valid: false, message: `URLs must be ${MAX_URL_LENGTH} characters or fewer.` };
    }

    const schemeMatch = raw.match(/^([a-z][a-z0-9+.-]*):/i);
    if (schemeMatch && !/^https?:\/\//i.test(raw)) {
        return {
            valid: false,
            message: /^(http|https)$/i.test(schemeMatch[1])
                ? "Please enter a valid HTTP or HTTPS URL."
                : "Unsupported URL scheme. Use HTTP or HTTPS."
        };
    }

    const candidate = schemeMatch ? raw : `https://${raw}`;
    if (candidate.length > MAX_URL_LENGTH) {
        return { valid: false, message: `URLs must be ${MAX_URL_LENGTH} characters or fewer.` };
    }

    try {
        const parsed = new URL(candidate);
        if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
            return { valid: false, message: "Unsupported URL scheme. Use HTTP or HTTPS." };
        }

        const authority = candidate.match(/^https?:\/\/([^/?#]*)/i)?.[1] || "";
        if (authority.includes("@") || parsed.username || parsed.password) {
            return { valid: false, message: "URLs containing credentials are not allowed." };
        }

        const hostname = parsed.hostname.toLowerCase();
        const hostWithoutBrackets = hostname.replace(/^\[|\]$/g, "");
        if (!hostname || hostWithoutBrackets.length > 253) {
            return { valid: false, message: "Please enter a valid HTTP or HTTPS URL." };
        }

        if (!hostWithoutBrackets.includes(":")) {
            const labels = hostWithoutBrackets.split(".");
            const isIPv4 = labels.length === 4 && labels.every(label => /^\d{1,3}$/.test(label));
            const validDomain = labels.length >= 2
                && labels.every(label => label.length <= 63 && /^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$/i.test(label))
                && (isIPv4 || labels[labels.length - 1].length >= 2);
            if (!validDomain) {
                return { valid: false, message: "Please enter a valid HTTP or HTTPS URL." };
            }
        }

        if (isRestrictedDestination(hostname)) {
            return { valid: false, message: "This destination is restricted for security reasons." };
        }

        return { valid: true, url: parsed.href };
    } catch {
        return { valid: false, message: "Please enter a valid HTTP or HTTPS URL." };
    }
}

/* =========================================================
   DOM ELEMENTS
   ========================================================= */

const urlInput = $("urlInput");
const clearInput = $("clearInput");
const analyzeBtn = $("analyzeBtn");
const analyzeText = document.querySelector(".analyze-btn-text");
const analyzeArrow = document.querySelector(".analyze-btn-icon");

const scannerMessage = $("scannerMessage");
const scannerMessageText = $("scannerMessageText");
const urlValidationMessage = $("urlValidationMessage");
const scanLoading = $("scanLoading");
const scanAgainBtn = $("scanAgainBtn");

/* Result */

const riskScore = $("riskScore");
const riskGauge = $("riskGauge");
const riskStatus = $("riskStatus");
const riskLevel = $("riskLevel");

const verdictIcon = $("verdictIcon");
const verdictTitle = $("verdictTitle");
const verdictText = $("verdictText");
const verdictDescription = $("verdictDescription");

const confidenceValue = $("confidenceValue");
const confidenceBar = $("confidenceFill");

const resultStatus = $("resultStatus");

/* Explanation */

const explanationTitle = $("explanationTitle");
const explanationText = $("explanationText");
const aiExplanation = $("aiExplanation");
const reasonList = $("reasonList");
const emptyHistory = $("emptyHistory");

/* Features */

const featureHttpsStatus = $("featureHttpsStatus");
const featureLengthStatus = $("featureLengthStatus");
const featureIPStatus = $("featureIPStatus");
const featureAtStatus = $("featureAtStatus");
const featureSubdomainStatus = $("featureSubdomainStatus");
const featureSpecialStatus = $("featureSpecialStatus");
const featureShortenerStatus = $("featureShortenerStatus");
const featureKeywordsStatus = $("featureKeywordsStatus");

/* Security checks */

const dnsCheckIcon = $("dnsCheckIcon");
const dnsCheckStatus = $("dnsCheckStatus");
const sslCheckIcon = $("sslCheckIcon");
const sslCheckStatus = $("sslCheckStatus");
const urlCheckIcon = $("urlCheckIcon");
const urlCheckStatus = $("urlCheckStatus");
const mlCheckIcon = $("mlCheckIcon");
const mlCheckStatus = $("mlCheckStatus");

/* Report */

const reportUrl = $("reportUrl");
const reportTime = $("reportTime");
const reportVerdict = $("reportVerdict");
const reportRiskScore = $("reportRiskScore");
const reportConfidence = $("reportConfidence");
const reportStatus = $("reportStatus");
const reportSummary = $("reportSummary");
const reportIRSummary = $("reportIRSummary");
const reportBadge = $("reportBadge");
const printReportBtn = $("printReportBtn");
const exportReportBtn = $("exportReportBtn");

/* History */

const historyList = $("historyList");
const historyTableBody = $("historyTableBody");
const clearHistoryBtn = $("clearHistoryBtn");
const historyFilterButtons = document.querySelectorAll(".history-actions [data-filter]");
let activeHistoryFilter = "all";

/* Information retrieval */

const irOverallStatus = $("irOverallStatus");
const irLanguageScore = $("irLanguageScore");
const irLanguageStatus = $("irLanguageStatus");
const irSuspiciousTerms = $("irSuspiciousTerms");
const irPageRankScore = $("irPageRankScore");
const irPageRankRank = $("irPageRankRank");
const irGraphNodes = $("irGraphNodes");
const irGraphEdges = $("irGraphEdges");
const irPageRankStatus = $("irPageRankStatus");
const irGraphDetails = $("irGraphDetails");
const irRecommendations = $("irRecommendations");
const irRecommendationStatus = $("irRecommendationStatus");

/* Dashboard stats */

const totalScans = $("totalScans");
const threatsDetected = $("threatsDetected");
const safeUrls = $("safeUrls");
const modelStatus = $("modelStatus");


/* =========================================================
   MESSAGE FUNCTIONS
   ========================================================= */

function showScannerMessage(message, type = "error") {
    if (!scannerMessage) return;

    scannerMessage.style.display = "block";

    if (scannerMessageText) {
        scannerMessageText.textContent = message;
    } else {
        scannerMessage.textContent = message;
    }

    scannerMessage.classList.remove(
        "error",
        "success",
        "warning"
    );

    scannerMessage.classList.add(type);
}

function hideScannerMessage() {
    if (scannerMessage) {
        scannerMessage.style.display = "none";
    }
}

function setURLValidationMessage(message = "") {
    const text = String(message || "");
    if (urlValidationMessage) {
        urlValidationMessage.textContent = text;
    }
    if (urlInput) {
        urlInput.setAttribute("aria-invalid", String(Boolean(text)));
    }
    const wrapper = urlInput?.closest(".url-input-wrapper");
    if (wrapper) {
        wrapper.classList.toggle("invalid", Boolean(text));
    }
}


/* =========================================================
   LOADING
   ========================================================= */

function setLoading(isLoading) {
    if (analyzeBtn) {
        analyzeBtn.disabled = isLoading;
    }
    if (scanAgainBtn) {
        scanAgainBtn.disabled = isLoading;
    }

    if (analyzeText) {
        analyzeText.textContent =
            isLoading ? "Analyzing..." : "Analyze URL";
    }

    if (analyzeArrow) {
        analyzeArrow.style.display =
            isLoading ? "none" : "inline";
    }

    if (scanLoading) {
        scanLoading.style.display =
            isLoading ? "block" : "none";
    }
}


/* =========================================================
   BACKEND API
   ========================================================= */

async function analyzeWithBackend(url) {
    return requestAPI("/api/v1/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url })
    });
}

async function requestAPI(path, options = {}) {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 25000);

    try {
        const response = await fetch(`${API_BASE_URL}${path}`, {
            ...options,
            signal: controller.signal
        });
        const responseText = await response.text();
        let payload = null;

        if (responseText) {
            try {
                payload = JSON.parse(responseText);
            } catch {
                throw new Error(`Backend returned an invalid JSON response (${response.status}).`);
            }
        }

        if (!response.ok) {
            const detail = payload?.detail;
            const message = typeof detail === "string"
                ? detail
                : Array.isArray(detail)
                    ? detail.map(item => item.msg).filter(Boolean).join(" ")
                    : detail?.message || detail?.code || `Backend error (${response.status}).`;
            const error = new Error(message);
            error.status = response.status;
            error.payload = detail;
            throw error;
        }

        if (payload === null) {
            throw new Error("Backend returned an empty response.");
        }
        return payload;
    } catch (error) {
        if (error?.name === "AbortError") {
            throw new Error("The security backend timed out. Try again in a moment.");
        }
        if (error instanceof TypeError) {
            throw new Error(`Unable to connect to the security backend at ${API_BASE_URL}.`);
        }
        throw error;
    } finally {
        window.clearTimeout(timeout);
    }
}


/* =========================================================
   CONVERT BACKEND RESULT
   ========================================================= */

function convertBackendResult(data) {

    if (!data || data.valid === false) {
        return {
            valid: false,
            url: data?.url || "",
            prediction: "Invalid URL",
            classification: "invalid",
            risk_score: 0,
            confidence: 0,
            url_security: {},
            dns: {},
            ssl: {},
            ml: {},
            reasons: [],
            risk_explanation: data?.detail || "Invalid URL or unable to verify the hostname.",
            explanation: data?.detail || "Invalid URL or unable to verify the hostname.",
            ir_analysis: null
        };
    }

    const security = data.url_security || {};
    const dns = data.dns || {};
    const ssl = data.ssl || {};
    const ml = data.ml || {};
    const rawExplanation = data.explanation ?? data.risk_explanation ?? ml.explanation ?? "";

    let confidence = safeNumber(
        data.confidence ?? ml.confidence,
        0
    );

    if (confidence >= 0 && confidence <= 1) {
        confidence = confidence * 100;
    }

    confidence = Math.round(confidence * 10) / 10;

    const rawClassification = String(
        data.classification ||
        data.risk_classification ||
        ml.classification ||
        ""
    ).toLowerCase();

    const riskScoreValue = safeNumber(
        data.risk_score ??
        data.risk_engine?.risk_score,
        0
    );

    const mlIsPhishing = String(ml.classification || "").toLowerCase().includes("phish");
    const isHighRisk = rawClassification === "high_risk" || riskScoreValue >= 60;
    const isSuspicious = rawClassification === "medium_risk" || riskScoreValue >= 30;
    const isUnverifiable =
        data.verifiable === false || rawClassification.includes("unverifiable");

    const prediction =
        mlIsPhishing
            ? "Likely Phishing"
            : isHighRisk
                ? isUnverifiable ? "High Risk (Unverified)" : "High Risk"
                : isSuspicious
                    ? isUnverifiable ? "Suspicious (Unverified)" : "Suspicious"
                    : isUnverifiable ? "Unverified" : "Likely Legitimate";

    return {
        valid: true,
        verifiable: !isUnverifiable,
        url: data.url || "",
        prediction,
        classification:
            data.classification ||
            data.risk_classification ||
            ml.classification ||
            "",
        risk_score: riskScoreValue,
        confidence,
        url_security: security,
        dns,
        ssl,
        ml,
        reasons: Array.isArray(data.reasons)
            ? data.reasons
            : Array.isArray(data.signals)
                ? data.signals
                : Array.isArray(data.url_security_reasons)
                    ? data.url_security_reasons
                    : Array.isArray(ml.signals)
                        ? ml.signals
                        : [],
        risk_explanation: normalizeExplanation(rawExplanation),
        explanation: normalizeExplanation(rawExplanation),
        ir_analysis: data.ir_analysis || null
    };
}

function normalizeExplanation(value) {
    if (Array.isArray(value)) {
        return value
            .filter(item => item !== null && item !== undefined && String(item).trim())
            .map(item => String(item).trim())
            .join(" ");
    }

    if (typeof value === "string") {
        return value.trim();
    }

    return "";
}


function verdictLabel(prediction) {
    if (prediction === "Likely Phishing") return "Likely Phishing";
    if (prediction === "High Risk (Unverified)") return "High Risk · Unverified";
    if (prediction === "High Risk") return "High Risk";
    if (prediction === "Suspicious (Unverified)") return "Suspicious · Unverified";
    if (prediction === "Suspicious") return "Suspicious";
    if (prediction === "Unverified" || prediction === "Unable to verify URL") return "Unable to Verify";
    return "Likely Legitimate";
}


/* =========================================================
   DISPLAY RESULT
   ========================================================= */

function clearSecurityCheck(element, icon) {
    if (element) {
        element.textContent = "--";
        element.classList.remove("secure", "warning", "danger");
    }
    if (icon) {
        icon.textContent = "?";
    }
}

function resetScanDetails(result) {
    const state = result?.failureType || "invalid";
    const isInvalid = state === "invalid";
    const isScanning = state === "scanning";
    const title = isInvalid ? "Invalid URL" : isScanning ? "Analyzing URL" : "Scan Unavailable";
    const message = result?.risk_explanation || (isInvalid
        ? "Invalid URL. Enter a valid hostname such as https://google.com"
        : isScanning
            ? "Running the security and machine-learning checks."
            : "The scan could not be completed. Please try again.");

    if (riskScore) riskScore.textContent = "--";
    if (riskLevel) riskLevel.textContent = isInvalid ? "Invalid URL" : isScanning ? "Analyzing" : "Unavailable";
    if (riskStatus) riskStatus.textContent = isInvalid ? "INVALID" : isScanning ? "SCANNING" : "UNAVAILABLE";
    if (riskGauge) riskGauge.style.strokeDashoffset = "0";
    if (verdictTitle) verdictTitle.textContent = title;
    if (verdictText) verdictText.textContent = title;
    if (verdictIcon) verdictIcon.textContent = isInvalid ? "!" : isScanning ? "…" : "?";
    if (verdictDescription) verdictDescription.textContent = message;
    if (confidenceValue) confidenceValue.textContent = "--";
    if (confidenceBar) confidenceBar.style.width = "0%";
    if (resultStatus) resultStatus.textContent = isInvalid ? "Validation Failed" : isScanning ? "Analyzing" : "Backend Unavailable";

    [
        featureHttpsStatus,
        featureLengthStatus,
        featureIPStatus,
        featureAtStatus,
        featureSubdomainStatus,
        featureSpecialStatus,
        featureShortenerStatus,
        featureKeywordsStatus
    ].forEach(element => {
        if (element) element.textContent = "--";
    });

    clearSecurityCheck(dnsCheckStatus, dnsCheckIcon);
    clearSecurityCheck(sslCheckStatus, sslCheckIcon);
    clearSecurityCheck(urlCheckStatus, urlCheckIcon);
    clearSecurityCheck(mlCheckStatus, mlCheckIcon);

    displayExplanation(result);
    displayIRAnalysis(null, result?.url || "", isScanning ? "Analyzing scan" : "Unavailable");
    updateReport(result);

    if (modelStatus && state === "error") {
        modelStatus.textContent = "Unavailable";
    } else if (modelStatus && isScanning) {
        modelStatus.textContent = "Checking...";
    }
}

function displayResult(result) {

    if (!result || result.valid === false) {
        latestScanResult = null;
        resetScanDetails(result);
        return;
    }

    latestScanResult = result;
    const isUnverifiable = result.verifiable === false;

    const score = safeNumber(
        result.risk_score,
        0
    );

    const confidence = safeNumber(
        result.confidence,
        0
    );

    /* Risk score */

    if (riskScore) {
        riskScore.textContent = score.toFixed(2);
    }

    /* Risk level */

    if (riskLevel) {

        riskLevel.textContent =
            isUnverifiable
                ? "Unverified"
                : score < 30
                ? "Low Risk"
                : score < 60
                    ? "Medium Risk"
                    : "High Risk";
    }

    /* Risk status */

    if (riskStatus) {

        riskStatus.textContent =
            isUnverifiable
                ? "UNVERIFIED"
                : score < 30
                ? "LOW"
                : score < 60
                    ? "MEDIUM"
                    : "HIGH";
    }

    /* Verdict */

    if (verdictTitle) {
        verdictTitle.textContent = verdictLabel(result.prediction);
    }

    if (verdictText) {
        verdictText.textContent = verdictLabel(result.prediction);
    }

    if (verdictDescription) {
        verdictDescription.textContent = getMLVerdictComparison(result)
            || (result.prediction === "Likely Phishing"
                ? "The trained model classified this URL as phishing; this is a prediction, not proof."
                : result.prediction.startsWith("High Risk")
                    ? "The combined risk score is high; this does not by itself mean the classifier predicted phishing."
                    : result.prediction.startsWith("Suspicious")
                        ? "The combined risk score is elevated and should be reviewed."
                        : isUnverifiable
                            ? "The destination could not be fully verified; no safe verdict is asserted."
                            : "The trained model predicts legitimate; this is not a guarantee of safety.");
    }

    /* Confidence */

    if (confidenceValue) {
        confidenceValue.textContent =
            `${confidence.toFixed(1)}%`;
    }

    if (confidenceBar) {
        confidenceBar.style.width =
            `${Math.min(100, confidence)}%`;
    }

    /* Gauge */

    if (riskGauge) {

        const circumference = 314;

        const offset =
            circumference -
            (Math.min(100, score) / 100) *
            circumference;

        riskGauge.style.strokeDasharray =
            `${circumference}`;

        riskGauge.style.strokeDashoffset =
            `${offset}`;
    }

    if (resultStatus) {
        resultStatus.textContent =
            "Analysis Complete";
    }

    displayFeatures(result);

    displaySecurityChecks(result);

    displayExplanation(result);

    displayIRAnalysis(result.ir_analysis);

    if (modelStatus) {
        modelStatus.textContent = result.ml?.classification ? "Available" : "Unavailable";
    }

    updateReport(result);

    updateDashboardStats();
}


/* =========================================================
   INFORMATION RETRIEVAL
   ========================================================= */

function displayIRAnalysis(analysis, currentUrl = "", emptyState = "Unavailable") {
    if (!analysis || typeof analysis !== "object") {
        if (irOverallStatus) {
            irOverallStatus.textContent = emptyState;
        }
        if (irLanguageScore) irLanguageScore.textContent = emptyState === "Analyzing scan" ? "Analyzing..." : "Unavailable";
        if (irLanguageStatus) irLanguageStatus.textContent = emptyState === "Analyzing scan" ? "Awaiting scan result" : "Unavailable";
        if (irSuspiciousTerms) irSuspiciousTerms.textContent = "No data available.";
        if (irPageRankScore) irPageRankScore.textContent = emptyState === "Analyzing scan" ? "Analyzing..." : "Unavailable";
        if (irPageRankRank) irPageRankRank.textContent = "--";
        if (irGraphNodes) irGraphNodes.textContent = "--";
        if (irGraphEdges) irGraphEdges.textContent = "--";
        if (irPageRankStatus) irPageRankStatus.textContent = emptyState === "Analyzing scan" ? "Awaiting scan result" : "Insufficient graph data";
        if (irRecommendations) irRecommendations.innerHTML = "<li>No similar URLs found.</li>";
        if (irRecommendationStatus) irRecommendationStatus.textContent = emptyState === "Analyzing scan" ? "Awaiting scan result" : "Unavailable";
        return;
    }

    const language = analysis.language_model || {};
    const pageRank = analysis.pagerank || {};
    const recommendations = analysis.content_recommendations || {};
    const languageAvailable = language.status === "available";
    const languageInsufficient = language.status !== "available"
        && /required|insufficient/i.test(String(language.message || ""));
    const graphNodeCount = Number(pageRank.graph_nodes);
    const graphEdgeCount = Number(pageRank.graph_edges);
    const pageRankAvailable = pageRank.status === "available"
        && Number.isFinite(graphNodeCount)
        && graphNodeCount > 1
        && Number.isFinite(graphEdgeCount)
        && graphEdgeCount > 0;
    const recommendationsAvailable = recommendations.status === "available";

    if (irOverallStatus) {
        irOverallStatus.textContent = analysis.status === "available"
            ? `IR analysis calculated from ${safeNumber(analysis.corpus_size, 0)} historical URLs.`
            : analysis.message || "IR analysis is temporarily unavailable.";
    }

    const languageScore = language.score;
    if (irLanguageScore) {
        irLanguageScore.textContent = languageAvailable && typeof languageScore === "number" && Number.isFinite(languageScore)
            ? `${(languageScore * 100).toFixed(1)}%`
            : languageInsufficient ? "Insufficient data" : "Unavailable";
    }
    if (irLanguageStatus) {
        irLanguageStatus.textContent = languageAvailable
            ? `${safeNumber(language.training_documents, 0)} labeled history records`
            : languageInsufficient ? "Insufficient corpus data" : language.message || "Language model unavailable";
    }
    if (irSuspiciousTerms) {
        const terms = Array.isArray(language.suspicious_terms)
            ? language.suspicious_terms.filter(term => typeof term === "string" && term.trim())
            : [];
        irSuspiciousTerms.textContent = terms.length ? terms.join(", ") : "No corpus-derived terms identified.";
    }

    const graphScore = pageRank.score;
    if (irPageRankScore) {
        irPageRankScore.textContent = pageRankAvailable && typeof graphScore === "number" && Number.isFinite(graphScore)
            ? graphScore.toFixed(6)
            : pageRank.status === "available" ? "Insufficient data" : "Unavailable";
    }
    if (irPageRankRank) {
        const rank = Number(pageRank.rank);
        irPageRankRank.textContent = pageRankAvailable && Number.isInteger(rank) && rank > 0 ? `#${rank}` : "--";
    }
    if (irPageRankStatus) {
        irPageRankStatus.textContent = pageRankAvailable
            ? "PageRank calculated over the local relationship graph"
            : pageRank.status === "available" ? "Insufficient graph data" : pageRank.message || "PageRank unavailable";
    }
    if (irGraphDetails) {
        irGraphDetails.textContent = pageRank.message
            || "Scan history stores URLs but no observed links; graph ranking is unavailable.";
    }
    if (irGraphNodes) {
        irGraphNodes.textContent = Number.isFinite(graphNodeCount) ? String(graphNodeCount) : "--";
    }
    if (irGraphEdges) {
        irGraphEdges.textContent = Number.isFinite(graphEdgeCount) ? String(graphEdgeCount) : "--";
    }

    let displayedRecommendationCount = 0;
    if (irRecommendations) {
        irRecommendations.innerHTML = "";
        const matches = Array.isArray(recommendations.recommendations)
            ? recommendations.recommendations
            : [];
        const normalizedCurrentUrl = normalizeURLForMatch(currentUrl);
        const validMatches = matches.filter(item =>
            item
            && typeof item.url === "string"
            && item.url.trim()
            && normalizeURLForMatch(item.url) !== normalizedCurrentUrl
            && typeof item.similarity === "number"
            && Number.isFinite(item.similarity)
            && item.similarity > 0
            && item.similarity <= 1
        );
        displayedRecommendationCount = validMatches.length;

        if (!validMatches.length) {
            const item = document.createElement("li");
            item.textContent = "No similar URLs found.";
            irRecommendations.appendChild(item);
        } else {
            validMatches.slice(0, 3).forEach(match => {
                const item = document.createElement("li");
                const url = document.createElement("span");
                const similarity = document.createElement("strong");
                const percentage = match.similarity * 100;
                url.className = "ir-recommendation-url";
                url.textContent = match.url;
                similarity.textContent = `${Math.max(0, Math.min(100, percentage)).toFixed(1)}%`;
                item.append(url, similarity);
                irRecommendations.appendChild(item);
            });
        }
    }
    if (irRecommendationStatus) {
        irRecommendationStatus.textContent = recommendationsAvailable
            ? displayedRecommendationCount
                ? `${displayedRecommendationCount} historical match${displayedRecommendationCount === 1 ? "" : "es"}`
                : "No similar URLs found."
            : recommendations.message || "Recommendations unavailable";
    }
}

function normalizeURLForMatch(value) {
    try {
        const candidate = /^https?:\/\//i.test(String(value || ""))
            ? String(value).trim()
            : `https://${String(value || "").trim()}`;
        const parsed = new URL(candidate);
        const pathname = parsed.pathname.replace(/\/+$/, "");
        return `${parsed.protocol}//${parsed.host}${pathname}${parsed.search}`.toLowerCase();
    } catch {
        return "";
    }
}


/* =========================================================
   FEATURES
   ========================================================= */

function displayFeatures(result) {

    const security = result.url_security || {};
    const url = result.url || "";

    if (featureHttpsStatus) {
        featureHttpsStatus.textContent =
            security.uses_https ? "Secure" : "Warning";
    }

    if (featureLengthStatus) {
        featureLengthStatus.textContent =
            safeNumber(security.url_length, url.length);
    }

    if (featureIPStatus) {
        featureIPStatus.textContent =
            security.has_ip_address ? "Detected" : "Not Detected";
    }

    if (featureAtStatus) {
        featureAtStatus.textContent =
            security.has_at_symbol ? "Detected" : "Not Detected";
    }

    if (featureSubdomainStatus) {
        featureSubdomainStatus.textContent =
            safeNumber(security.subdomain_count, 0);
    }

    if (featureSpecialStatus) {
        featureSpecialStatus.textContent =
            safeNumber(security.special_char_count, 0);
    }

    if (featureShortenerStatus) {
        featureShortenerStatus.textContent =
            isShortenedURL(url) ? "Detected" : "Not Detected";
    }

    const keywordCount = safeNumber(security.suspicious_keyword_count, 0);

    if (featureKeywordsStatus) {
        featureKeywordsStatus.textContent =
            keywordCount > 0 ? `${keywordCount} Detected` : "None Detected";
    }
}


/* =========================================================
   SECURITY CHECKS
   ========================================================= */

function setSecurityCheck(element, text, type) {

    if (!element) return;

    element.textContent = text;

    element.classList.remove(
        "secure",
        "warning",
        "danger"
    );

    element.classList.add(type);
}


function displaySecurityChecks(data) {

    if (!data) {
        return;
    }

    const security = data.url_security || {};
    const dns = data.dns || {};
    const ssl = data.ssl || {};
    const ml = data.ml || {};
    const dnsIsPublic = dns.public !== false;
    const dnsIsVerified = dns.resolves && dnsIsPublic;
    const sslWasChecked = ssl.checked !== false && typeof ssl.valid === "boolean";
    const urlHasIndicators = Boolean(
        security.has_ip_address || security.has_at_symbol || security.suspicious_keyword_count > 0
    );

    setSecurityCheck(
        dnsCheckStatus,
        !dns.resolves ? "Not Resolved" : dnsIsPublic ? "Resolved" : "Blocked: non-public host",
        dnsIsVerified ? "secure" : "warning"
    );

    setSecurityCheck(
        sslCheckStatus,
        !sslWasChecked ? "Not Checked" : ssl.valid ? "Valid" : "Invalid",
        !sslWasChecked ? "warning" : ssl.valid ? "secure" : "warning"
    );

    setSecurityCheck(
        urlCheckStatus,
        urlHasIndicators
            ? "Warning"
            : "Secure",
        urlHasIndicators
            ? "warning"
            : "secure"
    );

    const mlClassification = String(ml.classification || "").toLowerCase();
    const mlPhishing = mlClassification.includes("phish");
    const mlLegitimate = mlClassification.includes("legitimate");
    setSecurityCheck(
        mlCheckStatus,
        mlPhishing ? "Phishing" : mlLegitimate ? "Legitimate" : "Unavailable",
        mlPhishing ? "danger" : mlLegitimate ? "secure" : "warning"
    );

    if (dnsCheckIcon) {
        dnsCheckIcon.textContent = dnsIsVerified ? "✓" : "!";
    }

    if (sslCheckIcon) {
        sslCheckIcon.textContent = !sslWasChecked ? "?" : ssl.valid ? "✓" : "!";
    }

    if (urlCheckIcon) {
        urlCheckIcon.textContent = urlHasIndicators ? "!" : "✓";
    }

    if (mlCheckIcon) {
        mlCheckIcon.textContent = mlPhishing ? "!" : mlLegitimate ? "✓" : "?";
    }
}


/* =========================================================
   EXPLANATION
   ========================================================= */

function displayExplanation(result) {

    const explanationValue = normalizeExplanation(
        result?.risk_explanation || result?.explanation || ""
    );
    const resultMismatch = getMLVerdictComparison(result);

    const fallbackText =
        result?.valid === false
            ? explanationValue || "The scan could not be completed."
            : result?.prediction === "Likely Phishing"
                ? "The trained model classified this URL as phishing; this is a prediction, not proof."
                : result?.prediction.startsWith("High Risk")
                    ? "The combined risk score is high; this does not by itself mean the classifier predicted phishing."
                    : result?.prediction.startsWith("Suspicious")
                        ? "The combined risk score is elevated and should be reviewed."
                        : result?.prediction === "Unverified"
                            ? "The destination could not be fully verified; no safe verdict is asserted."
                            : "The trained model predicts legitimate; this is not a guarantee of safety.";

    const displayText = [resultMismatch, explanationValue || fallbackText]
        .filter(Boolean)
        .join(" ");

    if (explanationTitle) {
        explanationTitle.textContent =
            resultMismatch
                ? "ML result and overall assessment differ"
                : result?.valid === false
                    ? result.failureType === "scanning"
                        ? "Analysis in progress"
                        : result.failureType === "error" ? "Scan unavailable" : "URL validation failed"
                    : result.prediction === "Likely Phishing"
                        ? "Model phishing prediction"
                        : result.prediction.startsWith("High Risk") || result.prediction.startsWith("Suspicious")
                            ? "Elevated risk indicators require review"
                            : "No major phishing indicators detected";
    }

    if (aiExplanation) {
        aiExplanation.textContent = displayText;
    }

    if (explanationText) {
        explanationText.textContent = displayText;
    }

    if (!reasonList) {
        return;
    }

    reasonList.innerHTML = "";

    if (result?.valid === false) {
        const li = document.createElement("li");
        li.textContent = explanationValue || "No data available.";
        reasonList.appendChild(li);
        return;
    }

    let reasons = [];

    if (Array.isArray(result.reasons)) {
        reasons = result.reasons;
    }

    if (reasons.length === 0) {

        const li = document.createElement("li");

        li.textContent =
            result.prediction === "Likely Phishing" || result.prediction.startsWith("High Risk") || result.prediction.startsWith("Suspicious")
                ? "Potentially suspicious URL characteristics were detected."
                : "No additional suspicious indicators were reported.";

        reasonList.appendChild(li);

        return;
    }

    reasons.forEach(reason => {

        if (
            reason !== null &&
            reason !== undefined &&
            String(reason).trim()
        ) {

            const li =
                document.createElement("li");

            li.textContent =
                String(reason);

            reasonList.appendChild(li);
        }
    });
}

function getMLVerdictComparison(result) {
    if (!result || result.valid === false) {
        return "";
    }

    const mlClassification = String(result.ml?.classification || "").toLowerCase();
    const mlVerdict = mlClassification.includes("phish")
        ? "Phishing"
        : mlClassification.includes("legitimate")
            ? "Legitimate"
            : "";
    if (!mlVerdict) {
        return "";
    }

    const risk = safeNumber(result.risk_score, 0).toFixed(2);
    if (mlVerdict === "Legitimate" && (result.classification === "high_risk" || result.classification === "medium_risk")) {
        return `The ML model predicts legitimate, while independent indicators produce a ${result.classification.replace("_", " ")} score of ${risk}/100. This is not a safe verdict.`;
    }
    if (mlVerdict === "Legitimate" && result.verifiable === false) {
        return `The ML model classified the URL as legitimate, but the hostname could not be verified; this result is not presented as safe. The overall risk score is ${risk}/100.`;
    }
    return "";
}

function getIRReportSummary(analysis, currentUrl) {
    if (!analysis || typeof analysis !== "object") {
        return "IR analysis unavailable.";
    }

    const language = analysis.language_model || {};
    const pageRank = analysis.pagerank || {};
    const recommendations = analysis.content_recommendations || {};
    const languageScore = Number(language.score);
    const suspiciousTerms = Array.isArray(language.suspicious_terms)
        ? language.suspicious_terms.filter(term => typeof term === "string" && term.trim())
        : [];
    const languageText = language.status === "available" && Number.isFinite(languageScore)
        ? `Language-model phishing likelihood ${(languageScore * 100).toFixed(1)}% from ${safeNumber(language.training_documents, 0)} labeled records; phishing-associated terms: ${suspiciousTerms.length ? suspiciousTerms.join(", ") : "none identified"}`
        : /required|insufficient/i.test(String(language.message || ""))
            ? "Insufficient corpus data"
            : "Language model unavailable";

    const graphNodes = Number(pageRank.graph_nodes);
    const graphEdges = Number(pageRank.graph_edges);
    const graphScore = Number(pageRank.score);
    const graphText = pageRank.status === "available"
        && graphNodes > 1
        && graphEdges > 0
        && Number.isFinite(graphScore)
        ? `PageRank ${graphScore.toFixed(6)}, rank #${safeNumber(pageRank.rank, 0)}, ${graphNodes} URLs/nodes and ${graphEdges} relationships/edges`
        : pageRank.message || "No observed link relationships; graph ranking unavailable";

    const currentKey = normalizeURLForMatch(currentUrl);
    const matchCount = (Array.isArray(recommendations.recommendations)
        ? recommendations.recommendations
        : []).filter(item => item
            && typeof item.url === "string"
            && normalizeURLForMatch(item.url) !== currentKey
            && typeof item.similarity === "number"
            && Number.isFinite(item.similarity)
            && item.similarity > 0
            && item.similarity <= 1
        ).length;

    return `${languageText}; ${graphText}; ${matchCount} similar historical URL${matchCount === 1 ? "" : "s"}.`;
}


/* =========================================================
   REPORT
   ========================================================= */

function updateReport(result) {

    if (!result || result.valid === false) {
        const failureType = result?.failureType || "invalid";
        const isInvalid = failureType === "invalid";
        const isScanning = failureType === "scanning";

        if (reportUrl) {
            reportUrl.textContent = result?.url || "--";
        }

        if (reportTime) {
            reportTime.textContent = formatDate();
        }

        if (reportVerdict) {
            reportVerdict.textContent = isInvalid ? "Invalid URL" : isScanning ? "Analyzing" : "Unavailable";
        }

        if (reportRiskScore) {
            reportRiskScore.textContent = "--";
        }

        if (reportConfidence) {
            reportConfidence.textContent = "--";
        }

        if (reportStatus) {
            reportStatus.textContent = isInvalid ? "Validation Failed" : isScanning ? "Scanning" : "Backend Error";
        }

        if (reportBadge) {
            reportBadge.textContent = isInvalid ? "INVALID URL" : isScanning ? "SCANNING" : "UNAVAILABLE";
            reportBadge.classList.remove("warning", "danger", "secure");
            reportBadge.classList.add(isInvalid ? "warning" : isScanning ? "warning" : "danger");
        }

        if (reportSummary) {
            reportSummary.textContent = result?.risk_explanation || (isInvalid
                ? "Invalid URL. Enter a valid hostname such as https://google.com"
                : isScanning
                    ? "The current scan is in progress."
                    : "The backend could not complete this scan.");
        }

        if (reportIRSummary) {
            reportIRSummary.textContent = isScanning ? "IR analysis will appear when scanning completes." : "IR analysis unavailable.";
        }

        return;
    }

    if (reportUrl) {
        reportUrl.textContent = result.url || "--";
    }

    if (reportTime) {
        reportTime.textContent = formatDate();
    }

    if (reportVerdict) {
        reportVerdict.textContent = result.prediction;
    }

    if (reportRiskScore) {
        reportRiskScore.textContent =
            safeNumber(result.risk_score, 0).toFixed(2);
    }

    if (reportConfidence) {
        reportConfidence.textContent =
            `${safeNumber(result.confidence, 0).toFixed(1)}%`;
    }

    if (reportStatus) {
        reportStatus.textContent = result.verifiable === false ? "Unverified" : "Completed";
    }

    if (reportBadge) {
        const isMLPhishing = result.prediction === "Likely Phishing";
        const isHighRisk = result.prediction.startsWith("High Risk");
        const isSuspicious = result.prediction.startsWith("Suspicious");
        reportBadge.textContent = isMLPhishing
            ? "MODEL PHISHING PREDICTION"
            : isHighRisk ? "HIGH RISK" : isSuspicious ? "REVIEW REQUIRED" : result.verifiable === false ? "UNVERIFIED" : "LOW RISK";
        reportBadge.classList.remove("warning", "danger", "secure");
        reportBadge.classList.add(
            isMLPhishing || isHighRisk ? "danger" : isSuspicious || result.verifiable === false ? "warning" : "secure"
        );
    }

    if (reportSummary) {
        reportSummary.textContent = getMLVerdictComparison(result)
            || (result.prediction === "Likely Phishing"
                ? "The trained model predicted phishing; this is not proof."
                : result.prediction.startsWith("High Risk")
                    ? "The hybrid score is high; independent indicators and model output should be reviewed separately."
                    : result.prediction.startsWith("Suspicious")
                        ? "The hybrid score is elevated and should be reviewed."
                        : result.verifiable === false
                            ? "The destination could not be fully verified; no safe verdict is asserted."
                            : "The trained model predicts legitimate; this is not a guarantee of safety.");
    }

    if (reportIRSummary) {
        reportIRSummary.textContent = getIRReportSummary(result.ir_analysis, result.url);
    }
}


/* =========================================================
   HISTORY
   ========================================================= */

function getHistory() {
    return historyRecords;
}


function historyPrediction(classification, verifiable) {
    if (verifiable === false) return "Unverified";
    const normalized = String(classification || "").toLowerCase();
    if (normalized === "high_risk") return "High Risk";
    if (normalized === "medium_risk") return "Suspicious";
    if (normalized === "low_risk") return "Low Risk";
    return "Unavailable";
}


async function refreshHistory(showError = false) {
    let loaded = false;
    try {
        const payload = await requestAPI("/api/v1/history");
        if (!Array.isArray(payload)) {
            throw new Error("Backend returned an invalid scan-history response.");
        }
        historyRecords = payload.map(record => ({
            id: record.id,
            url: record.url,
            classification: record.classification,
            verifiable: record.result?.verifiable !== false,
            riskScore: safeNumber(record.risk_score, 0).toFixed(2),
            prediction: historyPrediction(record.classification, record.result?.verifiable),
            confidence: safeNumber(record.confidence, 0) * 100,
            time: record.scan_time || "Unknown time"
        }));
        historyUnavailable = false;
        loaded = true;
    } catch (error) {
        historyUnavailable = true;
        if (showError) {
            showScannerMessage(`Could not refresh scan history: ${error.message}`, "error");
        }
    }
    renderHistory();
    updateDashboardStats();
    return loaded;
}


function renderHistory() {

    const history =
        getHistory();
    const filteredHistory = history.filter(item => {
        if (activeHistoryFilter === "threat") {
            return item.classification === "high_risk";
        }
        if (activeHistoryFilter === "safe") {
            return item.classification === "low_risk" && item.verifiable;
        }
        return true;
    });

    const shouldShowEmptyState = history.length === 0;

    if (emptyHistory) {
        emptyHistory.style.display = shouldShowEmptyState ? "block" : "none";
        const heading = emptyHistory.querySelector("h3");
        const description = emptyHistory.querySelector("p");
        if (heading) heading.textContent = historyUnavailable ? "History Unavailable" : "No Scan History";
        if (description) description.textContent = historyUnavailable
            ? "The backend history could not be loaded. Check the connection and refresh."
            : "Your analyzed URLs will appear here.";
    }

    if (historyTableBody) {

        historyTableBody.innerHTML = "";

        filteredHistory.forEach(item => {

            const row =
                document.createElement("tr");

            row.innerHTML = `
                <td>${escapeHTML(item.time)}</td>
                <td>${escapeHTML(item.url)}</td>
                <td>${escapeHTML(item.riskScore)}</td>
                <td>${escapeHTML(item.prediction)}</td>
                <td>${item.verifiable ? "Completed" : "Unverified"}</td>
            `;

            historyTableBody.appendChild(row);
        });

        if (history.length > 0 && filteredHistory.length === 0) {
            const row = document.createElement("tr");
            const cell = document.createElement("td");
            cell.colSpan = 5;
            cell.className = "history-filter-empty";
            cell.textContent = activeHistoryFilter === "threat"
                ? "No threat scans found."
                : activeHistoryFilter === "safe"
                    ? "No low-risk scans found."
                    : "No scans match this filter.";
            row.appendChild(cell);
            historyTableBody.appendChild(row);
        }
    }

    if (historyList) {

        historyList.innerHTML = "";

        if (history.length === 0 || filteredHistory.length === 0) {

            historyList.innerHTML =
                `<p>${history.length === 0 ? "No Scan History" : "No scans match this filter."}</p>`;

            return;
        }

        filteredHistory.forEach(item => {

            const div =
                document.createElement("div");

            div.className =
                "history-item";

            div.innerHTML = `
                <strong>${escapeHTML(item.url)}</strong>
                <span>Risk: ${escapeHTML(item.riskScore)}</span>
                <span>${escapeHTML(item.prediction)}</span>
            `;

            historyList.appendChild(div);
        });
    }
}


/* =========================================================
   DASHBOARD STATS
   ========================================================= */

function updateDashboardStats() {

    const history =
        getHistory();

    const total =
        history.length;

    const threats =
        history.filter(
            item => item.classification === "high_risk"
        ).length;

    const lowRisk =
        history.filter(
            item => item.classification === "low_risk" && item.verifiable
        ).length;

    if (totalScans) {
        totalScans.textContent =
            total;
    }

    if (threatsDetected) {
        threatsDetected.textContent =
            threats;
    }

    if (safeUrls) {
        safeUrls.textContent =
            lowRisk;
    }
}


async function refreshServiceStatus() {
    const topbarStatus = document.querySelector(".system-status span:last-child");
    const dashboardStatus = document.querySelector(".dashboard-status span:last-child");
    const protectionTitle = document.querySelector(".protection-card strong");
    const protectionDetails = document.querySelector(".protection-card span");

    try {
        const response = await requestAPI("/");
        const modelAvailable = response.model?.available === true;
        const statusText = modelAvailable ? "System Ready" : "ML Model Unavailable";
        if (topbarStatus) topbarStatus.textContent = statusText;
        if (dashboardStatus) dashboardStatus.textContent = modelAvailable ? "Protection Active" : "Partial Checks Available";
        if (protectionTitle) protectionTitle.textContent = modelAvailable ? "Protection Active" : "Checks Limited";
        if (protectionDetails) protectionDetails.textContent = modelAvailable
            ? "System ready for analysis"
            : "DNS, SSL and URL checks available";
        if (modelStatus) modelStatus.textContent = modelAvailable ? "Available" : "Unavailable";
    } catch {
        if (topbarStatus) topbarStatus.textContent = "Backend Unavailable";
        if (dashboardStatus) dashboardStatus.textContent = "Backend Unavailable";
        if (protectionTitle) protectionTitle.textContent = "Backend Unavailable";
        if (protectionDetails) protectionDetails.textContent = "Connect to the local API to scan URLs";
        if (modelStatus) modelStatus.textContent = "Unavailable";
    }
}


/* =========================================================
   MAIN SCAN FUNCTION
   ========================================================= */

async function scanURL() {
    if (scanInProgress) {
        return;
    }

    const validation =
        validateURL(
            urlInput?.value
        );

    if (!validation.valid) {

        setURLValidationMessage(validation.message);
        const invalidResult = {
            valid: false,
            failureType: "invalid",
            url: urlInput?.value?.trim() || "",
            prediction: "Invalid URL",
            risk_explanation: "Invalid URL. Enter a valid hostname such as https://google.com"
        };
        displayResult(invalidResult);

        showScannerMessage(
            invalidResult.risk_explanation,
            "error"
        );

        return;
    }

    setURLValidationMessage("");
    const url =
        validation.url;

    scanInProgress = true;
    hideScannerMessage();

    setLoading(true);
    displayResult({
        valid: false,
        failureType: "scanning",
        url,
        prediction: "Analyzing",
        risk_explanation: "Analysis in progress. Previous scan data has been cleared."
    });

    try {

        const backendData =
            await analyzeWithBackend(url);

        const result =
            convertBackendResult(
                backendData
            );

        displayResult(result);

        if (!result.valid) {
            showScannerMessage(
                result.risk_explanation || "Invalid URL. Enter a valid hostname such as https://google.com",
                "error"
            );
            return;
        }

        const historyLoaded = await refreshHistory();
        showScannerMessage(
            historyLoaded
                ? "URL analysis completed successfully."
                : "URL scan completed, but scan history could not be refreshed.",
            historyLoaded ? "success" : "warning"
        );

    } catch (error) {

        if (error?.status === 400 || error?.status === 422) {
            setURLValidationMessage(error.message || "Please enter a valid HTTP or HTTPS URL.");
            const invalidResult = {
                valid: false,
                failureType: "invalid",
                url,
                prediction: "Invalid URL",
                risk_explanation: error.message || "Invalid URL. Enter a valid hostname such as https://google.com"
            };
            displayResult(invalidResult);
            showScannerMessage(invalidResult.risk_explanation, "error");
            return;
        }

        if (error?.status === 403 && error?.payload?.code === "destination_restricted") {
            const message = "This destination is restricted for security reasons.";
            setURLValidationMessage(message);
            const partial = error.payload.partial_results;
            displayResult({
                valid: false,
                failureType: "error",
                url,
                prediction: "Scan Unavailable",
                risk_explanation: message
            });
            if (partial) {
                displayFeatures({ url, url_security: partial.url_security || {} });
                displaySecurityChecks(partial);
            }
            showScannerMessage(message, "error");
            return;
        }

        console.warn("PhishGuard scan could not complete:", error);
        const partial = error?.payload?.partial_results;
        const message = error?.message || "The scan could not be completed.";

        displayResult({
            valid: false,
            failureType: "error",
            url,
            prediction: "Scan Unavailable",
            risk_explanation: message
        });
        if (partial) {
            displayFeatures({ url, url_security: partial.url_security || {} });
            displaySecurityChecks(partial);
        }
        showScannerMessage(message, "error");

    } finally {
        scanInProgress = false;
        setLoading(false);
    }
}


/* =========================================================
   CLEAR INPUT
   ========================================================= */

function clearURLInput() {

    if (urlInput) {
        urlInput.value = "";
        urlInput.focus();
    }

    setURLValidationMessage("");
    hideScannerMessage();
}


/* =========================================================
   CLEAR HISTORY
   ========================================================= */

async function clearHistory() {
    try {
        await requestAPI("/api/v1/history", { method: "DELETE" });
    } catch (error) {
        showScannerMessage(`Could not clear scan history: ${error.message}`, "error");
        return;
    }

    historyRecords = [];
    historyUnavailable = false;
    activeHistoryFilter = "all";
    historyFilterButtons.forEach(button => {
        const selected = button.dataset.filter === "all";
        button.classList.toggle("active", selected);
        button.setAttribute("aria-pressed", String(selected));
    });

    renderHistory();

    updateDashboardStats();
    showScannerMessage("Scan history cleared.", "success");
}

function setupHistoryFilters() {
    historyFilterButtons.forEach(button => {
        button.setAttribute("aria-pressed", String(button.dataset.filter === activeHistoryFilter));
        button.addEventListener("click", () => {
            activeHistoryFilter = button.dataset.filter || "all";
            historyFilterButtons.forEach(filterButton => {
                const selected = filterButton === button;
                filterButton.classList.toggle("active", selected);
                filterButton.setAttribute("aria-pressed", String(selected));
            });
            renderHistory();
        });
    });
}


/* =========================================================
   PRINT REPORT
   ========================================================= */

function printReport() {
    window.print();
}


function exportReport() {
    if (!latestScanResult) {
        showScannerMessage("Complete a successful scan before exporting a report.", "warning");
        return;
    }

    const report = {
        generated_at: new Date().toISOString(),
        scan: latestScanResult
    };
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const downloadUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = downloadUrl;
    link.download = "phishguard-security-report.json";
    link.click();
    URL.revokeObjectURL(downloadUrl);
}


/* =========================================================
   NAVIGATION
   ========================================================= */

function setupNavigation() {

    const links =
        document.querySelectorAll(
            'a[href^="#"]'
        );

    links.forEach(link => {

        link.addEventListener(
            "click",
            () => {

                const targetSelector =
                    link.getAttribute("href");

                const target = targetSelector && targetSelector.length > 1
                    ? document.querySelector(targetSelector)
                    : null;

                if (target) {
                    setTimeout(() => {
                        target.scrollIntoView({ behavior: "smooth", block: "start" });
                    }, 50);
                }
            }
        );
    });
}


/* =========================================================
   EVENT LISTENERS
   ========================================================= */

if (analyzeBtn) {

    analyzeBtn.addEventListener(
        "click",
        scanURL
    );
}

if (scanAgainBtn) {

    scanAgainBtn.addEventListener(
        "click",
        scanURL
    );
}

if (clearInput) {

    clearInput.addEventListener(
        "click",
        clearURLInput
    );
}

if (clearHistoryBtn) {

    clearHistoryBtn.addEventListener(
        "click",
        clearHistory
    );
}

if (printReportBtn) {

    printReportBtn.addEventListener(
        "click",
        printReport
    );
}

if (exportReportBtn) {
    exportReportBtn.addEventListener("click", exportReport);
}

if (urlInput) {

    urlInput.addEventListener("input", () => {
        if (urlValidationMessage?.textContent) {
            const validation = validateURL(urlInput.value);
            setURLValidationMessage(validation.valid ? "" : validation.message);
        }
    });

    urlInput.addEventListener(
        "keydown",
        event => {

            if (event.key === "Enter") {
                scanURL();
            }
        }
    );
}


/* =========================================================
   STARTUP
   ========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        renderHistory();

        updateDashboardStats();

        refreshServiceStatus();
        refreshHistory();

        setupNavigation();

        setupHistoryFilters();

        console.log(
            "PhishGuard frontend loaded successfully."
        );
    }
);