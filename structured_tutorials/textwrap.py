# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Module for wrapping text width."""

import re
import textwrap
from collections.abc import Iterator
from typing import Any


class CommandLineTextWrapper(textwrap.TextWrapper):
    """Subclass of TextWrapper that "unsplits" a short option and its (supposed) value.

    This makes sure that a command with many options will not break between short options and their value,
    e.g. for ``docker run -e FOO=foo -e BAR=bar ...``, the text wrapper will never insert a line split between
    ``-e`` and its respective option value.

    Note that the class of course does not know the semantics of the command it renders. A short option
    followed by a value is always considered a reason not to break. For example, for ``docker run ... -d
    image``, the wrapper will never split between ``-d`` and ``image``, despite the latter being unrelated to
    the former.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.subsequent_indent = ">    "
        self.break_on_hyphens = False
        self.break_long_words = False
        self.replace_whitespace = False

    def _unsplit_optargs(self, chunks: list[str]) -> Iterator[str]:
        unsplit: list[str] = []
        for chunk in chunks:
            if re.match("-[a-z]$", chunk):  # chunk appears to be an option
                if unsplit:  # previous option was also an optarg, so yield what was there
                    yield from unsplit
                unsplit = [chunk]
            elif chunk == " ":
                if unsplit:  # this is the whitespace after an option
                    unsplit.append(chunk)
                else:  # a whitespace not preceded by an option
                    yield chunk

            # The unsplit buffer has two values (short option and space) and this chunk looks like its
            # value, so yield the buffer and this value as split
            elif len(unsplit) == 2 and re.match("[a-zA-Z0-9`]", chunk):
                # unsplit option, whitespace and option value
                unsplit.append(chunk)
                yield "".join(unsplit)
                unsplit = []

            # There is something in the unsplit buffer, but this chunk does not look like a value (maybe
            # it's a long option?), so we yield tokens from the buffer and then this chunk.
            elif unsplit:
                yield from unsplit
                unsplit = []
                yield chunk
            else:
                yield chunk

        # yield any remaining chunks
        yield from unsplit

    def _split(self, text: str) -> list[str]:
        chunks = super()._split(text)
        chunks = list(self._unsplit_optargs(chunks))
        return chunks


def wrap_command_filter(command: str, prompt: str, text_width: int) -> str:
    """Filter to wrap a command based on the given text width."""
    lines = []
    split_command_lines = tuple(enumerate(command.split("\\\n"), start=1))

    # Split paragraphs based on backslash-newline and wrap them separately
    for line_no, command_line in split_command_lines:
        final_line = line_no == len(split_command_lines)

        # Strip any remaining newline, they are treated as a single space
        command_line = re.sub(r"\s*\n\s*", " ", command_line).strip()
        if not command_line:
            continue

        wrapper = CommandLineTextWrapper(width=text_width)
        if line_no == 1:
            wrapper.initial_indent = prompt
        else:
            wrapper.initial_indent = wrapper.subsequent_indent

        wrapped_command_lines = wrapper.wrap(command_line)
        lines += [
            f"{line} \\" if (i != len(wrapped_command_lines) or not final_line) else line
            for i, line in enumerate(wrapped_command_lines, 1)
        ]
    return "\n".join(lines)
