# coding=utf-8
# Copyright 2019 TF.Text Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Text shape ops.

A variety of useful regex helper functions using the RE2 library
(string_ops.regex_full_match) for matching various relevant patterns within
input text.

Naming convention:
  is_$PROPERTY: the entire string is composed of $PROPERTY
  has_$PROPERTY: the string contains at least one $PROPERTY.
  has_no_$PROPERTY: the string does not contain any $PROPERTY.
  begins_with_$PROPERTY: the string begins with $PROPERTY characters.
  ends_with_$PROPERTY: the string ends with $PROPERTY characters.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re
import enum

from tensorflow.python.framework import ops
from tensorflow.python.ops import array_ops
from tensorflow.python.ops import string_ops

#===============================================================================
# Implementation: Regular Expressions for WordShapes
#===============================================================================


def _emoticon_regex():
  """Regexp to detect emoticons."""
  emoticons = [
      ":-)", ":)", ":o)", ":]", ":3", ":>", "=]", "=)", ":}", ":^)", ":-D",
      ":-))", ":-)))", ":-))))", ":-)))))", ">:[", ":-(", ":(", ":-c", ":c",
      ":-<", ":<", ":-[", ":[", ":{", ";(", ":-||", ":@", ">:(", ":'-(", ":'(",
      ":'-)", ":')", "D:<", ">:O", ":-O", ":-o", ":*", ":-*", ":^*", ";-)",
      ";)", "*-)", "*)", ";-]", ";]", ";^)", ":-,", ">:P", ":-P", ":p", "=p",
      ":-p", "=p", ":P", "=P", ";p", ";-p", ";P", ";-P"
      ">:\\", ">:/", ":-/", ":-.", ":/", ":\\", "=/", "=\\", ":|", ":-|", ":$",
      ":-#", ":#", "O:-)", "0:-)", "0:)", "0;^)", ">:)", ">;)", ">:-)", "}:-)",
      "}:)", "3:-)", ">_>^", "^<_<", "|;-)", "|-O", ":-J", ":-&", ":&", "#-)",
      "%-)", "%)", "<:-|", "~:-\\", "*<|:-)", "=:o]", ",:-)", "7:^]", "</3",
      "<3", "8-)", "^_^", ":D", ":-D", "=D", "^_^;;", "O=)", "}=)", "B)", "B-)",
      "=|", "-_-", "o_o;", "u_u", ":-\\", ":s", ":S", ":-s", ":-S", ";*", ";-*"
      ":(", "=(", ">.<", ">:-(", ">:(", ">=(", ";_;", "T_T", "='(", ">_<", "D:",
      ":o", ":-o", "=o", "o.o", ":O", ":-O", "=O", "O.O", "x_x", "X-(", "X(",
      "X-o", "X-O", ":X)", "(=^.^=)", "(=^..^=)", "=^_^=", "-<@%", ":(|)",
      ":(:)", "(]:{", "<\\3", "~@~", "8'(", "XD", "DX"
  ]
  # Note: unicode-containing emojis are added manually-escaped here.
  return "|".join(map(re.escape, emoticons)) + "|".join(
      [u"\\:\u3063\\)", u"\\:\u3063C", u"\u0ca0\\_\u0ca0"])


def _emoji_regex():
  """Regexp to detect emoji characters."""
  char_class = "".join([
      "[", u"\u2600", "-", u"\u26ff",
      u"\U0001f300", "-", u"\U0001f6ff",
      u"\U0001f900", "-", u"\U0001f9ff", "]"
  ])  # pyformat:disable
  return ".*" + char_class + ".*"


def _begins_with_open_quote_regex():
  # Note: RE2 syntax doesn't support char class intersection.
  char_class = "".join([
      "\"", "'", "`", u"\uff07", u"\uff02", u"\u2018", u"\u201a", u"\u201b",
      u"\u201c", u"\u00ab", u"\u201e", u"\u201f" + u"\u2039", u"\u300c",
      u"\u300e", u"\u301d", u"\u2e42" + u"\uff62", u"\ufe41", u"\ufe43"
  ])
  return "``.*|[" + char_class + "][^" + char_class + "]*"


