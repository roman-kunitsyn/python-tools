from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from voice_generator.decoders.snac import SnacDecoder


class SnacDecoderTests(TestCase):
    def test_decode_accepts_json_audio_tokens(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.wav"
            decoder = SnacDecoder()

            with patch("voice_generator.decoders.snac._load_snac_model") as load_model, patch(
                "voice_generator.decoders.snac._reconstruct_codebooks"
            ) as reconstruct:
                load_model.return_value.decode.return_value = [0.0, 0.1, -0.1, 0.0]
                reconstruct.return_value = [[1, 2], [3], [4], [5]]
                decoded = decoder.decode(
                    '{"audio_tokens": [1, 2, 3, 4]}',
                    output_path,
                    format="wav",
                )

            self.assertEqual(decoded, output_path)
            self.assertTrue(output_path.exists())
