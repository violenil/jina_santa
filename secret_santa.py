from typing import List

import hubble
from hubble import AuthenticationRequiredError
from hubble import login_required
from jina import Executor, requests, Document, DocumentArray


class SecretSanta(Executor):
    """
    This Executor arranges matches between participants and a random Secret Santee.
    """

    def __init__(self, participants: List[str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.participants = DocumentArray(
            [Document(text=p) for p in participants.keys()]
        )
        self.allowed_emails = [email for email in participants.values()]
        self.secret_map = self._match_santas_to_santees()

    def _get_user_info(self, token):
        try:
            client = hubble.Client(token=token, max_retries=None, jsonify=True)
            user_info = client.get_user_info()
            if user_info["code"] != 200:
                raise PermissionError(
                    "Wrong token passed or the token is expired! Please re-login."
                )
            return user_info["data"]
        except AuthenticationRequiredError as e:
            raise PermissionError(
                "Token expired or invalid. Please use an updated token.", e
            )

    def _verify_user(self, santa):
        token = str(hubble.Auth.get_auth_token())
        user_info = self._get_user_info(token)
        user_email = user_info.get("email")
        nickname = user_info.get("nickname")
        if user_email in self.allowed_emails and santa.lower() in nickname:
            return True
        raise PermissionError(
            f'User {user_info.get("email") or user_info["_id"]} has no permission to access this Secret Santa app.'
        )

    @requests(on="/match_me")
    @login_required
    def get_santee(self, parameters: dict, **kwargs):
        """
        Get a random santee for a santa from the list of santa's.
        A santee can only be assigned once, and a santa cannot be their own santee.
        """
        santa = parameters.get("santa")
        if santa in self.secret_map and self._verify_user(santa):
            print(f"Santa {santa} --> {self.secret_map[santa]}")
        else:
            print(f"{santa} is not a santa!")

    def _match_santas_to_santees(self):
        """
        This matching function randomly assigns one participant to each santa.
        """
        random_santas = self.participants.shuffle()
        secret_map = {}
        for i, santa in enumerate(random_santas):
            if i == len(random_santas) - 1:
                santee = random_santas[0]
            else:
                santee = random_santas[i + 1]
            secret_map[santa.text] = santee.text
        return secret_map
