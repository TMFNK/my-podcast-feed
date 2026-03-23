import os
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

sys.path.insert(
    0,
    str(
        Path(
            "/Users/edis-mac/Documents/03-Eddie-Python-Projects/python/my-podcast-feed-main/scripts"
        )
    ),
)

from utils import get_data_dir, load_config


class UtilsDataDirTests(unittest.TestCase):
    def test_get_data_dir_prefers_repo_root_when_project_has_repo_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            repo_root.mkdir()
            (repo_root / "state.json").write_text("{}", encoding="utf-8")

            data_dir = get_data_dir(repo_root=repo_root, home_dir=Path(tmp) / "home")

            self.assertEqual(data_dir, repo_root)
            self.assertTrue((repo_root / "logs").is_dir())
            self.assertTrue((repo_root / "scripts_output").is_dir())
            self.assertTrue((repo_root / "episodes").is_dir())

    def test_load_config_falls_back_to_legacy_home_when_repo_has_no_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo_root = root / "repo"
            repo_root.mkdir()
            (repo_root / "state.json").write_text("{}", encoding="utf-8")

            legacy_dir = root / "home" / ".claude" / "personalized-podcast"
            legacy_dir.mkdir(parents=True)
            config_path = legacy_dir / "config.yaml"
            config_path.write_text(
                yaml.safe_dump({"show_name": "Fallback Show", "sources": {"rss": []}}),
                encoding="utf-8",
            )

            config = load_config(repo_root=repo_root, home_dir=root / "home")

            self.assertEqual(config["show_name"], "Fallback Show")

    def test_get_data_dir_uses_explicit_environment_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            override_dir = Path(tmp) / "custom-data"
            old_value = os.environ.get("PODCAST_DATA_DIR")
            os.environ["PODCAST_DATA_DIR"] = str(override_dir)
            try:
                data_dir = get_data_dir(repo_root=Path(tmp) / "repo")
            finally:
                if old_value is None:
                    os.environ.pop("PODCAST_DATA_DIR", None)
                else:
                    os.environ["PODCAST_DATA_DIR"] = old_value

            self.assertEqual(data_dir, override_dir)
            self.assertTrue((override_dir / "logs").is_dir())


if __name__ == "__main__":
    unittest.main()
