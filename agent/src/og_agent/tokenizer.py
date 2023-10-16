# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

"""
Taken from the NAYA project

https://github.com/danielyule/naya

Copyright (c) 2019 Daniel Yule
"""
import io
import unicodedata

SURROGATE = "Cs"


class TokenType:
    OPERATOR = 0
    STRING = 1
    NUMBER = 2
    BOOLEAN = 3
    NULL = 4


class State:
    WHITESPACE = 0
    INTEGER_0 = 1
    INTEGER_SIGN = 2
    INTEGER = 3
    INTEGER_EXP = 4
    INTEGER_EXP_0 = 5
    FLOATING_POINT_0 = 6
    FLOATING_POINT = 8
    STRING = 9
    STRING_ESCAPE = 10
    STRING_END = 11
    TRUE_1 = 12
    TRUE_2 = 13
    TRUE_3 = 14
    FALSE_1 = 15
    FALSE_2 = 16
    FALSE_3 = 17
    FALSE_4 = 18
    NULL_1 = 19
    NULL_2 = 20
    NULL_3 = 21
    UNICODE = 22
    UNICODE_SURROGATE_START = 23
    UNICODE_SURROGATE_STRING_ESCAPE = 24
    UNICODE_SURROGATE = 25


class SpecialChar:
    # Kind of a hack but simple: if we used the empty string "" to represent
    # EOF, expressions like `char in "0123456789"` would be true for EOF, which
    # is confusing. If we used a non-string, they would result in TypeErrors.
    # By using the string "EOF", they work as expected. The only thing we have
    # to be careful about is to not ever use "EOF" in any such strings used for
    # char membership checking, which we have no reason to do anyway.
    EOF = "EOF"


class UnCompletedException(Exception):

    def __init_(self, token):
        super().__init__("")
        self.token = token


def _guess_encoding(stream):
    # if it looks like a urllib response, get the charset from the headers (if any)
    try:
        encoding = stream.headers.get_content_charset()
    except:  # noqa
        encoding = None
    if encoding is None:
        # JSON is supposed to be UTF-8
        # https://tools.ietf.org/id/draft-ietf-json-rfc4627bis-09.html#:~:text=The%20default%20encoding%20is%20UTF,16%20and%20UTF%2D32).
        encoding = "utf-8"
    return encoding


def _ensure_text(stream):
    data = stream.read(0)
    if isinstance(data, bytes):
        encoding = _guess_encoding(stream)
        return io.TextIOWrapper(stream, encoding=encoding)
    return stream