def _ends_with_close_quote_regex():
  char_class = "".join([
      "\"", "'", "`", u"\uff07", u"\uff02", u"\u00bb", u"\u2019", u"\u201d",
      u"\u203a", u"\u300d", u"\u300f", u"\u301e" + u"\u301f", u"\ufe42",
      u"\ufe44", u"\uff63"
  ])

  return ".*''|[^" + char_class + "]*[" + char_class + "]"


class WordShape(enum.Enum):
  """Values for the 'pattern' arg of the wordshape op.

     The supported wordshape identifiers are:
     %(identifier_list)s
  """
  HAS_PUNCTUATION_DASH = r".*\p{Pd}+.*"
  HAS_NO_DIGITS = r"\P{Nd}*"
  HAS_SOME_DIGITS = r".*\P{Nd}\p{Nd}.*|.*\p{Nd}\P{Nd}.*"
  HAS_ONLY_DIGITS = r"\p{Nd}+"
  IS_NUMERIC_VALUE = r"([+-]?((\p{Nd}+\.?\p{Nd}*)|(\.\p{Nd}+)))([eE]-?\p{Nd}+)?"
  IS_WHITESPACE = r"\p{Whitespace}+"
  HAS_NO_PUNCT_OR_SYMBOL = r"[^\p{P}\p{S}]*"
  HAS_SOME_PUNCT_OR_SYMBOL = r".*[^\p{P}\p{S}][\p{P}\p{S}].*|.*[\p{P}\p{S}][^\p{P}\p{S}].*"  # pylint: disable=line-too-long
  IS_PUNCT_OR_SYMBOL = r"[\p{P}|\p{S}]+"
  BEGINS_WITH_PUNCT_OR_SYMBOL = r"[\p{P}\p{S}].*"
  ENDS_WITH_PUNCT_OR_SYMBOL = r".*[\p{P}\p{S}]"
  ENDS_WITH_SENTENCE_TERMINAL = r".*[\p{Sentence_Terminal}]"
  ENDS_WITH_MULTIPLE_SENTENCE_TERMINAL = r".*[\p{Sentence_Terminal}]{2}"
  ENDS_WITH_TERMINAL_PUNCT = r".*[\p{Terminal_Punctuation}]"
  ENDS_WITH_MULTIPLE_TERMINAL_PUNCT = r".*[\p{Terminal_Punctuation}]{2}"
  ENDS_WITH_ELLIPSIS = r".*(\.{3}|[" + u"\u2026" + u"\u22ef" + "])"
  IS_EMOTICON = _emoticon_regex()
  ENDS_WITH_EMOTICON = r".*(" + _emoticon_regex() + r")$"
  HAS_EMOJI = r".*(" + _emoji_regex() + r")$"
  IS_ACRONYM_WITH_PERIODS = r"(\p{Lu}\.)+"
  IS_UPPERCASE = r"\p{Lu}+"
  IS_LOWERCASE = r"\p{Ll}+"
  HAS_MIXED_CASE = r".*\p{Lu}.*\p{Ll}.*|.*\p{Ll}.*\p{Lu}.*"
  IS_MIXED_CASE_LETTERS = r"\p{L}*\p{Lu}\p{L}*\p{Ll}\p{L}*|\p{L}*\p{Ll}\p{L}*\p{Lu}\p{L}*"  # pylint: disable=line-too-long
  # Is a single capital letter alone a title case?
  HAS_TITLE_CASE = r"\P{L}*[\p{Lu}\p{Lt}]\p{Ll}+.*"
  HAS_NO_QUOTES = "[^\"'`\\p{Quotation_Mark}]*"
  BEGINS_WITH_OPEN_QUOTE = _begins_with_open_quote_regex()
  ENDS_WITH_CLOSE_QUOTE = _ends_with_close_quote_regex()
  HAS_QUOTE = r"^[`\p{Quotation_Mark}].*|.*[`\p{Quotation_Mark}]$"
  HAS_MATH_SYMBOL = r".*\p{Sm}.*"
  HAS_CURRENCY_SYMBOL = r".*\p{Sc}$"
  HAS_NON_LETTER = r".*\P{L}.*"


