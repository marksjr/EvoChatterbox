import importlib
import io
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


class FakeTensor:
    def __init__(self, label: str = "tensor") -> None:
        self.label = label

    def dim(self) -> int:
        return 2

    def unsqueeze(self, dim: int):
        return self

    def cpu(self):
        return self


class FakeModel:
    def __init__(self, sr: int = 24000) -> None:
        self.sr = sr
        self.generate_calls = []

    def generate(self, *args, **kwargs):
        self.generate_calls.append({"args": args, "kwargs": kwargs})
        return FakeTensor("generated")


class FakeStandardTTS(FakeModel):
    @classmethod
    def from_pretrained(cls, device: str):
        return cls()


class FakeMultilingualTTS(FakeModel):
    @classmethod
    def from_local(cls, ckpt_dir, device: str):
        return cls()


def install_dependency_stubs() -> None:
    fake_torch = types.ModuleType("torch")
    fake_torch.Tensor = FakeTensor
    fake_torch.float32 = "float32"
    fake_torch.zeros = lambda shape, dtype=None: FakeTensor("silence")
    fake_torch.cat = lambda tensors, dim=1: FakeTensor("cat")
    fake_torch.cuda = types.SimpleNamespace(
        is_available=lambda: False,
        get_device_name=lambda index: "Fake GPU",
    )

    fake_torchaudio = types.ModuleType("torchaudio")
    fake_torchaudio.save = lambda path, wav, sr: Path(path).write_bytes(b"RIFF")

    fake_hf = types.ModuleType("huggingface_hub")
    fake_hf.snapshot_download = lambda **kwargs: str(Path.cwd())

    fake_chatterbox = types.ModuleType("chatterbox")
    fake_chatterbox_models = types.ModuleType("chatterbox.models")
    fake_s3gen = types.ModuleType("chatterbox.models.s3gen")
    fake_s3gen.S3GEN_SR = 24000

    fake_mtl = types.ModuleType("chatterbox.mtl_tts")
    fake_mtl.ChatterboxMultilingualTTS = FakeMultilingualTTS
    fake_mtl.SUPPORTED_LANGUAGES = {"pt": "Portuguese", "es": "Spanish"}

    fake_tts = types.ModuleType("chatterbox.tts")
    fake_tts.ChatterboxTTS = FakeStandardTTS

    sys.modules["torch"] = fake_torch
    sys.modules["torchaudio"] = fake_torchaudio
    sys.modules["huggingface_hub"] = fake_hf
    sys.modules["chatterbox"] = fake_chatterbox
    sys.modules["chatterbox.models"] = fake_chatterbox_models
    sys.modules["chatterbox.models.s3gen"] = fake_s3gen
    sys.modules["chatterbox.mtl_tts"] = fake_mtl
    sys.modules["chatterbox.tts"] = fake_tts


def load_app_module():
    install_dependency_stubs()
    sys.modules.pop("app", None)
    return importlib.import_module("app")


app_module = load_app_module()
from fastapi.testclient import TestClient


