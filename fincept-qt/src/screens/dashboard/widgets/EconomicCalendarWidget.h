#pragma once
#include "screens/dashboard/widgets/BaseWidget.h"

#include <QJsonArray>
#include <QLabel>
#include <QScrollArea>
#include <QVBoxLayout>

namespace fincept::screens::widgets {

/// Economic Calendar Widget — 合併 Fincept 原生 API 和 KTW-SaaS 情報室數據
/// Fincept: GET https://api.fincept.in/macro/upcoming-events
/// SaaS:   GET /api/fincept/intelligence?type=calendar
class EconomicCalendarWidget : public BaseWidget {
    Q_OBJECT
  public:
    explicit EconomicCalendarWidget(QWidget* parent = nullptr);

  protected:
    void on_theme_changed() override;

  private:
    void apply_styles();
    void refresh_data();
    void fetch_saas_data();      // KTW SaaS 情報室數據
    void merge_and_populate();   // 合併兩路數據
    void populate(const QJsonArray& events);

    QWidget* header_widget_ = nullptr;
    QFrame* header_sep_ = nullptr;
    QScrollArea* scroll_area_ = nullptr;
    QVBoxLayout* list_layout_ = nullptr;
    QLabel* status_label_ = nullptr;
    QVector<QLabel*> header_labels_;
    QJsonArray last_events_;      // 已合併的最終事件列表
    QJsonArray fincept_events_;   // Fincept 原生數據
    QJsonArray saas_events_;      // SaaS 情報室數據
    int pending_fetches_ = 0;     // 待完成的並行請求計數
};

} // namespace fincept::screens::widgets
