"""Ley 1 — No Daño Activo (filtro de salida y de herramientas)."""
import pytest

from inference_engine.rules.law_1_no_harm import Law1NoHarm


@pytest.fixture
def law():
    return Law1NoHarm()


@pytest.mark.parametrize("text", [
    "Voy a ejecutar rm -rf / ahora",
    "del /s /q c:\\",
    "FORMAT C: /q",
    "DROP DATABASE produccion;",
])
def test_blocks_known_destructive_commands(law, text):
    r = law.validate_action(text)
    assert r["is_valid"] is False
    assert "Ley 1" in r["reason"]


@pytest.mark.parametrize("text", [
    "La capital de Colombia es Bogotá.",
    "Para listar archivos usa ls -la",
    "rm archivo.txt borra un solo archivo",
])
def test_allows_safe_text(law, text):
    assert law.validate_action(text)["is_valid"] is True


def test_information_about_command_is_also_blocked(law):
    """Documenta el comportamiento actual: la Ley 1 dice censurar la ACCIÓN y no la
    información, pero hoy bloquea cualquier texto que contenga el comando."""
    r = law.validate_action("Nunca ejecutes 'rm -rf /' porque borra todo el sistema.")
    assert r["is_valid"] is False


@pytest.mark.parametrize("text", [
    "rm  -rf /",            # doble espacio
    "rm -fr /",             # flags invertidos
    "sudo rm -r -f /",      # flags separados
    "rm -rf --no-preserve-root /",
    "rm -rf ~",
    "mkfs.ext4 /dev/sda",
    "dd if=/dev/zero of=/dev/sda",
    "Remove-Item -Recurse -Force C:\\",
    "rd /s /q C:\\",
])
def test_destructive_variants_are_blocked(law, text):
    assert law.validate_action(text)["is_valid"] is False


@pytest.mark.parametrize("text", [
    "rm -rf ./build",
    "rm -r carpeta_temporal",
    "Clona la ISO con: dd if=a.iso of=b.img",
    "El formato de fecha es dd/mm/aaaa",
])
def test_non_root_operations_allowed(law, text):
    assert law.validate_action(text)["is_valid"] is True