def tokenize(stream):
    stream = _ensure_text(stream)

    def is_delimiter(char):
        return char.isspace() or char in "{}[]:," or char == SpecialChar.EOF

    token = []
    unicode_buffer = ""
    completed = False
    now_token = ""

    def process_char(char):
        nonlocal token, completed, now_token, unicode_buffer
        advance = True
        add_char = False
        next_state = state
        if state == State.WHITESPACE:
            if char == "{":
                completed = True
                now_token = (TokenType.OPERATOR, "{")
            elif char == "}":
                completed = True
                now_token = (TokenType.OPERATOR, "}")
            elif char == "[":
                completed = True
                now_token = (TokenType.OPERATOR, "[")
            elif char == "]":
                completed = True
                now_token = (TokenType.OPERATOR, "]")
            elif char == ",":
                completed = True
                now_token = (TokenType.OPERATOR, ",")
            elif char == ":":
                completed = True
                now_token = (TokenType.OPERATOR, ":")
            elif char == '"':
                next_state = State.STRING
            elif char in "123456789":
                next_state = State.INTEGER
                add_char = True
            elif char == "0":
                next_state = State.INTEGER_0
                add_char = True
            elif char == "-":
                next_state = State.INTEGER_SIGN
                add_char = True
            elif char == "f":
                next_state = State.FALSE_1
            elif char == "t":
                next_state = State.TRUE_1
            elif char == "n":
                next_state = State.NULL_1
            elif not char.isspace() and not char == SpecialChar.EOF:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == State.INTEGER:
            if char in "0123456789":
                add_char = True
            elif char == ".":
                next_state = State.FLOATING_POINT_0
                add_char = True
            elif char == "e" or char == "E":
                next_state = State.INTEGER_EXP_0
                add_char = True
            elif is_delimiter(char):
                next_state = State.WHITESPACE
                completed = True
                now_token = (TokenType.NUMBER, int("".join(token)))
                advance = False
            else:
                raise ValueError(
                    "A number must contain only digits.  Got '{}'".format(char)
                )
        elif state == State.INTEGER_0:
            if char == ".":
                next_state = State.FLOATING_POINT_0
                add_char = True
            elif char == "e" or char == "E":
                next_state = State.INTEGER_EXP_0
                add_char = True
            elif is_delimiter(char):
                next_state = State.WHITESPACE
                completed = True
                now_token = (TokenType.NUMBER, 0)
                advance = False
            else:
                raise ValueError(
                    "A 0 must be followed by a '.' or a 'e'.  Got '{0}'".format(char)
                )
        elif state == State.INTEGER_SIGN:
            if char == "0":
                next_state = State.INTEGER_0
                add_char = True
            elif char in "123456789":
                next_state = State.INTEGER
                add_char = True
            else:
                raise ValueError(
                    "A - must be followed by a digit.  Got '{0}'".format(char)
                )
        elif state == State.INTEGER_EXP_0:
            if char == "+" or char == "-" or char in "0123456789":
                next_state = State.INTEGER_EXP
                add_char = True
            else:
                raise ValueError(
                    "An e in a number must be followed by a '+', '-' or digit.  Got '{0}'".format(
                        char
                    )
                )
        elif state == State.INTEGER_EXP:
            if char in "0123456789":
                add_char = True
            elif is_delimiter(char):
                completed = True
                now_token = (TokenType.NUMBER, float("".join(token)))
                next_state = State.WHITESPACE
                advance = False
            else:
                raise ValueError(
                    "A number exponent must consist only of digits.  Got '{}'".format(
                        char
                    )
                )
        elif state == State.FLOATING_POINT:
            if char in "0123456789":
                add_char = True
            elif char == "e" or char == "E":
                next_state = State.INTEGER_EXP_0
                add_char = True
            elif is_delimiter(char):
                completed = True
                now_token = (TokenType.NUMBER, float("".join(token)))
                next_state = State.WHITESPACE
                advance = False
            else:
                raise ValueError("A number must include only digits")
        elif state == State.FLOATING_POINT_0:
            if char in "0123456789":
                next_state = State.FLOATING_POINT
                add_char = True
            else:
                raise ValueError(
                    "A number with a decimal point must be followed by a fractional part"
                )
        elif state == State.FALSE_1:
            if char == "a":
                next_state = State.FALSE_2
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == State.FALSE_2:
            if char == "l":
                next_state = State.FALSE_3
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == State.FALSE_3:
            if char == "s":
                next_state = State.FALSE_4
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == State.FALSE_4:
            if char == "e":
                next_state = State.WHITESPACE
                completed = True
                now_token = (TokenType.BOOLEAN, False)
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == State.TRUE_1:
            if char == "r":
                next_state = State.TRUE_2
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == State.TRUE_2:
            if char == "u":
                next_state = State.TRUE_3
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == State.TRUE_3:
            if char == "e":
                next_state = State.WHITESPACE
                completed = True
                now_token = (TokenType.BOOLEAN, True)
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == State.NULL_1:
            if char == "u":
                next_state = State.NULL_2
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == State.NULL_2:
            if char == "l":
                next_state = State.NULL_3
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == State.NULL_3:
            if char == "l":
                next_state = State.WHITESPACE
                completed = True
                now_token = (TokenType.NULL, None)
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == State.STRING:
            if char == '"':
                completed = True
                now_token = (TokenType.STRING, "".join(token))
                next_state = State.STRING_END
            elif char == "\\":
                next_state = State.STRING_ESCAPE
            elif char == SpecialChar.EOF:
                raise ValueError("Unterminated string at end of file")
            else:
                add_char = True
        elif state == State.STRING_END:
            if is_delimiter(char):
                advance = False
                next_state = State.WHITESPACE
            else:
                raise ValueError(
                    "Expected whitespace or an operator after string.  Got '{}'".format(
                        char
                    )
                )
        elif state == State.STRING_ESCAPE:
            next_state = State.STRING
            if char == "\\" or char == '"':
                add_char = True
            elif char == "b":
                char = "\b"
                add_char = True
            elif char == "f":
                char = "\f"
                add_char = True
            elif char == "n":
                char = "\n"
                add_char = True
            elif char == "t":
                char = "\t"
                add_char = True
            elif char == "r":
                char = "\r"
                add_char = True
            elif char == "/":
                char = "/"
                add_char = True
            elif char == "u":
                next_state = State.UNICODE
                unicode_buffer = ""
            else:
                raise ValueError("Invalid string escape: {}".format(char))
        elif state == State.UNICODE:
            if char == SpecialChar.EOF:
                raise ValueError("Unterminated unicode literal at end of file")
            unicode_buffer += char
            if len(unicode_buffer) == 4:
                try:
                    code_point = int(unicode_buffer, 16)
                except ValueError:
                    raise ValueError(f"Invalid unicode literal: \\u{unicode_buffer}")
                char = chr(code_point)
                if unicodedata.category(char) == SURROGATE:
                    next_state = State.UNICODE_SURROGATE_START
                else:
                    next_state = State.STRING
                    add_char = True
        elif state == State.UNICODE_SURROGATE_START:
            if char == "\\":
                next_state = State.UNICODE_SURROGATE_STRING_ESCAPE
            elif char == SpecialChar.EOF:
                raise ValueError("Unpaired UTF-16 surrogate at end of file")
            else:
                raise ValueError(f"Unpaired UTF-16 surrogate")

        elif state == State.UNICODE_SURROGATE_STRING_ESCAPE:
            if char == "u":
                next_state = State.UNICODE_SURROGATE
            elif char == SpecialChar.EOF:
                raise ValueError("Unpaired UTF-16 surrogate at end of file")
            else:
                raise ValueError(f"Unpaired UTF-16 surrogate")

        elif state == State.UNICODE_SURROGATE:
            if char == SpecialChar.EOF:
                raise ValueError("Unterminated unicode literal at end of file")
            unicode_buffer += char
            if len(unicode_buffer) == 8:
                code_point_1 = int(unicode_buffer[:4], 16)
                try:
                    code_point_2 = int(unicode_buffer[4:], 16)
                except ValueError:
                    raise ValueError(
                        f"Invalid unicode literal: \\u{unicode_buffer[4:]}"
                    )
                char = chr(code_point_2)
                if unicodedata.category(char) != SURROGATE:
                    raise ValueError(
                        f"Second half of UTF-16 surrogate pair is not a surrogate!"
                    )
                try:
                    pair = int.to_bytes(code_point_1, 2, "little") + int.to_bytes(
                        code_point_2, 2, "little"
                    )
                    char = pair.decode("utf-16-le")
                except ValueError:
                    raise ValueError(
                        f"Error decoding UTF-16 surrogate pair \\u{unicode_buffer[:4]}\\u{unicode_buffer[4:]}"
                    )
                next_state = State.STRING
                add_char = True

        if add_char:
            token.append(char)

        return advance, next_state

    state = State.WHITESPACE
    c = stream.read(1)
    index = 0
    while c:
        try:
            advance, state = process_char(c)
        except Exception as e:
            yield (state, token)
            break
        if completed:
            completed = False
            token = []
            yield (None, now_token)
        if advance:
            c = stream.read(1)
            index += 1
    try:
        process_char(SpecialChar.EOF)
        if completed:
            yield (None, now_token)
    except Exception as e:
        yield (state, token)
