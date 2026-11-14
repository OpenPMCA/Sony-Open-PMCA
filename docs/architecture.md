# Architecture

```
pmca-app.py              entry point
pmca_app/
  main.py                QApplication bootstrap, --check-runtime for packaged builds
  state.py               CameraState and display grouping. Pure Python.
  backend.py             Blocking operations over the pmca package. No Qt.
  ui/
    runtime.py           LogBus (stdout to Activity), Job (thread pool), CameraMonitor
    window.py            Main window, sidebar, camera state, operation lock
    camera_page.py  apps_page.py  tools_page.py  activity_page.py
    widgets.py           Hairline, Rows, ElidedLabel, StatusDot
pmca/                    USB, installer, store, firmware: unchanged protocol layer
```

Pages never call USB or the network. They call `Backend` methods inside `run_job`, and receive results on the GUI thread. Tests replace `Backend` with a fake (`tests/test_app_qt.py`), so the window runs offscreen without a camera.

`pmca-gui.py` is the previous Tk interface. It is not packaged and remains only until its tests are retired.
