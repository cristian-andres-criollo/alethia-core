"""Memoria episódica (ChromaMemoryClient — fallback JSON)."""
import json

import pytest

from vector_db.chroma_client import ChromaMemoryClient


@pytest.fixture
def mem(tmp_path):
    return ChromaMemoryClient(persist_directory=str(tmp_path / "db"))


def test_creates_empty_json_file(mem, tmp_path):
    f = tmp_path / "db" / "memory.json"
    assert f.exists()
    assert json.loads(f.read_text(encoding="utf-8")) == []


def test_save_and_search(mem):
    assert mem.save_memory("1", "Q: capital de Colombia | A: Bogotá")
    assert mem.save_memory("2", "Q: color del cielo | A: azul")
    result = mem.search_memories("capital colombia")
    assert "Bogotá" in result
    assert "azul" not in result


def test_search_ranks_by_score_and_limits(mem):
    mem.save_memory("a", "python")
    mem.save_memory("b", "python fastapi")
    mem.save_memory("c", "python fastapi pytest")
    mem.save_memory("d", "python fastapi pytest docker")
    result = mem.search_memories("python fastapi pytest docker", n_results=2).split("\n---\n")
    assert result == ["python fastapi pytest docker", "python fastapi pytest"]


def test_search_empty(mem):
    assert "No se encontraron" in mem.search_memories("lo que sea")


def test_search_no_match(mem):
    mem.save_memory("1", "hola")
    assert "No se encontraron" in mem.search_memories("zzz")


def test_persists_between_instances(tmp_path):
    """CP-15: reinicio del Motor sin pérdida de memoria."""
    d = str(tmp_path / "db")
    ChromaMemoryClient(persist_directory=d).save_memory("1", "recuerdo persistente")
    assert "persistente" in ChromaMemoryClient(persist_directory=d).search_memories("persistente")


def test_metadata_is_stored(mem, tmp_path):
    mem.save_memory("1", "x", {"idioma": "es"})
    data = json.loads((tmp_path / "db" / "memory.json").read_text(encoding="utf-8"))
    assert data[0] == {"id": "1", "content": "x", "metadata": {"idioma": "es"}}


def test_corrupted_file_does_not_crash(mem, tmp_path):
    (tmp_path / "db" / "memory.json").write_text("{no es json", encoding="utf-8")
    assert mem.save_memory("1", "x") is False
    assert "Error" in mem.search_memories("x")


def test_unicode_is_preserved(mem, tmp_path):
    mem.save_memory("1", "¿Qué más, parce? ñ 🚀")
    assert "parce" in mem.search_memories("parce")


@pytest.mark.xfail(strict=True, reason="GAP: según Scripts de BD, search_memories() debe retornar list, hoy retorna str")
def test_search_returns_list_per_docs(mem):
    mem.save_memory("1", "hola")
    assert isinstance(mem.search_memories("hola"), list)
