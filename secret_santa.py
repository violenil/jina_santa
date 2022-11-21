import random
from typing import List

import hubble
from hubble import AuthenticationRequiredError
from jina import Executor, requests, Document, DocumentArray
from jina.logging.logger import JinaLogger


class SecretSanta(Executor):
    """
    This Executor arranges matches between participants and a random Secret Santee.
    """

    def __init__(self, participants: List[str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        random.seed(4)
        random.shuffle(participants)
        self.nicknames = [p.split("@")[0] for p in participants]
        self.allowed_emails = participants
        self.secret_map = self._match_santas_to_santees()
        self.logger = JinaLogger(self.__class__.__name__)

    def _get_user_info(self, token) -> dict:
        try:
            client = hubble.Client(token=token, max_retries=None, jsonify=True)
            user_info = client.get_user_info()
            if user_info["code"] != 200:
                self.logger.info("Could not retrieve user info.")
            return user_info["data"]
        except AuthenticationRequiredError as e:
            self.logger.info("Authentication failed. Check token.")
            return {}

    def _verify_user_email(self, user_email) -> bool:
        if user_email in self.allowed_emails:
            return True
        self.logger.info("User email not allowed.")
        return False

    def _check_santa(self, santa: str) -> bool:
        if santa in self.secret_map:
            return True
        self.logger.info("User is not a santa.")
        return False

    @requests(on="/match_me")
    def get_santee(self, parameters: dict, **kwargs):
        """
        Get a random santee for a santa from the list of santa's.
        A santee can only be assigned once, and a santa cannot be their own santee.
        """
        token = parameters.get("token")
        if not token:
            return DocumentArray()
        user_info = self._get_user_info(token)
        if not user_info:
            return DocumentArray()
        nickname = user_info.get("nickname")
        if not self._check_santa(nickname):
            return DocumentArray()
        elif self._verify_user_email(user_info.get("email")):
            return DocumentArray([Document(text=self.secret_map[nickname])])
        else:
            return DocumentArray()

    def _match_santas_to_santees(self):
        """
        This matching function randomly assigns one participant to each santa.
        """
        secret_map = {}
        for i, santa in enumerate(self.nicknames):
            if i == len(self.nicknames) - 1:
                santee = self.nicknames[0]
            else:
                santee = self.nicknames[i + 1]
            secret_map[santa] = santee
        return secret_map
