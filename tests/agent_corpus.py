"""Tiny German clause corpus + fakes shared by agent and API tests."""

from __future__ import annotations

from api.agent.schemas import RiskSignal
from rag.chunking import Chunk
from rag.embeddings import BagOfWordsEmbedder
from rag.ingest import ingest
from rag.retriever import Retriever
from rag.store import InMemoryStore

CORPUS = [
    Chunk(
        "A.2.2.2.2",
        "Unfall",
        "Versichert sind Schäden am Fahrzeug durch Unfall. Ein Unfall ist ein unmittelbar von außen plötzlich mit mechanischer Gewalt einwirkendes Ereignis.",
        "A.2.2.2",
        11,
    ),
    Chunk(
        "A.2.2.2.3",
        "Mut- oder böswillige Handlungen",
        "Versichert sind mut- oder böswillige Handlungen betriebsfremder Personen.",
        "A.2.2.2",
        11,
    ),
    Chunk(
        "A.2.5.8",
        "Selbstbeteiligung",
        "Ist eine Selbstbeteiligung vereinbart, wird diese bei jedem Schadenereignis von der Entschädigung abgezogen.",
        "A.2.5",
        14,
    ),
    Chunk(
        "E.1.1.1",
        "Anzeigepflicht",
        "Sie sind verpflichtet, uns jedes Schadenereignis innerhalb einer Woche anzuzeigen.",
        "E.1.1",
        31,
    ),
    Chunk(
        "E.1.1.3",
        "Aufklärungspflicht",
        "Sie müssen alles tun, was zur Aufklärung des Versicherungsfalls erforderlich ist. Unfallstelle nicht verlassen, Polizei.",
        "E.1.1",
        31,
    ),
    Chunk(
        "A.2.2.1.4",
        "Zusammenstoß mit Haarwild",
        "Versichert ist der Zusammenstoß des Fahrzeugs mit Haarwild.",
        "A.2.2.1",
        10,
    ),
]


class FakeScorer:
    model_version = "fake-0"

    def score(self, facts, policy):
        return RiskSignal(
            score=0.42, band="medium", reasons=["no police report", "no witnesses", "late evening"]
        )


def make_retriever() -> Retriever:
    store, emb = InMemoryStore(), BagOfWordsEmbedder()
    ingest(CORPUS, store, emb)
    return Retriever(store, emb)
