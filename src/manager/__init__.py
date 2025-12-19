#! /usr/bin/python

import difflib
import glob
import logging
import os
import re
import shlex
import shutil
import subprocess
import sys
import textwrap
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Generator, Iterator, Optional, Union

import click
from jinja2 import Environment, FileSystemLoader

logging.basicConfig(
    format="%(levelname)s %(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)


basepath: Path = Path.cwd()
"""The parent directory of the meta repository (https://github.com/TeXLuaCATS/meta)."""


def set_basepath(path: Union[str, Path]) -> None:
    global basepath
    basepath = Path(path)


text_blocks = {
    "copyright_notice": f"""-- -----------------------------------------------------------------------------
-- Copyright (C) 2022-{datetime.now().year} by Josef Friedrich <josef@friedrich.rocks>
-- -----------------------------------------------------------------------------
--
-- This program is free software: you can redistribute it and/or modify it
-- under the terms of the GNU General Public License as published by the
-- Free Software Foundation, either version 2 of the License, or (at your
-- option) any later version.
--
-- This program is distributed in the hope that it will be useful, but
-- WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
-- Public License for more details.
--
-- You should have received a copy of the GNU General Public License along
-- with this program. If not, see <https://www.gnu.org/licenses/>.
--
-- -----------------------------------------------------------------------------""",
    "navigation_table_help": """-- The `_N` table makes it easier to navigate through the type definitions with
-- the help of the outline:
-- https://github.com/TeXLuaCATS/meta?tab=readme-ov-file#navigation-table-_n""",
}


class Color:
    """ANSI color codes

    Source: https://gist.github.com/rene-d/9e584a7dd2935d0f461904b9f2950007
    """

    BLACK = "\033[0;30m"
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    BROWN = "\033[0;33m"
    BLUE = "\033[0;34m"
    PURPLE = "\033[0;35m"
    CYAN = "\033[0;36m"
    LIGHT_GRAY = "\033[0;37m"
    # DARK_GRAY = "\033[1;30m"
    # LIGHT_RED = "\033[1;31m"
    # LIGHT_GREEN = "\033[1;32m"
    # YELLOW = "\033[1;33m"
    # LIGHT_BLUE = "\033[1;34m"
    # LIGHT_PURPLE = "\033[1;35m"
    # LIGHT_CYAN = "\033[1;36m"
    # LIGHT_WHITE = "\033[1;37m"
    # BOLD = "\033[1m"
    # FAINT = "\033[2m"
    # ITALIC = "\033[3m"
    # UNDERLINE = "\033[4m"
    # BLINK = "\033[5m"
    # NEGATIVE = "\033[7m"
    # CROSSED = "\033[9m"
    END = "\033[0m"

    @staticmethod
    def _apply_color(color: str, text: Any) -> str:
        return color + str(text) + Color.END

    @staticmethod
    def red(text: Any) -> str:
        return Color._apply_color(Color.RED, text)

    @staticmethod
    def green(text: Any) -> str:
        return Color._apply_color(Color.GREEN, text)


def _run_stylua(path: Path | str) -> None:
    subprocess.check_call(
        [
            "/usr/local/bin/stylua",
            "--config-path",
            basepath / "stylua.toml",
            path,
        ]
    )


def _run_pygmentize(
    path: Optional[Union[Path, str]] = None, stdin: Optional[str] = None
) -> None:
    if not path and not stdin or path and stdin:
        raise Exception(f"Specify path OR content, got: path: {path} stdin: {stdin}")

    if path:
        subprocess.check_call(
            [
                "pygmentize",
                path,
            ]
        )

    elif stdin:
        process = subprocess.Popen(
            ["pygmentize", "-l", "lua"], stdin=subprocess.PIPE, text=True
        )
        process.communicate(input=stdin)


def _diff(a: str, b: str) -> None:
    for line in difflib.unified_diff(a.splitlines(), b.splitlines(), n=1):
        if line.startswith("-"):
            print(Color.RED + line + Color.END)
        elif line.startswith("+"):
            print(Color.GREEN + line + Color.END)
        elif line.startswith("@@"):
            print(Color.PURPLE + line + Color.END)
        else:
            print(line)


def _copy_directory(
    src: str | Path, dest: str | Path, delete_dest: bool = True
) -> None:
    """
    Copies the contents of the source directory to the destination directory.

    If the destination directory exists, it is first removed along with all its contents.
    Then, the source directory is copied to the destination path.

    Args:
        src: Path to the source directory to copy.
        dest: Path to the destination directory.
    """
    if isinstance(dest, str):
        dest = Path(dest)
    if dest.exists() and delete_dest:
        shutil.rmtree(dest)
    shutil.copytree(src, dest, dirs_exist_ok=True)


def _download_url(url: str, dest_path: str) -> None:
    logger.debug("Download %s into %s", Color.red(url), Color.green(dest_path))
    with urllib.request.urlopen(url) as response:
        data = response.read()
        with open(dest_path, "wb") as f:
            f.write(data)


class TextFile:
    path: Path
    orig_content: str
    content: str

    def __init__(self, path: Union[str, Path]) -> None:
        if isinstance(path, str):
            path = Path(path)
        self.path = path
        if not self.path.exists():
            self.path.touch()
        self.content = self.path.read_text()
        self.orig_content = self.content

    def __str__(self) -> str:
        return str(self.path)

    @property
    def filename(self) -> str:
        return self.path.name

    def write(self, text: str) -> None:
        """
        Writes the given text to the file at the specified path and updates the content attribute.

        Args:
            text: The text to be written to the file.

        Logs:
            Logs an informational message indicating the file path where the text is written.
        """
        logger.info("Write to %s", Color.green(self.path))
        self.path.write_text(text)
        self.content = text

    def prepend(self, text: str, save: bool = False) -> str:
        """
        Prepends the given text to the current content, removes duplicate empty lines,
        and optionally saves the updated content.

        Args:
            text: The text to prepend to the current content.
            save: If True, saves the updated content. Defaults to False.

        Returns:
            str: The finalized content after prepending and processing.
        """
        self.content = text + "\n" + self.content
        self.remove_duplicate_empty_lines()
        return self.finalize(save)

    def append(self, text: str, save: bool = False) -> str:
        """
        Appends the given text to the current content and optionally saves the result.

        Args:
            text: The text to append to the current content.
            save: If True, the content will be saved after appending. Defaults to False.

        Returns:
            str: The finalized content after appending the text.
        """
        self.content = self.content + "\n" + text
        self.remove_duplicate_empty_lines()
        return self.finalize(save)

    def replace(self, old: str, new: str, save: bool = False) -> str:
        """
        Replaces occurrences of a substring with a new string in the content.

        Args:
            old: The substring to be replaced.
            new: The string to replace the old substring with.
            save: If True, saves the changes after replacement. Defaults to False.

        Returns:
            str: The updated content after the replacement.
        """
        self.content = self.content.replace(old, new)
        return self.finalize(save)

    def remove_duplicate_empty_lines(self, save: bool = False) -> str:
        """
        Removes consecutive duplicate empty lines from the content.

        Args:
            save: If True, saves the modified content. Defaults to False.

        Returns:
            str: The finalized content after removing duplicate empty lines.
        """
        self.content = re.sub("\n\n+", "\n\n", self.content)
        return self.finalize(save)

    def remove_return_statement(self, save: bool = False) -> str:
        """
        Removes all 'return' statements from the content.

        This method uses a regular expression to find and remove lines that
        start with the keyword 'return', followed by any content, in the stored
        content. Optionally, the updated content can be saved.

        Args:
            save: If True, the updated content will be saved. Defaults
            to False.

        Returns:
            str: The finalized content after removing 'return' statements.
        """
        self.content = re.sub(r"^return .+\n?", "", self.content, flags=re.MULTILINE)
        return self.finalize(save)

    def convert_local_to_global_table(self, save: bool = False) -> str:
        """
        Converts the first occurrence of a Lua-style local table declaration
        to a global table declaration within the content. The conversion
        changes a line like `local table_name = {}` to `table_name = {}`.

        Args:
            save: If True, the changes will be saved. Defaults to False.

        Returns:
            str: The finalized content after the conversion.
        """
        self.content = re.sub(
            r"^local ([a-z_][a-z_0-9]*) ?= ?\{ ?\}",
            r"\1 = {}",
            self.content,
            count=1,
            flags=re.MULTILINE,
        )
        return self.finalize(save)

    def remove_double_dash_comments(self, save: bool = False) -> str:
        """
        Removes lines from the content that are single-line comments starting with
        a double dash (`--`) but not followed by another dash (e.g., `---`).

        Args:
            save (bool): If True, the changes will be saved. Defaults to False.

        Returns:
            str: The finalized content after removing the specified lines.
        """
        content: list[str] = []
        for line in self.content.splitlines():
            if not re.match(r"^(--[^-].*|--)$", line):
                content.append(line)
        self.content = "\n".join(content)
        return self.finalize(save)

    def remove_navigation_table(self, save: bool = False) -> str:
        """
        Removes the navigation table and associated metadata from the content.

        This method performs the following actions:
        - Removes a helper table used for navigating the documentation.
        - Deletes lines starting with `_N` that represent the navigation table.
        - Removes duplicate empty lines from the content.
        - Strips leading and trailing whitespace from the content.

        Args:
            save (bool): If True, the changes will be saved. Defaults to False.

        Returns:
            str: The finalized content after modifications.
        """

        self.content = self.content.replace(
            "-- The `_N` table makes it easier to navigate through the type definitions with\n"
            + "-- the help of the outline:\n"
            + "-- https://github.com/TeXLuaCATS/meta?tab=readme-ov-file#navigation-table-_n\n",
            "",
        )
        # Remove the navigation table
        self.content = re.sub(r"^_N.+\n", "", self.content, flags=re.MULTILINE)

        self.remove_duplicate_empty_lines()
        # Remove leading and trailing whitespace
        self.content = self.content.strip() + "\n"
        return self.finalize(save)

    def clean_docstrings(self, save: bool = False) -> str:
        """
        Cleans and formats the docstrings in the content by applying various transformations.

        This method performs the following operations:
        - Ensures that docstrings start with an empty comment line.
        - Removes duplicate empty comment lines.
        - Limits the number of consecutive empty lines to one.

        Args:
            save (bool): If True, saves the cleaned content. Defaults to False.

        Returns:
            str: The finalized and cleaned content.
        """
        # Start a docstring with an empty comment line.
        self.content = re.sub(r"\n\n---(?=[^\n])", r"\n\n---\n---", self.content)

        # Remove duplicate empty comment lines.
        self.content = re.sub("\n---(\n---)+\n", "\n---\n", self.content)

        self.content = self.content.replace("\n\n---\n\n", "\n\n")

        # Allow only one empty line
        self.remove_duplicate_empty_lines()

        # Side effect with code examples in Lua docstrings
        # content = content.replace(") end\n---", ") end\n\n---")

        # Add an empty comment line before the @param annotation.
        # content = re.sub(
        #     r"(?<!\n---)\n---@param(?=.*?\n.*?@param)", r"\n---\n---@param", content
        # )
        return self.finalize(save)

    def convert_html_to_lua(self, save: bool = False) -> str:
        """
        Converts the HTML content in `self.content` to a Lua-compatible format.

        This method performs the following transformations:
        - Replaces `<tt>` or `<code>` tags with backticks (`).
        - Replaces `<pre>` tags with triple backticks (```).
        - Converts `<li>` tags to Markdown-style list items (`* `).
        - Removes all other HTML tags.
        - Prefixes each line with `---` to format it as a Lua comment.

        Args:
            save (bool): If True, saves the converted content. Defaults to False.

        Returns:
            str: The converted Lua-compatible content.
        """
        self.content = re.sub(
            r"</?(tt|code)>",
            "`",
            self.content,
        )
        self.content = re.sub(
            r"</?pre.*?>",
            "```",
            self.content,
        )
        self.content = re.sub(r"<li> *", "* ", self.content)
        self.content = re.sub(r"</?.*?> *", "", self.content)
        self.content = "---" + self.content.replace("\n", "\n---")
        return self.finalize(save)

    def convert_tex_to_lua(self, save: bool = False) -> str:
        """
        Converts TeX-based content to Lua-compatible format by applying a series of
        regular expression substitutions and string replacements. The method processes
        the content to transform TeX commands, symbols, and formatting into a Lua-friendly
        representation.

        Args:
            save (bool): If True, saves the modified content after processing. Defaults to False.

        Returns:
            str: The processed content in Lua-compatible format.
        """

        tuple[tuple[str, str]]

        replacements = (
            (r"(\n|^)% .*\n", ""),
            (
                r"\\(type|typ|prm|lpr|nod|syntax|notabene|whs|cbk)[\s]*\{([^}]*)\}",
                r"`\2`",
            ),
            (
                r"\\libidx\s*\{(.*?)\}\s*\{(.*?)\}",
                r"`\1.\2`",
            ),
            (
                r"\\(hyphenatedurl)[\s]*\{([^}]*)\}",
                r"\2",
            ),
            (r"\\quot(e|ation)\s*\{([^}]*)\}", r"“\2”"),
            (r"\$([^$]+)\$", r"`\1`"),
            (r"\\TEX\\?", "*TeX*"),
            (r"\\ETEX\\?", "*e-TeX*"),
            (r"\\CONTEXT\\?", "*ConTeXt*"),
            (r"\\LUATEX\\?", "*LuaTeX*"),
            (r"\\LUA\\?", "*Lua*"),
            (r"\\PDFTEX\\?", "*pdfTeX*"),
            (r"\\PDF\\?", "*PDF*"),
            (r"\\DVI\\?", "*DVI*"),
            (r"\\OPENTYPE\\?", "*OpenType*"),
            (r"\\TRUETYPE\\?", "*TrueType*"),
            (r"\\MICROSOFT\\?", "*Microsoft*"),
            (r"\\FONTFORGE\\?", "*FontForge*"),
            (r"\\POSTSCRIPT\\?", "*PostScript*"),
            (r"\\UTF-?8?\\?", "*UTF-8*"),
            (r"\\UNICODE\\?", "*Unicode*"),
            (r"\\(environment|startcomponent) .*\n", ""),
            (r"\\(starttyping|startfunctioncall|stoptyping|stopfunctioncall)", "```"),
            (r"\\startitemize(\[[^]]*\])?", ""),
            (r"\\startitem\s*", "* "),
            (r"\\stopitem(ize)?", ""),
            ("~", " "),
            (r"\|-\|", "-"),
            (r"\|/\|", "/"),
            (r"\\NC \\NR", ""),
            (r"\\(NC|NR|DB|BC|LL|TB|stoptabulate)", ""),
            (r"\\starttabulate\[.*?\]", ""),
            (r"etc\\.\\", "etc."),
            (
                r"\\start(sub)*(section|chapter)*\[.*title=\{(.*?)\}\]",
                r"# \3",
            ),
            (r"\\(sub)*section\{(.*?)\}", r"# \2"),
            (r"\\(libindex|topicindex)\s*\{[^}]+\}", ""),
            (
                r"\\stop(sub)*section",
                "",
            ),
            (
                r"--- `(.*)` +(float|string|boolean|number|table|.*node) +",
                r"---@field \1 \2 # ",
            ),
            (r"\\unknown\\", "..."),
            (r"\n--- {10,}", " "),
            (r"[ \t]*\n", "\n"),
        )

        for pattern, replacement in replacements:
            self.content = re.sub(pattern, replacement, self.content)

        self.content = "---" + self.content.replace("\n", "\n---")
        self.content = re.sub(r"---\n(---\n)+", "---\n", self.content)
        return self.finalize(save)

    def create_navigation_table(self) -> None:
        self.content = re.sub(
            r"[^\w\n]",
            "_",
            self.content,
        )
        self.content = re.sub(
            r"__+",
            "_",
            self.content,
        )
        self.content = re.sub(
            r"_\n",
            "\n",
            self.content,
        )
        self.content = re.sub(
            r"\n(?=\w)",
            "\n_N._",
            self.content,
        )
        self.content = re.sub(
            r"(?<=\w)\n",
            " = 0\n",
            self.content,
        )
        self.save()

    def convert_links_to_templates(self, save: bool = False) -> str:
        def __replace(match: re.Match[str]) -> str:
            caption = match.group("caption")
            url = match.group("url")
            hash = match.group("hash")[:7]
            relpath = match.group("relpath")
            lines = match.group("lines").replace("L", "").split("-")
            start_line: int
            end_line: Optional[int] = None

            argument: str
            start_line = int(lines[0])
            if len(lines) == 2:
                end_line = int(lines[1])
                argument = f"{hash}:{relpath}:{start_line}:{end_line}"
            else:
                argument = f"{hash}:{relpath}:{start_line}"

            function_name: Optional[str] = None
            if (
                caption == "Corresponding C source code"
                and url == "https://gitlab.lisn.upsaclay.fr/texlive/luatex/-/blob"
            ):
                function_name = "luatex_c"

            if not function_name:
                return match.group(0)

            return "* {{ " + function_name + "('" + argument + "') }}"

        self.content = re.sub(
            r"\* (?P<caption>.+): \[.+\]\((?P<url>.+)/(?P<hash>[a-fA-F0-9]{40,})/(?P<relpath>.*)#(?P<lines>[L0-9-]+)\)",
            __replace,
            self.content,
        )

        return self.finalize(save)

    def render_templates(self, repo: "Repository", save: bool = False) -> str:
        env = Environment(loader=FileSystemLoader(self.path.parent))

        def luatex_c(
            commit_id: str,
            relpath: str,
            start_line: int,
            end_line: Optional[int] = None,
        ) -> str:
            if len(commit_id) == 7:
                commit_id = commit_ids[commit_id]
            lines_url: str
            lines_text: str
            if end_line is not None:
                lines_url = f"L{start_line}-{end_line}"
                lines_text = f"Lines {start_line}-{end_line}"
            else:
                lines_url = f"L{start_line}"
                lines_text = f"Line {start_line}"
            return f"Corresponding C source code: [{relpath} {lines_text}](https://gitlab.lisn.upsaclay.fr/texlive/luatex/-/blob/{commit_id}/source/texk/web2c/luatexdir/{relpath}#{lines_url})"

        env.globals = {
            "luatex_c": luatex_c,
            "contribute": f"😱 [Types]({repo.get_github_blob_url(filename=self.filename)}) incomplete or incorrect? 🙏 [Please contribute!]({repo.github_pull_request_url})",
        }

        template = env.get_template(self.path.name)
        self.content = template.render()
        return self.finalize(save)

    def rewrap(self, save: bool = False) -> str:
        """The Rewrap extension (https://github.com/dnut/Rewrap) does not support rewraping of thee hyphens prefixed comment lines."""
        if self.content == "":
            return ""
        lines: list[str] = []
        is_fenced_code_block = False

        to_rewrap: list[str] = []
        for line in self.content.splitlines():
            if line.startswith("---"):
                if line.startswith("---```") and not is_fenced_code_block:
                    is_fenced_code_block = True
                elif line.startswith("---```") and is_fenced_code_block:
                    is_fenced_code_block = False

                if (
                    line == "---"
                    or line.startswith("---@")
                    or line.startswith("---|")
                    or line.startswith("---😱 [Types]")
                    # enumeration 1. 2. 3. ...
                    or re.match(r"^---\d+\. ", line)
                    or line.startswith("---* ")
                    # second line of a unordered list
                    or re.match(r"^---\s\s*\w", line) is not None
                    or is_fenced_code_block
                ):
                    lines_no_comment: list[str] = []
                    for to_rewrap_line in to_rewrap:
                        lines_no_comment.append(to_rewrap_line[3:])
                    for rewrapped_line in textwrap.wrap(
                        " ".join(lines_no_comment),
                        width=77,
                        break_long_words=False,
                        break_on_hyphens=False,
                    ):
                        lines.append(f"---{rewrapped_line}")
                    to_rewrap = []
                    lines.append(line)
                else:
                    to_rewrap.append(line)
            else:
                for left_over_line in to_rewrap:
                    lines.append(left_over_line)
                to_rewrap = []
                lines.append(line)

        self.content = "\n".join(lines)
        if self.content != "":
            _run_pygmentize(stdin=self.content)
        return self.finalize(save)

    def save(self) -> None:
        self.content = self.content.strip() + "\n"
        if logger.isEnabledFor(logging.DEBUG):
            _diff(self.orig_content, self.content)
        self.path.write_text(self.content)

    def finalize(self, save: bool = False) -> str:
        if save:
            self.save()
        return self.content


class Folder:
    path: Path

    def __init__(self, path: Union[str, Path]) -> None:
        self.path = Path(path)

    def list(
        self, relpath: Optional[Union[str, Path]] = None, extension: str = "lua"
    ) -> Generator["TextFile", Any, None]:
        """
        List files recursively as text files with a specified extension.

        Args:
            relpath: A relative path to search within.
            If None, the search will start from the base path (``self.path``).
            extension (str): The file extension to filter by. Defaults to ``lua``.

        Yields:
            TextFile: A generator yielding ``TextFile`` objects for each file
            matching the specified extension in the search path.
        """
        search_path: Path
        if relpath is None:
            search_path = self.path
        else:
            search_path = self.path / relpath
        for path in sorted(
            glob.glob(f"{search_path}/**/*.{extension}", recursive=True)
        ):
            yield TextFile(path)

    def list_path(
        self, relpath: Optional[Union[str, Path]] = None, extension: str = "lua"
    ) -> Generator[Path, Any, None]:
        search_path: Path
        if relpath is None:
            search_path = self.path
        else:
            search_path = self.path / relpath
        if search_path.is_file():
            yield Path(search_path)
            return

        with_extension = Path(f"{search_path}.{extension}")
        if with_extension.is_file():
            yield with_extension
            return
        for path in sorted(
            glob.glob(f"{search_path}/**/*.{extension}", recursive=True)
        ):
            yield Path(path)

    def __str__(self) -> str:
        return str(self.path)

    def get(self, relpath: Union[str, Path]) -> TextFile:
        """
        Retrieve a TextFile object for the given relative path.

        Args:
            relpath: The relative path to the file.

        Returns:
            TextFile: An instance of TextFile representing the file at the specified path.
        """
        return TextFile(self.path / relpath)

    def copy(self, dest: Union[str, Path], delete_dest: bool = True) -> None:
        _copy_directory(self.path, dest, delete_dest)

    @staticmethod
    def __get_pattern(subfolder: Optional[Union[str, Path]] = None) -> str:
        if subfolder:
            return f"{subfolder}/*"
        else:
            return "*"

    def clear(self, subfolder: Optional[Union[str, Path]] = None) -> None:
        """
        Deletes all files and subfolders in the folder or in the specified subfolder.

        Args:
            subfolder: Delete files in the subfolder if specified.
        """
        for file in self.path.glob(Folder.__get_pattern(subfolder)):
            if file.is_file():
                file.unlink()
            elif file.is_dir():
                shutil.rmtree(file)

    def count(self, subfolder: Optional[Union[str, Path]] = None) -> int:
        """
        Counts the number of files and subfolders in the folder recursively.

        Args:
            subfolder: Count files in the subfolder if specified.

        Returns:
            The total number of files and subfolders (including all subdirectories)
        """
        count = 0
        for _ in self.path.rglob(Folder.__get_pattern(subfolder)):
            count += 1
        return count


class Repository:
    path: Path

    def __init__(self, path: Union[Path, str]) -> None:
        self.path = Path(path)

    @staticmethod
    def clone(
        remote: str, dest: Union[str, Path], ignore_errors: bool = False
    ) -> "Repository":
        """
        Clone a remote Git repository to a specified destination.
        The repository will only be cloned if ``dest`` does not contain a ``.git`` folder.
        All submodules are cloned to.

        Args:
            remote: The URL of the remote Git repository to clone.
            dest: The destination path where the repository
                should be cloned. Can be a string or a Path object.

        Returns:
            Repository: An instance of the ``Repository`` class representing the
            cloned repository.

        Raises:
            subprocess.CalledProcessError: If the `git clone` command fails.
        """
        if isinstance(dest, str):
            dest = Path(dest)
        if not (dest / ".git").is_dir():
            args: list[Union[str, Path]] = [
                "git",
                "clone",
                "--recurse-submodules",
                "-j4",
                remote,
                dest,
            ]
            if ignore_errors:
                process = subprocess.Popen(args)
                process.communicate()
            else:
                subprocess.check_call(args)

        return Repository(dest)

    def check_call(self, *args: str) -> int:
        return subprocess.check_call(args, cwd=self.path)

    def check_output(self, *args: str) -> str:
        return subprocess.check_output(args, encoding="utf-8", cwd=self.path).strip()

    def checkout(self, branch: str = "main") -> None:
        if not self.exists_branch(branch):
            self.check_call("git", "branch", branch)
        self.check_call("git", "checkout", branch)

    def checkout_clean(self, branch: str = "main") -> None:
        self.__add()
        self.__reset()
        self.checkout(branch)
        self.__add()
        self.__reset()
        self.__pull(branch)

    def __add(self) -> None:
        self.check_call("git", "add", "-A")

    def __reset(self) -> None:
        self.check_call("git", "reset", "--hard", "HEAD")

    def __pull(self, branch: str = "main") -> None:
        self.check_call("git", "pull", "origin", branch)

    def __push(self, branch: str = "main") -> None:
        self.check_call("git", "push", "-u", "origin", branch)

    def __commit(self, message: str) -> bool:
        result = subprocess.run(["git", "commit", "-m", message], cwd=self.path)
        return result.returncode == 0

    __basepath: Optional[Path] = None

    @property
    def basepath(self) -> Path:
        if not self.__basepath:
            self.__basepath = Path(
                self.check_output("git", "rev-parse", "--show-toplevel")
            )
        return self.__basepath

    @property
    def folder(self) -> Folder:
        return Folder(self.path)

    def get_relpath(self, file: Path | str) -> str:
        relpath = str(file)
        relpath = relpath.replace(str(self.basepath), "")
        if relpath != str(file):
            return relpath[1:]  # remove leading /
        return relpath

    def get_github_blob_url(
        self,
        relpath: Optional[Union[Path, str]] = None,
        filename: Optional[Union[Path, str]] = None,
    ) -> str:
        # https://github.com/TeXLuaCATS/LuaTeX/blob/main/library/font.lua
        if (not relpath and not filename) or (relpath and filename):
            raise Exception("Specify relpath OR filename")
        if filename:
            relpath = f"library/{filename}"

        if relpath:
            relpath = self.get_relpath(relpath)

        return f"https://github.com/{self.github_owner_repo}/blob/main/{relpath}"

    def get_text_file(self, relpath: Union[Path, str]) -> TextFile:
        return TextFile(self.path / relpath)

    @property
    def github_owner_repo(self) -> str:
        # git@github.com:TeXLuaCATS/LuaMetaTeX.git
        # https://github.com/TeXLuaCATS/LuaMetaTeX.git
        remote = self.remote
        remote = remote.replace(".git", "")
        return re.sub("^.*github.com.", "", remote)

    @property
    def github_pull_request_url(self) -> str:
        return f"https://github.com/{self.github_owner_repo}/pulls"

    @property
    def is_commited(self) -> bool:
        """
        Checks if there are no uncommitted changes in the current Git repository.

        Returns:
            bool: True if the working directory is clean (no changes since last commit), False otherwise.
        """
        return self.check_output("git", "diff", "HEAD") == ""

    __latest_commitid: Optional[str] = None

    @property
    def latest_commitid(self) -> str:
        if not self.__latest_commitid:
            self.__latest_commitid = self.check_output("git", "rev-parse", "HEAD")
        return self.__latest_commitid

    @property
    def latest_commit_url(self) -> str:
        owner_repo = self.github_owner_repo
        latest = self.latest_commitid
        # https://github.com/TeXLuaCATS/LuaMetaTeX/commit/7ec2a8ef132ce450e62c29ce4dfea0c7ac67fb42
        return f"https://github.com/{owner_repo}/commit/{latest}"

    __remote: Optional[str] = None

    @property
    def remote(self) -> str:
        if not self.__remote:
            self.__remote = self.check_output("git", "remote", "get-url", "origin")
        return self.__remote

    def clean(self) -> None:
        self.check_call("git", "clean", "-dfx")

    def copy_subdir(
        self, subdir: str | Path, dest: str | Path, delete_dest: bool = True
    ) -> None:
        if isinstance(dest, str):
            dest = Path(dest)
        if dest.exists() and delete_dest:
            shutil.rmtree(dest)
        shutil.copytree(self.path / subdir, dest, dirs_exist_ok=True)

    def exists_branch(self, branch: str) -> bool:
        return branch in self.check_output("git", "branch")

    def exists_remote(self, remote: str) -> bool:
        return remote in self.check_output("git", "remote")

    def fetch_upstream(self, upstream: str) -> None:
        # https://stackoverflow.com/a/7244456
        if not self.exists_remote("upstream"):
            self.check_call("git", "remote", "add", "upstream", upstream)
        self.check_call("git", "fetch", "upstream")
        self.check_call("git", "checkout", "main")
        self.check_call("git", "rebase", "upstream/main")
        self.check_call("git", "push", "-u", "origin", "main")

    def sync_submodules(self) -> None:
        def submodule(*args: str) -> None:
            self.check_call("git", "submodule", *args)

        def foreach(*args: str) -> None:
            submodule("foreach", "--recursive", "git", *args)

        # submodule("update", "--init", "--recursive", "--remote")
        # deletes .venv folder
        # foreach("clean", "-xfd")
        foreach("reset", "--hard")
        foreach("checkout", "main")
        foreach("pull", "origin", "main")

    def sync_from_remote(self, branch: str = "main") -> None:
        """
        Synchronizes the local repository with the remote repository by
        resetting the local repository and pulling down from the remote.

        Args:
            branch: The name of the branch to synchronize from. Defaults to "main".

        Returns:
            None
        """
        logger.debug(
            "Syncronize Git repository %s from remote %s",
            Color.green(self.path),
            Color.green(self.remote),
        )
        self.checkout(branch)
        self.__add()
        self.__reset()
        self.__pull(branch)

    def sync_to_remote(
        self,
        message: str,
        branch: str = "main",
    ) -> None:
        self.__pull(branch)
        self.__add()
        if self.__commit(message):
            self.__push(branch=branch)


commit_ids = {"f52b099": "f52b099f3e01d53dc03b315e1909245c3d5418d3"}


ManualsSpec = Union[list[str], dict[str, Optional[str]]]


@dataclass
class Subproject:
    name: str
    """The name of the subproject must match the name of its parent subfolder exactly.
    For example: LuaTeX"""

    manuals: Optional[ManualsSpec] = None

    manuals_base_url: Optional[str] = None

    external_definitions: Optional[dict[str, str]] = None

    @property
    def lowercase_name(self) -> str:
        """For example: ``luatex``"""
        return self.name.lower()

    @property
    def base(self) -> Path:
        """For example: ``LuaCATS/upstream/luasocket``"""
        return basepath / "LuaCATS" / "upstream" / self.name

    @property
    def library(self) -> Folder:
        """The library folder in the main repo where type definitions are
        located, for example: ``TeXLuaCATS/LuaTeX/library``"""
        return Folder(self.base / "library")

    @property
    def examples(self) -> Optional[Folder]:
        path = self.base / "examples"
        if path.is_dir():
            return Folder(self.base / "examples")

    @property
    def dist(self) -> Path:
        """The directory where the compiled Lua sources are temporarily stored
        for distribution, for example: ``dist/LuaTeX``.

        The directory will be created if the folder does not exist.
        """
        path = basepath / "dist" / self.name
        if not path.exists():
            path.mkdir(parents=True)
        return path

    _dist_library: Optional[Folder] = None

    @property
    def dist_library(self) -> Folder:
        """The ``library`` folder in the ``dist`` directory, for example: ``dist/LuaTeX/library``."""
        if self._dist_library is None:
            self._dist_library = Folder(self.dist / "library")
        return self._dist_library

    @property
    def merged_defintions(self) -> TextFile:
        """The text file where the merged definitions are stored."""
        return TextFile(self.dist / "merged_defintions.lua")

    _repo: Optional[Repository] = None

    @property
    def repo(self) -> Repository:
        """The main Git repository, where the definitions are developed and
        written, for example: ``LuaCATS/upstream/luasocket``"""
        if not self._repo:
            self._repo = Repository(self.base)
        return self._repo

    _downstream_repo: Optional[Repository] = None

    @property
    def downstream_repo(self) -> Optional[Repository]:
        """For example: ``LuaCATS/downstream/tex-luatex``"""
        return None

    @property
    def downstream_library(self) -> Optional[Folder]:
        """For example: ``LuaCATS/downstream/tex-luatex/library``"""
        if self._downstream_repo:
            return Folder(self._downstream_repo.path / "library")

    @property
    def manuals_folder(self) -> Folder:
        """For example: ``TeXLuaCATS/LuaTeX/resources/manual``"""
        path = self.repo.path / "resources" / "manual"
        if not path.exists():
            path.mkdir(parents=True)
        return Folder(path)

    def check_call(self, *args: str) -> int:
        return self.repo.check_call(*args)

    def check_output(self, *args: str) -> str:
        return self.repo.check_output(*args)

    def get(self, relpath: Union[str, Path]) -> TextFile:
        """
        Retrieve a TextFile object for the given relative path in the main repository.

        Args:
            relpath: The relative path to the file within the main repository.

        Returns:
            TextFile: An instance of TextFile representing the file at the specified path.
        """
        return TextFile(self.repo.path / relpath)

    def download_manuals(self) -> None:
        def _download(src_filename: str, dest_filename: Optional[str] = None) -> None:
            if dest_filename is None:
                dest_filename = src_filename
            dest = self.manuals_folder.path / dest_filename
            _download_url(f"{self.manuals_base_url}/{src_filename}", str(dest))
            dest_file = TextFile(dest)
            lua_file = TextFile(f"{dest}.lua")
            if dest.suffix == ".tex":
                lua_file.write(dest_file.convert_tex_to_lua())
            if dest.suffix == ".html":
                lua_file.write(dest_file.convert_html_to_lua())

        if self.manuals is not None and self.manuals_base_url is not None:
            if isinstance(self.manuals, list):
                for src_filename in self.manuals:
                    _download(src_filename)
            else:
                for src_filename, dest_filename in self.manuals.items():
                    if dest_filename:
                        _download(src_filename, dest_filename)

    def sync_external_defintions(self) -> None:
        if self.external_definitions is None:
            return
        for src, dest in self.external_definitions.items():
            dest_path = self.library.path / dest
            if re.match(r"^https?://", src, re.IGNORECASE):
                _download_url(src, str(dest_path))
            else:
                shutil.copyfile(basepath / src, dest_path)

            dest_file = TextFile(dest_path)
            dest_file.remove_return_statement()
            dest_file.convert_local_to_global_table()
            dest_file.save()

    def sync_from_remote(self) -> None:
        """
        Synchronizes the main and the downstream repository with the remote
        repositories by resetting the local repositories and pulling down from
        the remote.

        Args:
            branch: The name of the branch to synchronize from. Defaults to "main".

        Returns:
            None
        """
        self.repo.sync_from_remote()
        downstream = self.downstream_repo
        if downstream is not None:
            downstream.sync_from_remote()

    def run_examples(self, relpath: Optional[Union[str, Path]]) -> None:
        examples = self.examples
        if examples is None:
            raise Exception(f"The subproject {self.name} has no examples folder")
        for path in examples.list_path(relpath=relpath):
            example = ExampleFile(path)
            example.run()

    def format(self, rewrap: bool) -> None:
        def __format(folder: Folder, rewrap: bool):
            for file in folder.list():
                file.clean_docstrings(save=True)
                if rewrap:
                    file.rewrap(save=True)
            _run_stylua(folder.path)

        __format(self.library, rewrap)
        if self.downstream_library:
            __format(self.downstream_library, rewrap)

    def merge(
        self,
    ) -> None:
        """Merge all lua files into one big file for the CTAN upload."""
        # self.distribute()
        contents: list[str] = []
        for text_file in self.dist_library.list():
            content = text_file.remove_double_dash_comments()
            # Remove the return statements
            content = re.sub(r"^return .+\n", "", content, flags=re.MULTILINE)
            # Remove all ---@meta definitions. We add one ---@meta later
            content = content.replace("---@meta\n", "")
            contents.append(content)
        # Add copyright notice and meta definition at the beginning
        contents.insert(0, text_blocks["copyright_notice"])
        contents.insert(1, "---@meta\n")
        content = "\n".join(contents)
        # Artefact of the copyright removal
        content = content.replace("\n\n---\n\n", "")
        self.merged_defintions.write(content)
        self.merged_defintions.clean_docstrings(save=True)

    def distribute(self, sync_to_remote: bool = True) -> None:
        dist = Folder(self.dist / "library")
        self.library.copy(dist.path)
        for file in dist.list():
            file.remove_navigation_table(save=True)
            file.clean_docstrings(save=True)
            file.render_templates(self.repo, save=True)
        if self.downstream_repo:
            dist.copy(self.downstream_repo.path / "library")
            if sync_to_remote:
                if not self.repo.is_commited:
                    raise Exception(
                        "Uncommited changes found! Commit first, then retry!"
                    )
                self.downstream_repo.sync_to_remote(
                    "Sync with " + self.repo.latest_commit_url
                )
        self.merge()

    def generate_markdown_docs(self, commit_id: str) -> None:
        self.distribute()

        resources = basepath / "resources" / "html-docs"

        src = self.dist / "library"
        dest = basepath / "dist" / self.dist / "docs"

        subprocess.check_call(
            [
                "emmylua_doc",
                src,
                "--override-template",
                resources / "emmylua-templates",
                "--site-name",
                self.name,
                "--output",
                self.repo.path,
            ]
        )

        # css
        shutil.copyfile(
            resources / "extra.css", dest / "docs" / "stylesheets" / "extra.css"
        )

        # logo
        # https://squidfunk.github.io/mkdocs-material/setup/changing-the-logo-and-icons/#logo
        logo_src = resources / "images" / "logos" / (self.lowercase_name + ".svg")
        if logo_src.exists():
            logo_dest = dest / "docs" / "assets" / "logo.svg"
            logo_dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(logo_src, logo_dest)

        _copy_directory(
            resources / "webfonts" / "DejaVu",
            dest / "docs" / "assets" / "fonts",
            delete_dest=False,
        )

        subprocess.check_call(["mkdocs", "build"], cwd=dest)
        self.repo.checkout_clean("gh-pages")
        _copy_directory(dest, self.repo.path)
        self.repo.sync_to_remote("Generate docs", "gh-pages")

    def compile_tex_doc(self) -> None:
        pass

    def make_ctan_bundle(self) -> None:
        pass


@dataclass
class TeXSubproject(Subproject):
    @property
    def base(self) -> Path:
        return basepath / "TeXLuaCATS" / self.name

    @property
    def downstream_repo(self) -> Optional[Repository]:
        if not self._downstream_repo:
            self._downstream_repo = Repository(
                basepath / "LuaCATS" / "downstream" / f"tex-{self.lowercase_name}"
            )
        if self._downstream_repo.path.exists():
            return self._downstream_repo

    @property
    def readme_tex(self) -> Optional[Path]:
        path = self.base / "README.tex"
        if path.exists():
            return path

    @property
    def readme_pdf(self) -> Optional[Path]:
        path = self.base / "README.pdf"
        if path.exists():
            return path

    def compile_tex_doc(self) -> None:
        if not self.readme_tex:
            return
        self.check_call("lualatex", "--shell-escape", "README.tex")
        self.check_call("makeindex", "-s", "gglo.ist", "-o", "README.gls", "README.glo")
        self.check_call("makeindex", "-s", "gind.ist", "-o", "README.ind", "README.idx")
        self.check_call("lualatex", "--shell-escape", "README.tex")

    def make_ctan_bundle(self) -> None:
        self.distribute(False)
        self.compile_tex_doc()
        jobname = f"{self.lowercase_name}-type-definitions"
        folder = self.dist / jobname
        shutil.rmtree(folder, ignore_errors=True)
        folder.mkdir(exist_ok=True, parents=True)
        assert self.readme_tex
        shutil.copyfile(self.readme_tex, folder / f"{jobname}-doc.tex")
        assert self.readme_pdf
        shutil.copyfile(self.readme_pdf, folder / f"{jobname}-doc.pdf")
        shutil.copyfile(self.merged_defintions.path, folder / f"{jobname}.lua")
        subprocess.check_call(
            ["tar", "cvfz", f"{jobname}.tar.gz", jobname], cwd=self.dist
        )


current_subproject: Optional[str] = None


def set_subproject(subproject: Optional[str]) -> None:
    global current_subproject
    current_subproject = subproject


class SubprojectContainer:
    __projects: dict[str, Subproject] = {}

    def __init__(self, *subprojects: Subproject) -> None:
        for subproject in subprojects:
            self.add(subproject)

    def __iter__(self) -> Iterator[Subproject]:
        if current_subproject is not None:
            return iter((self.__projects[current_subproject],))
        return iter(self.__projects.values())

    def __getitem__(self, key: str) -> Subproject:
        if current_subproject is not None:
            return self.__projects[current_subproject]
        return self.__projects[key]

    def __len__(self) -> int:
        if current_subproject is not None:
            return 1
        return self.__projects.__sizeof__()

    def add(self, subprojects: Subproject | dict[str, Subproject]) -> None:
        if isinstance(subprojects, dict):
            for name, subproject in subprojects.items():
                self.__projects[name] = subproject
        else:
            self.__projects[subprojects.lowercase_name] = subprojects

    def get(self, name: str) -> Subproject:
        return self.__projects[name.lower()]

    @property
    def current(self) -> Optional[Subproject]:
        if current_subproject is not None:
            return self.__projects[current_subproject]

    @property
    def current_default(self) -> Subproject:
        if current_subproject is not None:
            return self.__projects[current_subproject]
        return self.__projects["luatex"]

    @property
    def names(self) -> list[str]:
        return list(self.__projects.keys())

    @property
    def tex_projects(self) -> Generator[TeXSubproject, Any, None]:
        for subproject in self:
            if isinstance(subproject, TeXSubproject):
                yield subproject


subprojects = SubprojectContainer(
    Subproject("lmathx"),
    Subproject("lpeg"),
    Subproject("luaharfbuzz"),
    Subproject("luasocket"),
    Subproject("luazip"),
    Subproject("lzlib"),
    Subproject("md5"),
    Subproject("slnunicode"),
    # TeX
    TeXSubproject("LuaLaTeX"),
    TeXSubproject(
        "Lualibs",
        manuals={
            "cld-abitoflua.tex": "01_abitoflua.tex",
            "cld-afewdetails.tex": "04_afewdetails.tex",
            "cld-backendcode.tex": "15_backendcode.tex",
            "cld-callbacks.tex": "14_callbacks.tex",
            "cld-contents.tex": None,
            "cld-ctxfunctions.tex": "11_ctxfunctions.tex",
            "cld-environment.tex": None,
            "cld-files.tex": "20_files.tex",
            "cld-gettingstarted.tex": "02_gettingstarted.tex",
            "cld-goodies.tex": "16_goodies.tex",
            "cld-graphics.tex": "06_graphics.tex",
            "cld-introduction.tex": None,
            "cld-logging.tex": "09_logging.tex",
            "cld-luafunctions.tex": "10_luafunctions.tex",
            "cld-macros.tex": "07_macros.tex",
            "cld-mkiv.tex": None,
            "cld-moreonfunctions.tex": "03_moreonfunctions.tex",
            "cld-nicetoknow.tex": "17_nicetoknow.tex",
            "cld-scanners.tex": "12_scanners.tex",
            "cld-somemoreexamples.tex": "05_somemoreexamples.tex",
            "cld-specialcommands.tex": "19_specialcommands.tex",
            "cld-summary.tex": "18_summary.tex",
            "cld-titlepage.tex": None,
            "cld-variables.tex": "13_variables.tex",
            "cld-verbatim.tex": "08_verbatim.tex",
        },
        manuals_base_url="https://raw.githubusercontent.com/contextgarden/context/refs/heads/main/doc/context/sources/general/manuals/cld",
    ),
    TeXSubproject(
        "LuaMetaTeX",
        manuals={
            "luametatex-assumptions.tex": "04_assumptions.tex",
            "luametatex-callbacks.tex": "07_callbacks.tex",
            "luametatex-constructions.tex": "03_constructions.tex",
            "luametatex-contents.tex": None,
            "luametatex-engines.tex": "01_engines.tex",
            "luametatex-fonts.tex": "08_fonts.tex",
            "luametatex-internals.tex": "05_internals.tex",
            "luametatex-introduction.tex": None,
            "luametatex-languages.tex": "09_languages.tex",
            "luametatex-libraries.tex": "17_libraries.tex",
            "luametatex-lua.tex": "10_lua.tex",
            "luametatex-math.tex": "13_math.tex",
            "luametatex-metapost.tex": "11_metapost.tex",
            "luametatex-nodes.tex": "15_nodes.tex",
            "luametatex-pdf.tex": "14_pdf.tex",
            "luametatex-primitives.tex": "06_primitives.tex",
            "luametatex-principles.tex": "02_principles.tex",
            "luametatex-style.tex": None,
            "luametatex-tex.tex": "12_tex.tex",
            "luametatex-tokens.tex": "16_tokens.tex",
            "luametatex-security.tex": "18_security.tex",
            "luametatex.tex": None,
        },
        manuals_base_url="https://raw.githubusercontent.com/contextgarden/context/refs/heads/main/doc/context/sources/general/manuals/luametatex",
        external_definitions={
            "LuaCATS/upstream/lmathx/library/mathx.lua": "xmath.lua",
        },
    ),
    TeXSubproject("LuaOTFload"),
    TeXSubproject(
        "LuaTeX",
        manuals={
            "luatex-backend.tex": "14_backend.tex",
            "luatex-callbacks.tex": "09_callbacks.tex",
            "luatex-contents.tex": None,
            "luatex-enhancements.tex": "02_enhancements.tex",
            "luatex-export-titlepage.tex": None,
            "luatex-firstpage.tex": None,
            "luatex-fontloader.tex": "12_fontloader.tex",
            "luatex-fonts.tex": "06_fonts.tex",
            "luatex-graphics.tex": "11_graphics.tex",
            "luatex-harfbuzz.tex": "13_harfbuzz.tex",
            "luatex-introduction.tex": None,
            "luatex-languages.tex": "05_languages.tex",
            "luatex-logos.tex": None,
            "luatex-lua.tex": "04_lua.tex",
            "luatex-math.tex": "07_math.tex",
            "luatex-modifications.tex": "03_modifications.tex",
            "luatex-nodes.tex": "08_nodes.tex",
            "luatex-preamble.tex": "01_preamble.tex",
            "luatex-registers.tex": None,
            "luatex-statistics.tex": None,
            "luatex-style.tex": None,
            "luatex-tex.tex": "10_tex.tex",
            "luatex-titlepage.tex": None,
        },
        manuals_base_url="https://gitlab.lisn.upsaclay.fr/texlive/luatex/-/raw/master/manual",
        external_definitions={
            "https://raw.githubusercontent.com/LuaCATS/luafilesystem/refs/heads/main/library/lfs.lua": "lfs.lua",
            "LuaCATS/upstream/lpeg/library/lpeg.lua": "lpeg.lua",
            "LuaCATS/upstream/luaharfbuzz/library/luaharfbuzz.lua": "luaharfbuzz.lua",
            "LuaCATS/upstream/luasocket/library/mbox.lua": "mbox.lua",
            "LuaCATS/upstream/luasocket/library/mime.lua": "mime.lua",
            "LuaCATS/upstream/luasocket/library/socket.lua": "socket.lua",
            "LuaCATS/upstream/md5/library/md5.lua": "md5.lua",
            "LuaCATS/upstream/slnunicode/library/unicode.lua": "unicode.lua",
            # "LuaCATS/upstream/lzlib/library/zlib.lua": "zlib.lua", to many differences
            "LuaCATS/upstream/luazip/library/zip.lua": "zip.lua",
        },
    ),
)

parent_repo = Repository(basepath)
vscode_extension_repo = Repository(basepath / "vscode_extension")


@click.group()
@click.option("-d", "--debug", is_flag=True)
@click.option("-b", "--base-path", metavar="PATH")
@click.option("--lualatex", is_flag=True, help="Select LuaLaTeX as current subproject.")
@click.option("--lualibs", is_flag=True, help="Select Lualibs as current subproject.")
@click.option(
    "--luametatex", is_flag=True, help="Select LuaMetaTeX as current subproject."
)
@click.option(
    "--luaotfload", is_flag=True, help="Select LuaOTFload as current subproject."
)
@click.option("--luatex", is_flag=True, help="Select LuaTeX as current subproject.")
def cli(
    debug: bool,
    base_path: Optional[str],
    lualatex: Optional[str],
    lualibs: Optional[str],
    luametatex: Optional[str],
    luaotfload: Optional[str],
    luatex: Optional[str],
) -> None:
    """Manager for the TeXLuaCATS project."""
    if debug:
        logger.setLevel(logging.DEBUG)
    if base_path is not None:
        set_basepath(base_path)

    if lualatex:
        set_subproject("lualatex")
    elif lualibs:
        set_subproject("lualibs")
    elif luametatex:
        set_subproject("luametatex")
    elif luaotfload:
        set_subproject("luaotfload")
    elif luatex:
        set_subproject("luatex")


@cli.command()
def ctan() -> None:
    """Generate a tar.gz file for the CTAN upload."""
    for subproject in subprojects:
        subproject.make_ctan_bundle()


class ExampleFile:
    path: Path

    orig_content: str

    run_luaonly: Optional[bool] = None

    print_docstrings: bool = False

    def __init__(self, path: Path) -> None:
        self.path = path
        self.orig_content = path.read_text()

    __orig_lines: Optional[list[str]] = None

    @property
    def orig_lines(self) -> list[str]:
        if self.__orig_lines is None:
            self.__orig_lines = self.orig_content.splitlines()
        return self.__orig_lines

    @property
    def first_line(self) -> Optional[str]:
        if len(self.orig_lines) > 0:
            return self.orig_lines[0]

    __cleaned_lua_code: Optional[str] = None

    @property
    def cleaned_lua_code(self) -> str:
        """Lua code without the shebang and the TeX markup."""
        if self.__cleaned_lua_code is None:
            cleaned: list[str] = []
            for line in self.orig_lines:
                if (
                    not line.startswith("--tex: ")
                    and not line.startswith("--tex-after: ")
                    and not line.startswith("--tex-before: ")
                    and not line.startswith("#!")
                ):
                    cleaned.append(line)
            self.__cleaned_lua_code = "\n".join(cleaned).strip()
        return self.__cleaned_lua_code

    __pure_lua_code: Optional[str] = None

    @property
    def pure_lua_code(self) -> str:
        """Lua code without the shebang, the TeX markup and the utils import
        (``require("utils")``)."""
        if self.__pure_lua_code is None:
            pure: list[str] = []
            for line in self.cleaned_lua_code.splitlines():
                if 'require("utils")' not in line:
                    pure.append(line)
            self.__pure_lua_code = "\n".join(pure).strip()
        return self.__pure_lua_code

    @property
    def docstring(self) -> str:
        """
        Generates a Lua-formatted docstring for the `pure_lua_code` attribute.

        Returns:
            str: A string containing the Lua-formatted docstring, including example code
            wrapped in Lua comment markers and a code block.
        """
        lines: list[str] = ["", "---__Example:__", "---", "---```lua"]
        for line in self.pure_lua_code.splitlines():
            lines.append("---" + line)
        lines.append("---```")
        lines.append("---")
        return "\n".join(lines)

    def copy_docstring_to_clipboard(self) -> None:
        read, write = os.pipe()
        os.write(write, self.docstring.encode(encoding="utf-8"))
        os.close(write)
        subprocess.check_call(["xclip", "-selection", "clipboard"], stdin=read)

    __tex_markup_before: Optional[str] = None

    @property
    def tex_markup_before(self) -> str:
        """Extracts lines marked with '--tex-before: ' from Lua code and separates them from the rest."""
        if self.__tex_markup_before is None:
            tex_markup: list[str] = []
            for line in self.orig_content.splitlines():
                if line.startswith("--tex: "):
                    tex_markup.append(line[7:])
                if line.startswith("--tex-before: "):
                    tex_markup.append(line[14:])
            if len(tex_markup) > 0:
                self.__tex_markup_before = "\n".join(tex_markup)
        if self.__tex_markup_before is None:
            return ""
        return self.__tex_markup_before

    __tex_markup_after: Optional[str] = None

    @property
    def tex_markup_after(self) -> str:
        """Extracts lines marked with '--tex-after: ' from Lua code and separates them from the rest."""
        if self.__tex_markup_after is None:
            tex_markup: list[str] = []
            for line in self.orig_content.splitlines():
                if line.startswith("--tex-after: "):
                    tex_markup.append(line[13:])
            if len(tex_markup) > 0:
                self.__tex_markup_after = "\n".join(tex_markup)
        if self.__tex_markup_after is None:
            return ""
        return self.__tex_markup_after

    __shebang: Optional[list[str]] = None

    @property
    def shebang(self) -> Optional[list[str]]:
        """
        Parse the first line to support a shebang syntax
        """
        if self.__shebang is None:
            # #! luatex --lua-only
            # #! /usr/local/texlive/bin/x86_64-linux/luatex
            if self.first_line and self.first_line.startswith("#!"):
                first_line = self.first_line.replace("#!", "")
                self.__shebang = shlex.split(first_line)
        return self.__shebang

    @shebang.setter
    def shebang(self, value: list[str]) -> None:
        self.__luaonly = None
        self.__shebang = value

    __luaonly: Optional[bool] = None

    @property
    def luaonly(self) -> bool:
        if ExampleFile.run_luaonly is True:
            return True
        if self.__luaonly is None:
            if self.shebang is not None and "--luaonly" in self.shebang:
                self.__luaonly = True
            else:
                self.__luaonly = False
        return self.__luaonly is True

    @luaonly.setter
    def luaonly(self, value: bool) -> None:
        self.__luaonly = value

    @staticmethod
    def tmp_lua() -> Path:
        return basepath / "tmp.lua"

    @staticmethod
    def tmp_tex() -> Path:
        return basepath / "tmp.tex"

    @property
    def file_to_run(self) -> Path:
        if self.luaonly:
            return ExampleFile.tmp_lua()
        return ExampleFile.tmp_tex()

    def write_tex_file(self) -> None:
        ExampleFile.tmp_tex().write_text(
            self.tex_markup_before
            + "\n"
            + "\\directlua{dofile('tmp.lua')}\n"
            + self.tex_markup_after
            + "\n"
            + "\\bye\n"
        )

    def write_lua_file(self) -> None:
        ExampleFile.tmp_lua().write_text(
            "print('---start---')\n" + self.cleaned_lua_code + "\nprint('---stop---')"
        )

    def run(self, luaonly: bool = False) -> None:
        print(f"Run example file {Color.green(self.path)}")
        args = self.shebang
        luaonly = self.luaonly or luaonly

        if not luaonly:
            self.write_tex_file()

        self.write_lua_file()

        if args is None or len(args) == 0:
            args = ["luatex"]
        if luaonly and "--luaonly" not in args:
            args.append("--luaonly")
        result = subprocess.run(
            [*args, "--halt-on-error", str(self.file_to_run)],
            capture_output=True,
            cwd=basepath,
            timeout=30,
        )
        output = result.stdout.decode("utf-8", errors="ignore")
        output = re.sub(r"^.*---start---", "", output, flags=re.DOTALL)
        output = re.sub(r"---stop---.*$", "", output, flags=re.DOTALL)
        print(output)

        if ExampleFile.print_docstrings:
            print(self.docstring)
            self.copy_docstring_to_clipboard()
        if result.returncode != 0:
            sys.exit(1)


@cli.command()
@click.argument("relpath", required=False)
@click.option(
    "-l",
    "--run-luaonly",
    "--luaonly",
    help="Exectute the example in an Lua only environement without the TeX related libraries",
    is_flag=True,
)
@click.option(
    "--print-docstring",
    help="Print the lua code into fenced markdown code plain as a Lua comment.",
    is_flag=True,
)
def example(
    relpath: Optional[str] = None,
    run_luaonly: bool = False,
    print_docstring: bool = False,
) -> None:
    """Execute a single example file or a folder containing examples files."""
    ExampleFile.run_luaonly = run_luaonly
    ExampleFile.print_docstrings = print_docstring
    subprojects.current_default.run_examples(relpath)


@cli.command()
def external_definitions() -> None:
    """Sync external definitions"""
    for subproject in subprojects:
        subproject.sync_external_defintions()

    luametatex = subprojects.get("luametatex")
    xmath = luametatex.get("library/xmath.lua")
    xmath.replace("mathx.", "xmath.")
    xmath.replace("mathx =", "xmath =")
    xmath.prepend(
        """---
---Corresponding directory in the LuaTeX repository: https://github.com/contextgarden/luametatex/blob/main/source/luarest
---Corresponding file in the LuaMetaTeX repository: https://github.com/contextgarden/luametatex/blob/main/source/luarest/lmtxmathlib.c
---
---Changes to the upstream project: renamed global mathx table (mathx -> xmath)
""",
    )
    xmath.save()

    luatex = subprojects.get("luatex")

    # lfs

    navigation_table = (
        text_blocks["navigation_table_help"]
        + "\n"
        + '_N._4_3_lua_modules = "page 70"\n\n'
    )

    lfs = luatex.get("library/lfs.lua")
    lfs.prepend(
        navigation_table
        + """---
---Corresponding directory in the LuaTeX repository: https://gitlab.lisn.upsaclay.fr/texlive/luatex/-/blob/master/source/texk/web2c/luatexdir/luafilesystem
---Corresponding file in the LuaTeX repository: https://gitlab.lisn.upsaclay.fr/texlive/luatex/-/blob/master/source/texk/web2c/luatexdir/luafilesystem/src/lfs.c
---
---Changes to the upstream project: global lfs table
""",
        True,
    )

    # lpeg

    lpeg = luatex.get("library/lpeg.lua")
    lpeg.replace(
        "function lpeg.utfR(cp1, cp2) end", "---function lpeg.utfR(cp1, cp2) end"
    )
    lpeg.prepend(
        navigation_table
        + """---
---Corresponding directory in the LuaTeX repository: https://gitlab.lisn.upsaclay.fr/texlive/luatex/-/blob/master/source/texk/web2c/luatexdir/luapeg
---Corresponding file in the LuaTeX repository: https://gitlab.lisn.upsaclay.fr/texlive/luatex/-/blob/master/source/texk/web2c/luatexdir/luapeg/lpeg.c
---
---Changes to the upstream project: global lpeg table"""
    )
    lpeg.save()

    # mbox

    mbox = luatex.get("library/mbox.lua")
    mbox.prepend(
        navigation_table
        + """---
---Corresponding directory in the LuaTeX repository: https://gitlab.lisn.upsaclay.fr/texlive/luatex/-/blob/master/source/texk/web2c/luatexdir/luasocket
---Corresponding file in the LuaTeX repository: https://gitlab.lisn.upsaclay.fr/texlive/luatex/-/blob/master/source/texk/web2c/luatexdir/luasocket/src/mbox.lua
---
---Changes to the upstream project: global mbox table
""",
        True,
    )

    # md5

    md5 = luatex.get("library/md5.lua")
    md5.prepend(
        navigation_table
        + """---
---Corresponding directory in the LuaTeX repository: https://gitlab.lisn.upsaclay.fr/texlive/luatex/-/blob/master/source/texk/web2c/luatexdir/luamd5
---Corresponding file in the LuaTeX repository: https://gitlab.lisn.upsaclay.fr/texlive/luatex/-/blob/master/source/texk/web2c/luatexdir/luamd5/md5lib.c
---
---Changes to the upstream project:
---* local md5 table
---* additional function md5.sumHEXA()

""",
    )
    md5.append(
        """
---
---Compute the MD5 upper case hexadecimal message-digest of the string `message`.
---
---Similar to `md5.sum()`
---but returns its value as a string of 32 hexadecimal digits (upper case letters).
---
---__Example:__
---
---```lua
---local hash = md5.sumHEXA('test')
---assert(hash == '098F6BCD4621D373CADE4E832627B4F6')
---```
---
---@param message string
---
---@return string # for example `098F6BCD4621D373CADE4E832627B4F6`
function md5.sumHEXA(message) end
""",
    )
    md5.save()

    # mime

    mime = luatex.get("library/mime.lua")
    mime.prepend(
        navigation_table
        + """---
---Corresponding directory in the LuaTeX repository: https://gitlab.lisn.upsaclay.fr/texlive/luatex/-/blob/master/source/texk/web2c/luatexdir/luasocket
---Corresponding file in the LuaTeX repository: https://gitlab.lisn.upsaclay.fr/texlive/luatex/-/blob/master/source/texk/web2c/luatexdir/luasocket/src/mime.lua
---
---Changes to the upstream project: global mime table
""",
        True,
    )

    # socket

    socket = luatex.get("library/socket.lua")
    socket.prepend(
        navigation_table
        + """---
---Corresponding directory in the LuaTeX repository: https://gitlab.lisn.upsaclay.fr/texlive/luatex/-/blob/master/source/texk/web2c/luatexdir/luasocket
---Corresponding file in the LuaTeX repository: https://gitlab.lisn.upsaclay.fr/texlive/luatex/-/blob/master/source/texk/web2c/luatexdir/luasocket/src/socket.lua
---
---Changes to the upstream project: global socket table
""",
        True,
    )

    # unicode

    unicode = luatex.get("library/unicode.lua")
    unicode.prepend(
        navigation_table
        + """---
---Corresponding directory in the LuaTeX repository: https://gitlab.lisn.upsaclay.fr/texlive/luatex/-/tree/master/source/texk/web2c/luatexdir/slnunicode
---Corresponding file in the LuaTeX repository: https://gitlab.lisn.upsaclay.fr/texlive/luatex/-/blob/master/source/texk/web2c/luatexdir/slnunicode/slnunico.c
---
---`slnunicode`, from the `selene` libraries, http://luaforge.net/projects/sln.
---This library has been slightly extended so that the `unicode.utf8.*`
---functions also accept the first 256 values of plane 18. This is the range
---*LuaTeX* uses for raw binary output, as explained above. We have no plans to
---provide more like this because you can basically do all that you want in
---*Lua*.
---
---Changes to the upstream project: global unicode table
""",
        True,
    )

    # zip

    zip = luatex.get("library/zip.lua")
    zip.prepend(
        navigation_table
        + """---
---Corresponding directory in the LuaTeX repository: https://gitlab.lisn.upsaclay.fr/texlive/luatex/-/tree/master/source/texk/web2c/luatexdir/luazip
---Corresponding file in the LuaTeX repository: https://gitlab.lisn.upsaclay.fr/texlive/luatex/-/blob/master/source/texk/web2c/luatexdir/luazip/src/luazip.c
---
---Changes to the upstream project: global zip table
""",
        True,
    )

    # (zlib) differs a lot from the upstream project


#     zlib = luatex.get("library/zlib.lua")
#     zlib.prepend(
#         """
# -- A helper table to better navigate through the documentation using the
# -- outline: https://github.com/TeXLuaCATS/meta?tab=readme-ov-file#navigation-table-_n
# _N = {}

# _N._4_3_lua_modules = "page 67"

# ---
# ---Changes to upstream: global zlib table
# """,
#         True,
#    )


@cli.command()
@click.option("--rewrap", is_flag=True, help="Rewrap docstrings.")
def format(rewrap: bool) -> None:
    """Format the lua docstrings (Remove duplicate empty comment lines, start docstring with an empty line)"""
    for subproject in subprojects:
        subproject.format(rewrap)


@cli.command()
def manuals() -> None:
    """Download the TeX or HTML sources of the manuals."""
    for subproject in subprojects:
        subproject.download_manuals()


@cli.command()
def merge() -> None:
    """Merge all lua files of a subproject into one big file for the CTAN upload."""
    for project in subprojects:
        project.merge()


@cli.command()
@click.option("--no-sync", is_flag=True, help="Do not commit and sync to the remote.")
def dist(no_sync: bool) -> None:
    """Copy the ``library`` to the ``dist`` folder, remove the navigation table, clean
    the docstrings and synchronize to the remote repository"""
    sync_to_remote = not no_sync
    for subproject in subprojects:
        subproject.distribute(sync_to_remote)
    # vscode extension
    vscode_extension_repo.checkout_clean("main")
    latest_commit_urls: list[str] = []
    for subproject in subprojects.tex_projects:
        _copy_directory(
            subproject.dist / "library",
            vscode_extension_repo.path / "library" / subproject.lowercase_name,
        )
        latest_commit_urls.append(subproject.repo.latest_commit_url)
    if sync_to_remote:
        vscode_extension_repo.sync_to_remote(
            "Sync with:\n\n" + "- " + "\n- ".join(latest_commit_urls)
        )
        parent_repo.sync_to_remote("Update submodules")


@cli.command()
@click.argument("path")
def rewrap(path: str) -> None:
    """The Rewrap extension (https://github.com/dnut/Rewrap) does not support rewraping of thee hyphens prefixed comment lines."""
    abspath = Path(path).resolve()
    file = TextFile(abspath)
    file.rewrap()


@cli.command()
def submodules() -> None:
    """Update all submodules. Synchronizes the main and the downstream
    repository with the remote repositories by resetting the local
    repositories and pulling down from the remote."""
    parent_repo.sync_submodules()
    # for subproject in subprojects:
    #     subproject.sync_from_remote()


@cli.command()
@click.option("--clean", is_flag=True, help="Remove a already cloned lls addon repo.")
def update_lls_addons(clean: bool) -> None:
    """
    Create a branch for a pull request in the repo git@github.com:Josef-Friedrich/LLS-Addons.git
    to update submodules in the repo
    git@github.com:LuaLS/LLS-Addons.git
    """

    base = Path("/tmp/lls_addons")

    if clean and base.exists():
        shutil.rmtree(base, ignore_errors=True)
    repo = Repository.clone(
        "git@github.com:Josef-Friedrich/LLS-Addons.git", base, ignore_errors=True
    )
    repo.fetch_upstream("git@github.com:LuaLS/LLS-Addons.git")
    today = datetime.now().strftime("%Y-%m-%d")
    update_branch = f"update_{today}"
    repo.checkout(update_branch)

    for addon in [
        "lmathx",
        "lpeg",
        "luasocket",
        "luazip",
        "lzlib",
        "md5",
        "slnunicode",
        "tex-lualatex",
        "tex-lualibs",
        "tex-luametatex",
        "tex-luatex",
    ]:
        pass

        addon_root = base / "addons" / addon / "module"

        addon_repo = Repository(addon_root)
        addon_repo.sync_from_remote()
        _run_stylua(addon_root)

    repo.sync_to_remote(
        message="Update TeX related submodules to the latest version",
        branch=update_branch,
    )


def main() -> None:
    cli()