class AppBehaviorTests(unittest.TestCase):
    def test_split_text_for_quality_keeps_short_text(self):
        self.assertEqual(app_module.split_text_for_quality("texto curto", max_chars=50), ["texto curto"])

    def test_split_text_for_quality_breaks_long_text(self):
        text = "Primeira frase bem longa para dividir. Segunda frase tambem longa para separar."
        chunks = app_module.split_text_for_quality(text, max_chars=30)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk) <= 30 for chunk in chunks))

    def test_validate_quality_mode_rejects_invalid_value(self):
        with self.assertRaises(app_module.HTTPException) as ctx:
            app_module.validate_quality_mode("turbo")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_config_exposes_quality_modes_and_limit(self):
        client = TestClient(app_module.app)
        response = client.get("/config")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("quality_modes", payload)
        self.assertEqual(payload["audio_prompt_max_mb"], 15)
        self.assertEqual(payload["quality_modes"][1]["id"], "max")
        language_ids = {item["id"] for item in payload["languages"]}
        self.assertIn("pt-br", language_ids)
        self.assertIn("pt-pt", language_ids)

    def test_api_docs_returns_html_document(self):
        client = TestClient(app_module.app)
        response = client.get("/api-docs")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers.get("content-type", ""))

    def test_resolve_generation_backend_routes_english_and_multilingual(self):
        standard_model = object()
        multilingual_model = object()
        with patch.object(app_module, "get_tts_model", return_value=standard_model), patch.object(
            app_module, "get_multilingual_model", return_value=multilingual_model
        ):
            model, backend = app_module.resolve_generation_backend("en")
            self.assertIs(model, standard_model)
            self.assertEqual(backend, "standard")

            model, backend = app_module.resolve_generation_backend("pt")
            self.assertIs(model, multilingual_model)
            self.assertEqual(backend, "multilingual")

    def test_generate_rejects_invalid_audio_prompt_extension(self):
        client = TestClient(app_module.app)
        fake_model = FakeModel()
        with patch.object(app_module, "resolve_generation_backend", return_value=(fake_model, "standard")):
            response = client.post(
                "/generate",
                data={"text": "teste", "language_id": "en", "quality_mode": "max"},
                files={"audio_prompt": ("voice.txt", io.BytesIO(b"invalid"), "text/plain")},
            )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Supported formats", response.json()["detail"])

    def test_generate_rejects_invalid_temperature(self):
        client = TestClient(app_module.app)
        response = client.post(
            "/generate",
            data={
                "text": "teste",
                "language_id": "en",
                "quality_mode": "max",
                "temperature": "2.5",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Temperature", response.json()["detail"])

    def test_generate_rejects_audio_prompt_above_limit(self):
        client = TestClient(app_module.app)
        fake_model = FakeModel()
        oversize = io.BytesIO(b"a" * (app_module.MAX_AUDIO_PROMPT_BYTES + 1))
        with patch.object(app_module, "resolve_generation_backend", return_value=(fake_model, "standard")):
            response = client.post(
                "/generate",
                data={"text": "teste", "language_id": "en", "quality_mode": "max"},
                files={"audio_prompt": ("voice.wav", oversize, "audio/wav")},
            )
        self.assertEqual(response.status_code, 413)
        self.assertIn("15 MB limit", response.json()["detail"])

    def test_generate_fast_mode_uses_direct_model_generation(self):
        client = TestClient(app_module.app)
        fake_model = FakeModel()
        with patch.object(app_module, "resolve_generation_backend", return_value=(fake_model, "standard")), patch.object(
            app_module, "generate_chunked_audio", side_effect=AssertionError("nao deveria usar chunking em fast"),
        ):
            response = client.post(
                "/generate",
                data={"text": "teste rapido", "language_id": "en", "quality_mode": "fast"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(fake_model.generate_calls), 1)

    def test_generate_returns_unique_output_filename_header(self):
        client = TestClient(app_module.app)
        fake_model = FakeModel()

        with patch.object(app_module, "resolve_generation_backend", return_value=(fake_model, "standard")), patch.object(
            app_module, "generate_chunked_audio", return_value=FakeTensor("chunked")
        ):
            response_one = client.post(
                "/generate",
                data={"text": "primeiro teste", "language_id": "en", "quality_mode": "max"},
            )
            response_two = client.post(
                "/generate",
                data={"text": "segundo teste", "language_id": "en", "quality_mode": "max"},
            )

        self.assertEqual(response_one.status_code, 200)
        self.assertEqual(response_two.status_code, 200)

        filename_one = response_one.headers.get("X-Output-Filename")
        filename_two = response_two.headers.get("X-Output-Filename")
        self.assertTrue(filename_one.startswith("chatterbox_"))
        self.assertTrue(filename_two.startswith("chatterbox_"))
        self.assertNotEqual(filename_one, filename_two)
        self.assertFalse((Path("output") / filename_one).exists())
        self.assertFalse((Path("output") / filename_two).exists())

    def test_generate_returns_request_id_header(self):
        client = TestClient(app_module.app)
        fake_model = FakeModel()
        with patch.object(app_module, "resolve_generation_backend", return_value=(fake_model, "standard")), patch.object(
            app_module, "generate_chunked_audio", return_value=FakeTensor("chunked")
        ):
            response = client.post(
                "/generate",
                data={"text": "teste", "language_id": "en", "quality_mode": "max"},
                headers={"X-Request-Id": "abc123"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("X-Request-Id"), "abc123")

    def test_generate_accepts_portuguese_alias_and_exposes_model_language_header(self):
        client = TestClient(app_module.app)
        fake_model = FakeModel()
        with patch.object(app_module, "resolve_generation_backend", return_value=(fake_model, "multilingual")), patch.object(
            app_module, "generate_chunked_audio", return_value=FakeTensor("chunked")
        ):
            response = client.post(
                "/generate",
                data={"text": "teste em portugues", "language_id": "pt-br", "quality_mode": "max"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("X-Language-Id"), "pt-br")
        self.assertEqual(response.headers.get("X-Model-Language-Id"), "pt")


if __name__ == "__main__":
    unittest.main()


