#pragma once
#include "core/report/ReportDocument.h"
#include <QScrollArea>
#include <QTextEdit>
#include <QVBoxLayout>
#include <QWidget>

namespace fincept::screens {

// 使用 fincept::report namespace 的型別，避免 MOC 合併 TU 衝突
using ReportComponent = ::fincept::report::ReportComponent;
using ReportMetadata  = ::fincept::report::ReportMetadata;
using ReportTheme     = ::fincept::report::ReportTheme;

/// Center panel — paginated A4 document canvas.
/// Each page is a separate QTextEdit with visible gap between pages,
/// matching Word/LibreOffice-style document layout.
/// Supports drag-and-drop of image files directly onto the canvas.
class DocumentCanvas : public QWidget {
    Q_OBJECT
  public:
    explicit DocumentCanvas(QWidget* parent = nullptr);

    void render(const QVector<ReportComponent>& components, const ReportMetadata& metadata, const ReportTheme& theme,
                int selected_index);

    /// Returns the last (current) page editor — used for export.
    QTextEdit* text_edit() const { return pages_.isEmpty() ? nullptr : pages_.last(); }

  signals:
    void image_dropped(const QString& file_path);

  protected:
    void dragEnterEvent(QDragEnterEvent* e) override;
    void dragMoveEvent(QDragMoveEvent* e) override;
    void dropEvent(QDropEvent* e) override;

  private:
    QScrollArea* scroll_ = nullptr;
    QWidget* container_ = nullptr;
    QVBoxLayout* pages_layout_ = nullptr;
    QVector<QTextEdit*> pages_;

    QTextEdit* new_page(const ReportTheme& theme);
    void clear_pages();
};

} // namespace fincept::screens
