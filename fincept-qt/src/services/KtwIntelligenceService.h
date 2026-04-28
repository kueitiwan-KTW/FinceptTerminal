#pragma once
#include "auth/AuthTypes.h"
#include "core/result/Result.h"

#include <QJsonArray>
#include <QJsonObject>
#include <QObject>

#include <functional>

namespace fincept {

/// KTW SaaS 情報室數據服務
/// 透過 /api/fincept/intelligence 取得新聞、經濟日曆、AI 分析、矛盾偵測等數據
class KtwIntelligenceService : public QObject {
    Q_OBJECT
  public:
    static KtwIntelligenceService& instance();

    // 情報室數據類型
    enum class DataType {
        News,           // 新聞
        Calendar,       // 經濟日曆
        AiAnalysis,     // AI 分析
        Contradictions  // 矛盾偵測
    };

    struct IntelligenceItem {
        QString id;
        QString title;
        QString content;
        QString category;
        QString source;
        QString published_at;
        QJsonObject raw;  // 原始 JSON

        static IntelligenceItem from_json(const QJsonObject& obj) {
            IntelligenceItem item;
            item.id = obj["id"].toString();
            item.title = obj["title"].toString();
            item.content = obj["content"].toString();
            item.category = obj["category"].toString();
            item.source = obj["source"].toString();
            item.published_at = obj["published_at"].toString();
            item.raw = obj;
            return item;
        }
    };

    struct IntelligenceResult {
        bool success = false;
        QString error;
        QList<IntelligenceItem> items;
        int total = 0;
        DataType type;
    };

    using Callback = std::function<void(IntelligenceResult)>;

    /// 取得情報室數據
    void fetch(DataType type, int limit, Callback cb);
    void fetch(DataType type, int limit, const QString& category, Callback cb);

    /// 檢查情報室功能是否可用（需 SaaS 模式 + finceptIntelligenceEnabled）
    bool is_available() const;

  private:
    KtwIntelligenceService() = default;

    static QString type_to_string(DataType type);
};

} // namespace fincept
