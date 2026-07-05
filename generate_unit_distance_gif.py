from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from PIL import Image


Point = tuple[int, int]
Edge = tuple[Point, Point]


@dataclass(frozen=True)
class FrameData:
    mesh_size: int
    edges: list[Edge]

    @property
    def is_pertinent(self) -> bool:
        return bool(self.edges)


def max_mesh_size(grid_size: int) -> int:
    if grid_size < 2:
        raise ValueError("grid_size doit être >= 2")
    return int(math.hypot(grid_size - 1, grid_size - 1))


def offsets_for_mesh(mesh_size: int, grid_size: int) -> list[tuple[int, int]]:
    if mesh_size < 1:
        raise ValueError("mesh_size doit être >= 1")

    squared = mesh_size * mesh_size
    offsets: set[tuple[int, int]] = set()

    max_delta = min(mesh_size, grid_size - 1)
    for dx in range(0, max_delta + 1):
        dy_sq = squared - dx * dx
        if dy_sq < 0:
            continue

        dy = math.isqrt(dy_sq)
        if dy * dy != dy_sq:
            continue
        if dy > grid_size - 1:
            continue
        if dx == 0 and dy == 0:
            continue

        offsets.add((dx, dy))

    return sorted(offsets)


def unit_edges_for_mesh(grid_size: int, mesh_size: int) -> list[Edge]:
    offsets = offsets_for_mesh(mesh_size, grid_size)
    edges: set[Edge] = set()

    for x in range(grid_size):
        for y in range(grid_size):
            p1 = (x, y)
            for dx, dy in offsets:
                for sx, sy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                    nx = x + sx * dx
                    ny = y + sy * dy
                    if not (0 <= nx < grid_size and 0 <= ny < grid_size):
                        continue
                    if (nx, ny) == p1:
                        continue

                    p2 = (nx, ny)
                    edge = (p1, p2) if p1 <= p2 else (p2, p1)
                    edges.add(edge)

    return sorted(edges)


def frame_data_for_meshes(
    grid_size: int,
    include_non_pertinent: bool,
) -> list[FrameData]:
    frames: list[FrameData] = []
    for mesh in range(1, max_mesh_size(grid_size) + 1):
        edges = unit_edges_for_mesh(grid_size, mesh)
        if include_non_pertinent or edges:
            frames.append(FrameData(mesh_size=mesh, edges=edges))
    return frames


def _to_pixel(
    point: Point,
    grid_size: int,
    image_size: int,
    margin: int,
) -> tuple[int, int]:
    span = image_size - 2 * margin
    if grid_size == 1:
        return margin + span // 2, margin + span // 2

    x, y = point
    px = margin + int(round((x / (grid_size - 1)) * span))
    py = image_size - margin - int(round((y / (grid_size - 1)) * span))
    return px, py


def _require_pillow() -> tuple[type, type]:
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:  # pragma: no cover - runtime dependency guard
        raise SystemExit(
            "Pillow est requis pour générer le GIF. Installez-le avec: pip install pillow"
        ) from exc
    return Image, ImageDraw


def render_frame(
    grid_size: int,
    frame_data: FrameData,
    image_size: int = 900,
    margin: int = 60,
) -> "Image.Image":
    Image, ImageDraw = _require_pillow()
    image = Image.new("RGB", (image_size, image_size), "white")
    draw = ImageDraw.Draw(image)

    for i in range(grid_size):
        p1 = _to_pixel((i, 0), grid_size, image_size, margin)
        p2 = _to_pixel((i, grid_size - 1), grid_size, image_size, margin)
        draw.line((p1, p2), fill=(220, 220, 220), width=1)

        p3 = _to_pixel((0, i), grid_size, image_size, margin)
        p4 = _to_pixel((grid_size - 1, i), grid_size, image_size, margin)
        draw.line((p3, p4), fill=(220, 220, 220), width=1)

    for p1, p2 in frame_data.edges:
        draw.line(
            (
                _to_pixel(p1, grid_size, image_size, margin),
                _to_pixel(p2, grid_size, image_size, margin),
            ),
            fill=(204, 68, 68),
            width=2,
        )

    radius = max(2, int(180 / grid_size))
    for x in range(grid_size):
        for y in range(grid_size):
            cx, cy = _to_pixel((x, y), grid_size, image_size, margin)
            draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill="black")

    status = "pertinent" if frame_data.is_pertinent else "non pertinent"
    caption = (
        f"Grille {grid_size}x{grid_size} | maillage={frame_data.mesh_size} | "
        f"{status} | paires distance 1: {len(frame_data.edges)}"
    )
    draw.rectangle((0, 0, image_size, 38), fill="white")
    draw.text((12, 10), caption, fill="black")

    return image


def generate_gif(
    output_path: Path,
    grid_size: int = 16,
    fps: int = 2,
    include_non_pertinent: bool = False,
) -> None:
    frames_data = frame_data_for_meshes(
        grid_size=grid_size,
        include_non_pertinent=include_non_pertinent,
    )
    if not frames_data:
        raise RuntimeError("Aucun maillage pertinent trouvé pour cette grille.")

    images = [render_frame(grid_size=grid_size, frame_data=fd) for fd in frames_data]
    duration_ms = max(1, int(1000 / max(1, fps)))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    images[0].save(
        output_path,
        save_all=True,
        append_images=images[1:],
        duration=duration_ms,
        loop=0,
        optimize=False,
    )


def _parse_args(args: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Génère un GIF pour visualiser les maillages pertinents du problème "
            "de la distance unitaire d'Erdos."
        )
    )
    parser.add_argument(
        "--grid-size",
        type=int,
        default=16,
        help="Taille de la grille carrée (défaut: 16)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("erdos_unit_distance.gif"),
        help="Chemin du GIF de sortie",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=2,
        help="Images par seconde (défaut: 2)",
    )
    parser.add_argument(
        "--include-non-pertinent",
        action="store_true",
        help="Inclure aussi les maillages sans paire à distance 1",
    )
    return parser.parse_args(args)


def main() -> None:
    ns = _parse_args()
    generate_gif(
        output_path=ns.output,
        grid_size=ns.grid_size,
        fps=ns.fps,
        include_non_pertinent=ns.include_non_pertinent,
    )
    print(f"GIF généré: {ns.output}")


if __name__ == "__main__":
    main()
