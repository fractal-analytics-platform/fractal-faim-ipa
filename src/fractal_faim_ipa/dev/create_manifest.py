"""Generate JSON schemas for tasks and write them to the Fractal manifest."""

from fractal_tasks_core.dev.create_manifest import create_manifest

if __name__ == "__main__":
    PACKAGE = "fractal_faim_ipa"
    docs_link = "https://github.com/fractal-analytics-platform/fractal-faim-ipa"
    create_manifest(package=PACKAGE, docs_link=docs_link)
