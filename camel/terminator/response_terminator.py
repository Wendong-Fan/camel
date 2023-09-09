# =========== Copyright 2023 @ CAMEL-AI.org. All Rights Reserved. ===========
# Licensed under the Apache License, Version 2.0 (the “License”);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an “AS IS” BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =========== Copyright 2023 @ CAMEL-AI.org. All Rights Reserved. ===========
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from camel.messages import BaseMessage
from camel.typing import TerminationMode

from .base import ResponseTerminator


class ResponseWordsTerminator(ResponseTerminator):

    def __init__(self, words_dict: Dict[str,
                                        int], case_sensitive: bool = False,
                 mode: TerminationMode = TerminationMode.ANY):
        super().__init__()
        self.words_dict = words_dict
        self.case_sensitive = case_sensitive
        self.mode = mode
        self._word_count_dict: Dict[str, int] = defaultdict(int)
        self._validate()

    def _validate(self):
        if len(self.words_dict) == 0:
            raise ValueError("`words_dict` cannot be empty")
        for word in self.words_dict:
            threshold = self.words_dict[word]
            if threshold <= 0:
                raise ValueError(f"Threshold for word `{word}` should "
                                 f"be larger than 0, got `{threshold}`")

    def is_terminated(
            self, messages: List[BaseMessage]) -> Tuple[bool, Optional[str]]:
        r"""Whether terminate the response by checking the occurrence
        of specified words reached to preset thresholds.

        Args:
            messages (list): List of :obj:`BaseMessage` from a response.

        Returns:
            tuple: A tuple containing whether the response should be
                terminated and a string of termination reason.
        """
        if self._terminated:
            return True, self._termination_reason
        for word in self.words_dict:
            special_word = word if self.case_sensitive else word.lower()
            for message in messages:
                if self.case_sensitive:
                    content = message.content
                else:
                    content = message.content.lower()
                if special_word in content:
                    self._word_count_dict[word] += 1

        num_reached = 0
        reasons: List[str] = []
        for word, value in self._word_count_dict.items():
            if value >= self.words_dict[word]:
                num_reached += 1
                reason = (f"Word `{word}` appears {value} "
                          f"times in response which has reached termination "
                          f"threshold {self.words_dict[word]}.")
                reasons.append(reason)

        if self.mode == TerminationMode.ANY:
            if num_reached > 0:
                self._terminated = True
                self._termination_reason = "\n".join(reasons)
        elif self.mode == TerminationMode.ALL:
            if num_reached >= len(self.words_dict):
                self._terminated = True
                self._termination_reason = "\n".join(reasons)
        else:
            raise ValueError(f"Unsupported termination mode `{self.mode}`")
        return self._terminated, self._termination_reason

    def reset(self):
        self._terminated = False
        self._termination_reason = None
        self._word_count_dict = defaultdict(int)
