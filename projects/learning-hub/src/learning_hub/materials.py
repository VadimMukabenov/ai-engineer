"""Keep source Markdown links useful both in Git and in the local classroom."""

from pathlib import Path
from urllib.parse import urlsplit

import markdown
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor


class LessonLinks(Treeprocessor):
    def __init__(self, root: Path, material: Path, catalog: dict):
        super().__init__()
        self.root, self.material = root, material
        self.routes = {
            (root / row["material_path"]).resolve(): f"/lessons/{row['id']}"
            for row in catalog["lessons"]
            if row["state"] == "ready" and row["material_path"]
        }

    def run(self, element):
        for link in element.iter("a"):
            url = urlsplit(link.get("href", ""))
            if url.scheme or url.netloc or not url.path or url.path.startswith("/"):
                continue
            target = (self.material.parent / url.path).resolve()
            if target.is_relative_to(self.root) and target in self.routes:
                link.set("href", self.routes[target] + (f"#{url.fragment}" if url.fragment else ""))


class LinkExtension(Extension):
    def __init__(self, root, material, catalog):
        super().__init__()
        self.processor = LessonLinks(root, material, catalog)

    def extendMarkdown(self, md):
        md.treeprocessors.register(self.processor, "lesson_links", 5)


def render_material(root: Path, material: Path, catalog: dict) -> str:
    return markdown.markdown(
        material.read_text(encoding="utf-8"),
        extensions=["fenced_code", "tables", LinkExtension(root, material, catalog)],
    )
