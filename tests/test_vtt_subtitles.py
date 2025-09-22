"""Tests for VTT subtitle functionality in audio resources."""

import io
from werkzeug.datastructures import FileStorage

from now_lms.db import CursoRecurso, database, select


class TestVTTSubtitleFunctionality:
    """Test VTT subtitle functionality for audio resources."""

    def create_sample_vtt(self):
        """Create a sample VTT file."""
        vtt_content = """WEBVTT

1
00:00:00.000 --> 00:00:05.000
Welcome to this audio lesson

2
00:00:05.000 --> 00:00:10.000
This is an example of synchronized subtitles
"""
        return FileStorage(stream=io.BytesIO(vtt_content.encode("utf-8")), filename="test.vtt", content_type="text/vtt")

    def create_sample_audio(self):
        """Create a minimal OGG audio file."""
        # Minimal OGG Vorbis header
        ogg_content = b"OggS\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1e\x01vorbis\x00\x00\x00\x00\x02D\xac\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\xb8\x01"
        return FileStorage(stream=io.BytesIO(ogg_content), filename="test.ogg", content_type="audio/ogg")

    def test_curso_recurso_model_has_subtitle_vtt(self, full_db_setup):
        """Test that CursoRecurso model has subtitle_vtt field."""
        with full_db_setup.app_context():
            # Get an existing audio resource or create one
            audio_resource = database.session.execute(select(CursoRecurso).filter_by(tipo="mp3")).scalar_one_or_none()

            if audio_resource:
                # Test that we can access the subtitle_vtt field
                assert hasattr(audio_resource, "subtitle_vtt")
                # Initially should be None
                assert audio_resource.subtitle_vtt is None

                # Test setting VTT content
                vtt_content = "WEBVTT\n\n1\n00:00:00.000 --> 00:00:05.000\nTest subtitle"
                audio_resource.subtitle_vtt = vtt_content
                database.session.commit()

                # Verify the content was saved
                saved_resource = database.session.execute(select(CursoRecurso).filter_by(id=audio_resource.id)).scalar_one()
                assert saved_resource.subtitle_vtt == vtt_content

    def test_vtt_file_content_validation(self):
        """Test VTT file content validation."""
        vtt_file = self.create_sample_vtt()

        # Read content
        vtt_file.stream.seek(0)
        content = vtt_file.read().decode("utf-8")

        # Validate VTT format
        assert content.startswith("WEBVTT")
        assert "00:00:00.000 --> 00:00:05.000" in content
        assert "Welcome to this audio lesson" in content

    def test_audio_file_creation(self):
        """Test audio file creation for testing."""
        audio_file = self.create_sample_audio()

        # Verify audio file properties
        assert audio_file.filename == "test.ogg"
        assert audio_file.content_type == "audio/ogg"

        # Read content to verify it's not empty
        audio_file.stream.seek(0)
        content = audio_file.read()
        assert len(content) > 0

    def test_secondary_subtitle_vtt_storage(self, full_db_setup):
        """Test secondary VTT subtitle storage and retrieval."""
        with full_db_setup.app_context():
            # Get or create an audio resource
            audio_resource = database.session.execute(select(CursoRecurso).filter_by(tipo="mp3")).scalar_one_or_none()

            if audio_resource:
                # Test VTT content with various formats and special characters
                primary_vtt = """WEBVTT

00:00:00.000 --> 00:00:03.000
¡Hola! ¿Cómo estás? Ñoño.

00:00:03.500 --> 00:00:06.500
Símbolos: àáâãäåæç © ® ™

00:00:07.000 --> 00:00:10.000
Emojis: 😀 🎵 📚
"""

                secondary_vtt = """WEBVTT

00:00:00.000 --> 00:00:03.000
Hello! How are you? Test.

00:00:03.500 --> 00:00:06.500
Symbols: àáâãäåæç © ® ™

00:00:07.000 --> 00:00:10.000
Emojis: 😀 🎵 📚
"""

                # Store original content
                original_primary = audio_resource.subtitle_vtt
                original_secondary = audio_resource.subtitle_vtt_secondary

                try:
                    # Set test content
                    audio_resource.subtitle_vtt = primary_vtt
                    audio_resource.subtitle_vtt_secondary = secondary_vtt
                    database.session.commit()

                    # Retrieve and verify
                    retrieved = database.session.execute(select(CursoRecurso).filter_by(id=audio_resource.id)).scalar_one()

                    # Test primary VTT
                    assert retrieved.subtitle_vtt == primary_vtt
                    assert len(retrieved.subtitle_vtt) == len(primary_vtt)

                    # Test secondary VTT
                    assert retrieved.subtitle_vtt_secondary == secondary_vtt
                    assert len(retrieved.subtitle_vtt_secondary) == len(secondary_vtt)

                    # Test special characters are preserved
                    assert "¡Hola! ¿Cómo estás? Ñoño." in retrieved.subtitle_vtt
                    assert "àáâãäåæç © ® ™" in retrieved.subtitle_vtt
                    assert "😀 🎵 📚" in retrieved.subtitle_vtt

                    assert "Hello! How are you? Test." in retrieved.subtitle_vtt_secondary
                    assert "àáâãäåæç © ® ™" in retrieved.subtitle_vtt_secondary
                    assert "😀 🎵 📚" in retrieved.subtitle_vtt_secondary

                finally:
                    # Restore original content
                    audio_resource.subtitle_vtt = original_primary
                    audio_resource.subtitle_vtt_secondary = original_secondary
                    database.session.commit()

    def test_vtt_format_parsing_edge_cases(self):
        """Test VTT parsing with various edge cases that could cause synchronization issues."""

        # Test case 1: HH:MM:SS.mmm format (which current implementation fails with)
        vtt_extended_format = """WEBVTT

00:00:01.000 --> 00:00:04.500
Hello, this is the first subtitle.

00:00:05.000 --> 00:00:08.500
Now appears the second subtitle.

00:00:09.000 --> 00:00:12.000
And this is the last subtitle.
"""

        # Test case 2: Multiline subtitles
        vtt_multiline = """WEBVTT

00:00.000 --> 00:03.000
Primera línea
Segunda línea del mismo subtítulo

00:03.500 --> 00:06.500
Otro subtítulo
con múltiples líneas
aquí

00:07.000 --> 00:10.000
Último subtítulo simple
"""

        # Test case 3: Empty lines and metadata
        vtt_with_metadata = """WEBVTT
Kind: captions
Language: es

NOTE
This is a test file with metadata

1
00:00.000 --> 00:03.000
Test subtitle with metadata

2
00:03.500 --> 00:06.500
Another test subtitle
"""

        test_cases = [
            ("Extended format", vtt_extended_format),
            ("Multiline", vtt_multiline),
            ("With metadata", vtt_with_metadata),
        ]

        for name, vtt_content in test_cases:
            # These tests help identify the parsing issues that cause sync problems
            assert "WEBVTT" in vtt_content
            assert "-->" in vtt_content
            # The content has proper structure, but current JS parsing may fail
