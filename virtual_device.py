"""Virtual device that mimics the OpenRazer device API for preview rendering."""


class VirtualMatrix:
    """Mimics device.fx.advanced.matrix with __getitem__/__setitem__."""

    def __init__(self, rows, cols):
        self._data = [[(0, 0, 0)] * cols for _ in range(rows)]
        self.rows = rows
        self.cols = cols

    def __setitem__(self, key, value):
        r, c = key
        if 0 <= r < self.rows and 0 <= c < self.cols:
            self._data[r][c] = tuple(value)

    def __getitem__(self, key):
        r, c = key
        if 0 <= r < self.rows and 0 <= c < self.cols:
            return self._data[r][c]
        return (0, 0, 0)


class VirtualAdvanced:
    """Mimics device.fx.advanced."""

    def __init__(self, rows=6, cols=16, on_draw=None):
        self.rows = rows
        self.cols = cols
        self.matrix = VirtualMatrix(rows, cols)
        self._on_draw = on_draw

    def draw(self):
        if self._on_draw:
            snapshot = [row[:] for row in self.matrix._data]
            self._on_draw(snapshot)


class VirtualFx:
    def __init__(self, advanced):
        self.advanced = advanced


class VirtualDevice:
    """Drop-in replacement for openrazer device, for preview rendering."""

    def __init__(self, rows=6, cols=16, on_draw=None):
        self.name = "Virtual Preview"
        self.fx = VirtualFx(VirtualAdvanced(rows, cols, on_draw))


def detect_dimensions(fallback_rows=6, fallback_cols=16):
    """Try to detect keyboard dimensions from OpenRazer, fall back to defaults."""
    try:
        from device import get_device
        dev = get_device(retries=1, retry_delay=0)
        if dev:
            return dev.fx.advanced.rows, dev.fx.advanced.cols
    except Exception:
        pass
    return fallback_rows, fallback_cols