# Note that the entries in _wordshape_doc must be indented 10 spaces to display
# correctly in the docstring.
_wordshape_doc = {
    WordShape.HAS_PUNCTUATION_DASH:
        """
          The input contains at least one unicode dash character.

          Note that this is similar to HAS_ANY_HYPHEN, but uses the Pd (Dash)
          unicode property. This property will not match to soft-hyphens and
          katakana middle dot characters.
          """,
    WordShape.HAS_NO_DIGITS:
        """
          The input contains no digit characters.
          """,
    WordShape.HAS_SOME_DIGITS:
        """
          The input contains a mix of digit characters and non-digit
          characters.
          """,
    WordShape.HAS_ONLY_DIGITS:
        """
          The input consists entirely of unicode digit characters.
          """,
    WordShape.IS_NUMERIC_VALUE:
        """
          The input is parseable as a numeric value.  This will match a
          fairly broad set of floating point and integer representations (but
          not Nan or Inf).
          """,
    WordShape.IS_WHITESPACE:
        """
          The input consists entirely of whitespace.
          """,
    WordShape.HAS_NO_PUNCT_OR_SYMBOL:
        """
          The input contains no unicode punctuation or symbol characters.
          """,
    WordShape.HAS_SOME_PUNCT_OR_SYMBOL:
        """
          The input contains a mix of punctuation or symbol characters,
          and non-punctuation non-symbol characters.
          """,
    WordShape.IS_PUNCT_OR_SYMBOL:
        """
          The input contains only punctuation and symbol characters.
          """,
    WordShape.BEGINS_WITH_PUNCT_OR_SYMBOL:
        """
          The input starts with a punctuation or symbol character.
          """,
    WordShape.ENDS_WITH_PUNCT_OR_SYMBOL:
        """
          The input ends with a punctuation or symbol character.
          """,
    WordShape.ENDS_WITH_SENTENCE_TERMINAL:
        """
          The input ends with a sentence-terminal character.
          """,
    WordShape.ENDS_WITH_MULTIPLE_SENTENCE_TERMINAL:
        """
          The input ends with multiple sentence-terminal characters.
          """,
    WordShape.ENDS_WITH_TERMINAL_PUNCT:
        """
          The input ends with a terminal-punctuation character.
          """,
    WordShape.ENDS_WITH_MULTIPLE_TERMINAL_PUNCT:
        """
          The input ends with multiple terminal-punctuation characters.
          """,
    WordShape.ENDS_WITH_ELLIPSIS:
        """
          The input ends with an ellipsis (i.e. with three or more
          periods or a unicode ellipsis character).""",
    WordShape.IS_EMOTICON:
        """
          The input is a single emoticon.
          """,
    WordShape.ENDS_WITH_EMOTICON:
        """
          The input ends with an emoticon.
          """,
    WordShape.HAS_EMOJI:
        """
          The input contains an emoji character.

          See http://www.unicode.org/Public/emoji/1.0//emoji-data.txt.
          Emojis are in unicode ranges `2600-26FF`, `1F300-1F6FF`, and
          `1F900-1F9FF`.
          """,
    WordShape.IS_ACRONYM_WITH_PERIODS:
        """
          The input is a period-separated acronym.
          This matches for strings of the form "I.B.M." but not "IBM".
          """,
    WordShape.IS_UPPERCASE:
        """
          The input contains only uppercase letterforms.
          """,
    WordShape.IS_LOWERCASE:
        """
          The input contains only lowercase letterforms.
          """,
    WordShape.HAS_MIXED_CASE:
        """
          The input contains both uppercase and lowercase letterforms.
          """,
    WordShape.IS_MIXED_CASE_LETTERS:
        """
          The input contains only uppercase and lowercase letterforms.
          """,
    WordShape.HAS_TITLE_CASE:
        """
          The input has title case (i.e. the first character is upper or title
          case, and the remaining characters are lowercase).
          """,
    WordShape.HAS_NO_QUOTES:
        """
          The input string contains no quote characters.
          """,
    WordShape.BEGINS_WITH_OPEN_QUOTE:
        r"""
          The input begins with an open quote.

          The following strings are considered open quotes:

          ```
               "  QUOTATION MARK
               '  APOSTROPHE
               `  GRAVE ACCENT
              ``  Pair of GRAVE ACCENTs
          \uFF02  FULLWIDTH QUOTATION MARK
          \uFF07  FULLWIDTH APOSTROPHE
          \u00AB  LEFT-POINTING DOUBLE ANGLE QUOTATION MARK
          \u2018  LEFT SINGLE QUOTATION MARK
          \u201A  SINGLE LOW-9 QUOTATION MARK
          \u201B  SINGLE HIGH-REVERSED-9 QUOTATION MARK
          \u201C  LEFT DOUBLE QUOTATION MARK
          \u201E  DOUBLE LOW-9 QUOTATION MARK
          \u201F  DOUBLE HIGH-REVERSED-9 QUOTATION MARK
          \u2039  SINGLE LEFT-POINTING ANGLE QUOTATION MARK
          \u300C  LEFT CORNER BRACKET
          \u300E  LEFT WHITE CORNER BRACKET
          \u301D  REVERSED DOUBLE PRIME QUOTATION MARK
          \u2E42  DOUBLE LOW-REVERSED-9 QUOTATION MARK
          \uFF62  HALFWIDTH LEFT CORNER BRACKET
          \uFE41  PRESENTATION FORM FOR VERTICAL LEFT CORNER BRACKET
          \uFE43  PRESENTATION FORM FOR VERTICAL LEFT WHITE CORNER BRACKET
          ```

          Note: U+B4 (acute accent) not included.
          """,
    WordShape.ENDS_WITH_CLOSE_QUOTE:
        r"""
          The input ends witha closing quote character.

          The following strings are considered close quotes:

          ```
               "  QUOTATION MARK
               '  APOSTROPHE
               `  GRAVE ACCENT
              ''  Pair of APOSTROPHEs
          \uFF02  FULLWIDTH QUOTATION MARK
          \uFF07  FULLWIDTH APOSTROPHE
          \u00BB  RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK
          \u2019  RIGHT SINGLE QUOTATION MARK
          \u201D  RIGHT DOUBLE QUOTATION MARK
          \u203A  SINGLE RIGHT-POINTING ANGLE QUOTATION MARK
          \u300D  RIGHT CORNER BRACKET
          \u300F  RIGHT WHITE CORNER BRACKET
          \u301E  DOUBLE PRIME QUOTATION MARK
          \u301F  LOW DOUBLE PRIME QUOTATION MARK
          \uFE42  PRESENTATION FORM FOR VERTICAL RIGHT CORNER BRACKET
          \uFE44  PRESENTATION FORM FOR VERTICAL RIGHT WHITE CORNER BRACKET
          \uFF63  HALFWIDTH RIGHT CORNER BRACKET
          ```

          Note: U+B4 (ACUTE ACCENT) is not included.
          """,
    WordShape.HAS_QUOTE:
        """
          The input starts or ends with a unicode quotation mark.
          """,
    WordShape.HAS_MATH_SYMBOL:
        """
          The input contains a mathematical symbol.
          """,
    WordShape.HAS_CURRENCY_SYMBOL:
        """
          The input contains a currency symbol.
          """,
    WordShape.HAS_NON_LETTER:
        """
          The input contains a non-letter character.
          """,
}


