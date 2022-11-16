from typing import List

from jina import Executor, requests, Document, DocumentArray


class SecretSanta(Executor):
    """
    This Executor arranges matches between participants and a random Secret Santee.
    """
    def __init__(self, participants: List[str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.participants = DocumentArray([Document(text=p) for p in participants])
        self.secret_map = self._match_santas_to_santees()

    @requests(on='/match_me')
    def get_santee(self, parameters: dict, **kwargs):
        """
        Get a random santee for a santa from the list of santa's.
        A santee can only be assigned once, and a santa cannot be their own santee.
        """
        santa = parameters.get('santa', None)
        if santa and santa in self.secret_map:
            print(f'Santa {santa} --> {self.secret_map[santa]}')
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
                santee = random_santas[i+1]
            secret_map[santa.text] = santee.text
        return secret_map


if __name__ == "__main__":
    from jina import Flow

    f = Flow().add(uses=SecretSanta, uses_with={"participants": ["Isabelle", "Leon", "Max", "Florian"]})

    with f:
        f.post(on='/match_me', parameters={"santa":'Isabelle'})
        f.post(on='/match_me', parameters={"santa": 'Max'})
        f.post(on='/match_me', parameters={"santa": 'Leon'})
        f.post(on='/match_me', parameters={"santa": 'Florian'})
        f.post(on='/match_me', parameters={"santa": 'Matty'})