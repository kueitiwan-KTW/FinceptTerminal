#include "services/KtwIntelligenceService.h"

#include "auth/AuthManager.h"
#include "core/config/AppConfig.h"
#include "core/logging/Logger.h"
#include "network/http/HttpClient.h"

#include <QJsonDocument>

namespace fincept {

KtwIntelligenceService& KtwIntelligenceService::instance() {
    static KtwIntelligenceService s;
    return s;
}

QString KtwIntelligenceService::type_to_string(DataType type) {
    switch (type) {
        case DataType::News: return "news";
        case DataType::Calendar: return "calendar";
        case DataType::AiAnalysis: return "ai-analysis";
        case DataType::Contradictions: return "contradictions";
    }
    return "news";
}

bool KtwIntelligenceService::is_available() const {
    auto& cfg = AppConfig::instance();
    if (!cfg.use_saas_auth())
        return false;

    // 檢查租戶的 intelligence 功能開關
    const auto& session = auth::AuthManager::instance().session();
    if (!session.authenticated || !session.user_info.is_saas_user)
        return false;

    return session.user_info.saas.fincept_features.intelligence;
}

void KtwIntelligenceService::fetch(DataType type, int limit, Callback cb) {
    fetch(type, limit, {}, std::move(cb));
}

void KtwIntelligenceService::fetch(DataType type, int limit, const QString& category, Callback cb) {
    if (!is_available()) {
        cb({false, "情報室功能不可用", {}, 0, type});
        return;
    }

    QString path = QString("/api/fincept/intelligence?type=%1&limit=%2")
        .arg(type_to_string(type))
        .arg(limit);

    if (!category.isEmpty())
        path += "&category=" + category;

    auto& http = HttpClient::instance();
    http.saas_get(path, [cb, type](Result<QJsonDocument> r) {
        if (r.is_err()) {
            cb({false, QString::fromStdString(r.error()), {}, 0, type});
            return;
        }

        auto obj = r.value().object();
        if (!obj["success"].toBool()) {
            cb({false, obj["error"].toString("取得數據失敗"), {}, 0, type});
            return;
        }

        auto data = obj["data"].toObject();
        QList<IntelligenceItem> items;
        auto items_array = data["items"].toArray();
        for (const auto& item : items_array) {
            items.append(IntelligenceItem::from_json(item.toObject()));
        }

        cb({true, {}, items, data["total"].toInt(), type});
    });
}

} // namespace fincept