def _add_identifier_list_to_docstring(func):
  items = [("WordShape." + ws.name, doc) for ws, doc in _wordshape_doc.items()]
  identifier_list = "".join(
      "\n        * `%s`:%s\n" % (name, doc) for (name, doc) in sorted(items))
  func.__doc__ = func.__doc__ % dict(identifier_list=identifier_list)

# Use the wordshape docstring we created above.
_add_identifier_list_to_docstring(WordShape)


def wordshape(input_tensor, pattern, name=None):
  """Determine wordshape features for each input string.

  Args:
    input_tensor: string `Tensor` with any shape.
    pattern: A `tftext.WordShape` or a list of WordShapes.
    name: A name for the operation (optional).

  Returns:
    `<bool>[input_tensor.shape + pattern.shape]`: A tensor where
      `result[i1...iN, j]` is true if `input_tensor[i1...iN]` has the wordshape
      specified by `pattern[j]`.

  Raises:
    ValueError: If `pattern` contains an unknown identifier.
  """
  if isinstance(pattern, WordShape):
    return string_ops.regex_full_match(input_tensor, pattern.value, name)
  elif (isinstance(pattern, (list, tuple)) and
        all(isinstance(s, WordShape) for s in pattern)):
    with ops.name_scope(name, "Wordshape", input_tensor):
      return array_ops.stack([wordshape(input_tensor, s) for s in pattern],
                             axis=-1)
  else:
    raise TypeError(
        "Expected 'pattern' to be a single WordShape or a list of WordShapes.")
