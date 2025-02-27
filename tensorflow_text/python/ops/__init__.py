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

"""Various TensorFlow ops related to text-processing."""

from tensorflow_text.python.ops.create_feature_bitmask_op import create_feature_bitmask
from tensorflow_text.python.ops.greedy_constrained_sequence_op import greedy_constrained_sequence
from tensorflow_text.python.ops.ngrams_op import ngrams
from tensorflow_text.python.ops.ngrams_op import Reduction
from tensorflow_text.python.ops.normalize_ops import case_fold_utf8
from tensorflow_text.python.ops.normalize_ops import normalize_utf8
from tensorflow_text.python.ops.pad_along_dimension_op import pad_along_dimension
from tensorflow_text.python.ops.pointer_ops import gather_with_default
from tensorflow_text.python.ops.pointer_ops import span_alignment
from tensorflow_text.python.ops.pointer_ops import span_overlaps
from tensorflow_text.python.ops.sentence_breaking_ops import sentence_fragments
from tensorflow_text.python.ops.sliding_window_op import sliding_window
from tensorflow_text.python.ops.string_ops import coerce_to_structurally_valid_utf8
from tensorflow_text.python.ops.tokenization import Tokenizer
from tensorflow_text.python.ops.tokenization import TokenizerWithOffsets
from tensorflow_text.python.ops.unicode_script_tokenizer import UnicodeScriptTokenizer
from tensorflow_text.python.ops.viterbi_constrained_sequence_op import viterbi_constrained_sequence
from tensorflow_text.python.ops.whitespace_tokenizer import WhitespaceTokenizer
from tensorflow_text.python.ops.wordpiece_tokenizer import WordpieceTokenizer
from tensorflow_text.python.ops.wordshape_ops import WordShape
from tensorflow_text.python.ops.wordshape_ops import wordshape
