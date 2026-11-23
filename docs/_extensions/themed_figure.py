"""Sphinx directive: theme-aware figures for Furo (only-light / only-dark)."""

from __future__ import annotations

from pathlib import Path

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective

logger = logging.getLogger(__name__)

IMAGES_URI_PREFIX = "/images/"


def _image_uri(filename: str) -> str:
    return IMAGES_URI_PREFIX + filename.lstrip("/").removeprefix("images/")


def _resolve_image(srcdir: Path, filename: str) -> Path:
    name = filename.lstrip("/").removeprefix("images/")
    return (srcdir / "images" / name).resolve()


class ThemedFigure(SphinxDirective):
    """Show different figures in Furo light and dark mode.

    The argument is a **logical id** defined in ``themed_figure_map`` in
    ``conf.py``. Default: ``<name>.svg`` in both themes. Use ``dual_theme`` for a
    separate ``<name>_dark.svg``.

    Example ``conf.py``::

       def _themed_figure(name: str, folder: str, *, dual_theme: bool = False) -> dict[str, str]:
           rel = f"{folder}/{name}"
           light = f"{rel}.svg"
           if dual_theme:
               return {"folder": folder, "dark": f"{rel}_dark.svg", "light": light}
           return {"folder": folder, "dark": light, "light": light}

       themed_figure_map = {
           "ac_node_model": _themed_figure("AC_node_model", "modelling", dual_theme=True),
       }

    Example RST::

       .. themed-figure:: ac_node_model
          :alt: AC node model
          :align: center
          :width: 250

          AC node equivalent circuit
    """

    has_content = True
    required_arguments = 1
    final_argument_whitespace = True
    option_spec = {
        "alt": directives.unchanged,
        "align": directives.unchanged,
        "width": directives.unchanged,
        "height": directives.unchanged,
        "scale": directives.unchanged,
        "light": directives.unchanged,
        "dark": directives.unchanged,
    }

    def run(self) -> list[nodes.Node]:
        figure_id = self.arguments[0].strip()
        mapping = self.config.themed_figure_map

        if figure_id not in mapping:
            raise self.error(
                f"Unknown themed figure {figure_id!r}; add it to themed_figure_map in conf.py"
            )

        entry = mapping[figure_id]
        if not isinstance(entry, dict) or "dark" not in entry:
            raise self.error(
                f"themed_figure_map[{figure_id!r}] must be a dict with 'dark' and 'light' keys"
            )

        srcdir = Path(self.env.srcdir)
        dark_name = self.options.get("dark") or entry["dark"]
        light_name = self.options.get("light") or entry.get("light")

        dark_abs = _resolve_image(srcdir, dark_name)
        if not dark_abs.is_file():
            raise self.error(f"Dark-mode figure not found: images/{dark_name}")

        dark_uri = _image_uri(dark_name)
        if not light_name:
            logger.warning(
                "No 'light' entry for themed figure %r; dark image used in both themes.",
                figure_id,
                location=self.get_location(),
            )
            light_uri = dark_uri
        else:
            light_abs = _resolve_image(srcdir, light_name)
            if not light_abs.is_file():
                logger.warning(
                    "Light-mode figure missing for %r (images/%s); "
                    "dark image used in both themes until the file exists.",
                    figure_id,
                    light_name,
                    location=self.get_location(),
                )
                light_uri = dark_uri
            else:
                light_uri = _image_uri(light_name)

        align = self.options.get("align")
        if align is not None and align not in {"left", "center", "right"}:
            raise self.error(f"align must be left, center, or right (got {align!r})")

        alt = self.options.get("alt", "")
        caption_text = "\n".join(line.strip() for line in self.content if line.strip())
        nodes_out: list[nodes.Node] = []
        for uri, theme_class in ((light_uri, "only-light"), (dark_uri, "only-dark")):
            figure = nodes.figure("", classes=[theme_class])
            if align is not None:
                figure["align"] = align

            image = nodes.image(uri=uri, alt=alt, classes=[theme_class])
            for key in ("width", "height", "scale"):
                if key in self.options:
                    image[key] = self.options[key]
            figure += image

            if caption_text:
                figure += nodes.caption("", "", nodes.Text(caption_text))

            nodes_out.append(figure)
        return nodes_out


def setup(app):
    app.add_config_value("themed_figure_map", {}, True)
    app.add_directive("themed-figure", ThemedFigure)
    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
