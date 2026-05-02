// src/services/maritime/MaritimeTypes.h
#pragma once
#include <QColor>
#include <QString>
#include <QStringList>
#include <QVector>

namespace fincept::services::maritime {

// ── Vessel data from API ────────────────────────────────────────────────────

struct VesselData {
    int id = 0;
    QString imo;
    QString name;
    double latitude = 0;
    double longitude = 0;
    double speed = 0;
    double angle = 0;
    QString from_port;
    QString to_port;
    QString from_date;
    QString to_date;
    double route_progress = 0;
    double draught = 0;
    QString last_updated;
    QString fetched_at;
};

// ── Trade route corridor (derived from current vessel set, not hardcoded) ──
//
// Built at runtime by aggregating loaded vessels on (from_port, to_port).
// `value` is left empty since the API does not expose trade-volume figures —
// the column is kept for future enrichment.

struct TradeRoute {
    QString name;
    QString value;
    QString status;  // active, delayed, critical (left empty when not derivable)
    int vessels = 0;
    double start_lat = 0, start_lng = 0;
    double end_lat = 0, end_lng = 0;
};

inline QColor route_status_color(const QString& status) {
    if (status == QStringLiteral("critical"))
        return QColor("#FF0000");
    if (status == QStringLiteral("delayed"))
        return QColor("#FFD700");
    if (status == QStringLiteral("active"))
        return QColor("#00FF00");
    return QColor("#888888");
}

// ── Page envelope for area-search / multi-vessel responses ──────────────────
//
// Wraps the parsed vessel list with the new credit metering + result counts
// the API returns. `not_found` is populated by multi-vessel when caller
// requested IMOs that aren't in the database.

struct VesselsPage {
    QVector<VesselData> vessels;
    int total_count = 0;       // server-reported total ("vessel_count" / "found_count")
    int found_count = 0;       // multi-vessel only
    QStringList not_found;     // multi-vessel only — IMOs missing from DB
    double credits_used = 0.0;
    int remaining_credits = -1; // -1 = unknown / not reported
};

struct VesselHistoryPage {
    QString imo;
    QVector<VesselData> history; // sorted newest-first
    int total_records = 0;
    double credits_used = 0.0;
    int remaining_credits = -1;
};

// ── Area search params ──────────────────────────────────────────────────────

struct AreaSearchParams {
    double min_lat = 0;
    double max_lat = 0;
    double min_lng = 0;
    double max_lng = 0;
    int days_ago = 0;
};

// ── Legacy types still used by MaritimeScreen.cpp ───────────────────────────

struct IntelligenceData {
    QString threat_level; // low, medium, high, critical
    int active_vessels = 0;
    int monitored_routes = 48;
    QString trade_volume = "$847.3B";
};

inline QColor threat_color(const QString& level) {
    if (level == "critical")
        return QColor("#FF0000");
    if (level == "high")
        return QColor("#FF6600");
    if (level == "medium")
        return QColor("#FFD700");
    return QColor("#00FF00"); // low
}

struct PresetPort {
    QString name;
    double lat;
    double lng;
};

inline QVector<PresetPort> preset_ports() {
    return {
        {"Mumbai (JNPT)", 18.9500, 72.9500},
        {"Singapore",      1.2644, 103.8200},
        {"Rotterdam",     51.9000,   4.5000},
        {"Shanghai",      31.3600, 121.6200},
        {"Dubai (Jebel Ali)", 25.0200, 55.0600},
        {"Los Angeles",   33.7400, -118.2700},
    };
}

// ── Hardcoded default trade routes (legacy, used by MaritimeScreen.cpp) ─────

inline QVector<TradeRoute> default_trade_routes() {
    return {
        {"Strait of Malacca",  "$45B",  "active",  127, 2.5, 101.5, 1.3, 103.8},
        {"Suez Canal",         "$150B", "active",  89,  30.0, 32.3, 31.3, 32.6},
        {"Panama Canal",       "$80B",  "delayed", 45,  8.9, -79.5, 9.4, -79.9},
        {"Strait of Hormuz",   "$120B", "active",  156, 26.5, 56.0, 26.6, 56.5},
        {"Cape of Good Hope",  "$25B",  "active",  34,  -34.3, 18.5, -34.8, 20.0},
        {"South China Sea",    "$3.4T", "critical",267, 10.0, 112.0, 20.0, 118.0},
        {"English Channel",    "$15B",  "active",  78,  50.9, 1.0, 51.0, 1.5},
        {"Bab el-Mandeb",      "$90B",  "active",  45,  12.6, 43.3, 12.4, 43.5},
        {"Taiwan Strait",      "$2.5T", "critical",189, 24.0, 118.5, 25.5, 120.0},
        {"Mozambique Channel", "$8B",   "active",  23,  -15.0, 41.0, -23.0, 43.0},
    };
}

} // namespace fincept::services::maritime

#include <QMetaType>
Q_DECLARE_METATYPE(fincept::services::maritime::VesselData)
Q_DECLARE_METATYPE(fincept::services::maritime::VesselsPage)
Q_DECLARE_METATYPE(fincept::services::maritime::VesselHistoryPage)
Q_DECLARE_METATYPE(QVector<fincept::services::maritime::VesselData>)
