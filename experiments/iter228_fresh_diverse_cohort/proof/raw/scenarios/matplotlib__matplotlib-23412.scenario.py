import matplotlib
matplotlib.use("Agg", force=True)

from matplotlib.backends.backend_agg import RendererAgg
from matplotlib.patches import Rectangle


class RecordingRenderer(RendererAgg):
    def __init__(self):
        super().__init__(80, 80, 100)
        self.dash_offset = None

    def draw_path(self, gc, path, transform, rgbFace=None):
        self.dash_offset = gc.get_dashes()[0]
        return super().draw_path(gc, path, transform, rgbFace)


renderer = RecordingRenderer()
patch = Rectangle((10, 10), 40, 20, fill=False, linewidth=1)
patch.set_linestyle((3, (5, 2)))
patch.draw(renderer)

print("RESULT=" + repr(renderer.dash_offset))
