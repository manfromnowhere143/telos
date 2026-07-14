import matplotlib
matplotlib.use("Agg", force=True)

from matplotlib.backend_bases import RendererBase
from matplotlib.patches import Rectangle


class CaptureRenderer(RendererBase):
    def __init__(self):
        super().__init__()
        self.dashes = []

    def draw_path(self, gc, path, transform, rgbFace=None):
        offset, pattern = gc.get_dashes()
        self.dashes.append((float(offset), tuple(float(x) for x in pattern)))


renderer = CaptureRenderer()
patch = Rectangle(
    (0, 0), 1, 1,
    fill=False,
    linewidth=1,
    linestyle=(2.5, (10, 10)),
)
patch.draw(renderer)

print("RESULT=" + repr(tuple(renderer.dashes)))
