/*---
MyHeaderView.h
---*/

#ifndef _MY_HEADER_VIEW_
#define _MY_HEADER_VIEW_

#include <QHeaderView>
#include <QComboBox>
#include <QLineEdit>
#include <QResizeEvent>

#include <iostream>

#define VERTICAL_MARGIN 2

class FilterHorizontalHeaderView : public QHeaderView
{
  Q_OBJECT
  typedef QHeaderView inherited;

public :
  FilterHorizontalHeaderView(QWidget* parent = 0)
  : QHeaderView(Qt::Horizontal, parent)
  , column1_(new QLineEdit(this))
  , column2_(new QComboBox(this))
  , filterHeight_(0)
  {
    column1_->setText("test");
    column2_->addItem("");
    column2_->addItem("1");
    column2_->addItem("2");

    // compute once and for all the height of our filter row
    filterHeight_ = std::max(column1_->sizeHint().height(), column2_->sizeHint().height());

    connect(this, SIGNAL(sectionResized(int, int, int)), SLOT(onSectionResized_(int, int, int)));
  }

  QWidget* filterWidget(int logicalIndex)
  {
      switch (logicalIndex)
      {
        case 0 : return column1_;
        case 1 : return column2_;
        default : return 0;
      }
  }

  virtual QSize sizeHint() const
  {
    QSize inheritedSizeHint = inherited::sizeHint();
    // insert space for our filter row
    return QSize(inheritedSizeHint.width(), inheritedSizeHint.height() +  
        filterHeight_ + 2 * VERTICAL_MARGIN);
  }

public slots :
  void onScroll(int value)
  {
    QRect vg = viewport()->geometry();

    // now let's position our widgets
    int start = visualIndexAt(vg.left());
    int end   = visualIndexAt(vg.right());

    start = (start == -1 ? 0           : start);
    end   = (end   == -1 ? count() - 1 : end);

    repositionFilterRow_(start, end);
  }

protected :
  virtual void updateGeometries()
  {
    QRect vg = viewport()->geometry();

    // add margins to the QHeaderView so that we reserve the remaining space 
    //to position our filter widgets
    setViewportMargins(0, 0, 0, filterHeight_);
    // call parent (which will recompute internal position of sections...)
    inherited::updateGeometries();

    // now let's position our widgets
    int start = visualIndexAt(vg.left());
    int end   = visualIndexAt(vg.right());

    start = (start == -1 ? 0           : start);
    end   = (end   == -1 ? count() - 1 : end);

    repositionFilterRow_(start, end);
  }

private slots :
  void onSectionResized_(int logicalIndex, int oldSize, int newSize)
  {
    // section logicalIndex has just been resized : let's reposition all 
    // visually available widgets on the right of it
    QRect vg  = viewport()->geometry();
    int start = visualIndex(logicalIndex); // visual index !
    int end   = visualIndexAt(vg.right());
    end       = (end == -1 ? count() - 1 : end);

    repositionFilterRow_(start, end);
  }

private :
  void repositionFilterRow_(int start, int end)
  {
    for (int i = start; i <= end; ++i)
    {
      int logical = logicalIndex(i);
      if (isSectionHidden(logical))
      {
          continue;
      }

      QWidget* fWidget = filterWidget(logical);
      if (fWidget != 0)
      {
        fWidget->move(sectionPosition(logical) - offset(), filterHeight_);
        fWidget->resize(sectionSize(logical), filterHeight_);
      }
    }
  }

private :
  QLineEdit* column1_;
  QComboBox* column2_;

  int filterHeight_;
};

#endif // _MY_HEADER_VIEW_

/*---
MyModel.h
---*/

#ifndef _USTENSILE_UI_TEST_MY_MODEL_
#define _USTENSILE_UI_TEST_MY_MODEL_

#include <QAbstractTableModel>

#include <assert.h>

class MyModel : public QAbstractTableModel
{
public :
  // from QAbstractTableModel
  virtual int rowCount(const QModelIndex &parent_index) const
  {
    return 3;
  }

  virtual int columnCount(const QModelIndex &index) const
  {
    return 2;
  }

  virtual QVariant data(const QModelIndex &index, int role) const
  {
    if (role == Qt::DisplayRole)
    {
      return index.row() * columnCount(QModelIndex()) + index.column();
    }

    return QVariant();
  }

  virtual QVariant headerData(int section, Qt::Orientation orientation, 
    int role = Qt::DisplayRole) const
  {
    //std::cout << "section = " << section << ", orientation = " << 
    orientation << (orientation == Qt::Horizontal ? "(HORIZONTAL)":"(N/A)") << ", 
    role = " << role << (role == Qt::DisplayRole ? "(DisplayRole)":"(N/A)") << 
    std::endl;

    if (orientation == Qt::Horizontal && role == Qt::DisplayRole && section >= 0)
    {
      static const char* names[] = {"test1", "test2"};
      assert(section >= 0);
      assert(section < (int)(sizeof(names) / sizeof(const char* )));
      return names[section];
    }

    return QVariant();
  }
};

#endif // _USTENSILE_UI_TEST_MY_MODEL_

/*---
main
---*/

int main(int argc, char** argv)
{
  QApplication app(argc, argv);
  QTableView view;
  MyModel model;
  FilterHorizontalHeaderView header;

  view.setModel(&model);
  view.setHorizontalHeader(&header);
  QObject::connect(view.horizontalScrollBar(), SIGNAL(valueChanged(int)), 
&header, SLOT(onScroll(int)));
  QObject::connect(view.verticalScrollBar(),   SIGNAL(valueChanged(int)), 
&header, SLOT(onScroll(int)));

  view.show();
  int exit_code = app.exec();

  return exit_code;
}