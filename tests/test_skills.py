# tests/test_skills.py
import pytest
from bot.skills import load_skill


class TestLoadSkill:
    def test_loads_and_interpolates_template(self, tmp_path):
        skill_file = tmp_path / "test_skill.md"
        skill_file.write_text("Analyze: {heroes}\nFormat as HTML.")

        result = load_skill(str(skill_file), heroes="Lancelot, Pharsa")
        assert result == "Analyze: Lancelot, Pharsa\nFormat as HTML."

    def test_no_placeholders(self, tmp_path):
        skill_file = tmp_path / "plain.md"
        skill_file.write_text("Just a plain prompt.")

        result = load_skill(str(skill_file))
        assert result == "Just a plain prompt."

    def test_multiple_placeholders(self, tmp_path):
        skill_file = tmp_path / "multi.md"
        skill_file.write_text("Heroes: {heroes}, Mode: {mode}")

        result = load_skill(str(skill_file), heroes="Tigreal", mode="ranked")
        assert result == "Heroes: Tigreal, Mode: ranked"

    def test_file_not_found_raises(self):
        with pytest.raises(FileNotFoundError):
            load_skill("/nonexistent/skill.md")
