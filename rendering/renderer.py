

"""
Rendering Subsystem
--------------------
Two renderer backends: an ASCII/text renderer for terminal play and a
matplotlib-based visual renderer for exporting world snapshots as PNGs.
Both consume the same GameState/world-chunk data structures produced by
generation.procgen, so no format conversion is needed between systems.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

TILE_GLYPHS = {"floor": ".", "obstacle": "#", "resource": "$"}
TILE_COLORS = {"floor": "#2b2b2b", "obstacle": "#5a5a5a", "resource": "#c9a227"}


class ASCIIRenderer:
    name = "ascii_renderer"

    def render_chunk(self, chunk):
        lines = []
        for row in chunk["grid"]:
            lines.append("".join(TILE_GLYPHS.get(t, "?") for t in row))
        return "\n".join(lines)

    def render_entities(self, chunk, entities):
        grid = [row[:] for row in [[TILE_GLYPHS.get(t, "?") for t in r] for r in chunk["grid"]]]
        for e in entities:
            if 0 <= e.y < len(grid) and 0 <= e.x < len(grid[0]):
                grid[int(e.y)][int(e.x)] = "@" if e.kind == "player" else e.kind[0].upper()
        return "\n".join("".join(r) for r in grid)


class VisualRenderer:
    name = "visual_renderer"

    def render_chunk_to_png(self, chunk, path, entities=None):
        h, w = chunk["height"], chunk["width"]
        fig, ax = plt.subplots(figsize=(w / 6, h / 6), dpi=120)
        for y, row in enumerate(chunk["grid"]):
            for x, tile in enumerate(row):
                ax.add_patch(plt.Rectangle((x, h - y - 1), 1, 1,
                             color=TILE_COLORS.get(tile, "#000000")))
        if entities:
            for e in entities:
                ax.plot(e.x + 0.5, h - e.y - 0.5, "o",
                        color="red" if e.kind == "player" else "cyan", markersize=6)
        ax.set_xlim(0, w)
        ax.set_ylim(0, h)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(f"biome: {chunk['biome']}", color="white")
        fig.patch.set_facecolor("#111111")
        fig.savefig(path, facecolor="#111111", bbox_inches="tight")
        plt.close(fig)
        return path
