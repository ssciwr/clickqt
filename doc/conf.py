import os
import shutil

# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html


# -- Project information -----------------------------------------------------

project = "clickqt"
# pylint: disable-next=redefined-builtin
copyright = "2022, Dominic Kempf"
author = "Dominic Kempf"

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx_mdinclude",
    "sphinx.ext.autodoc",
    "sphinx_rtd_theme",
    "enum_tools.autoenum",
    "sphinx_qt_documentation",
    "sphinx.ext.graphviz",
]

# Make the documentations order the same as the source order.
autodoc_member_order = "bysource"

# Linking to PySide6 documentation on "https://doc.qt.io/qtforpython-6/"
qt_documentation = "PySide6"

# Add any paths that contain templates here, relative to this directory.
templates_path = []

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]


def copy_readme_resources(app):
    if app.builder.name == "html":
        output_dir = os.path.join(app.outdir, "readme_resources")
        source_dir = os.path.join(app.srcdir, "..", "readme_resources")
        if not os.path.exists(output_dir):
            shutil.copytree(source_dir, output_dir)


def setup(app):
    app.connect("builder-inited", copy_readme_resources)
    app.add_css_file("wide_theme.css")
