"""Tests for audio player UI consistency."""

from flask import url_for

from now_lms.db import CursoRecurso, database, select


class TestAudioPlayerConsistency:
    """Test audio player UI consistency for files with and without subtitles."""

    def test_audio_without_subtitles_uses_enhanced_player(self, full_db_setup, client):
        """Test that audio files without subtitles use the enhanced player UI."""
        with full_db_setup.app_context():
            # Find an audio resource without subtitles
            audio_resource = database.session.execute(select(CursoRecurso).filter_by(tipo="mp3")).scalar_one_or_none()

            if audio_resource:
                # Ensure it has no subtitles
                audio_resource.subtitle_vtt = None
                database.session.commit()

                # Test the audio resource page
                response = client.get(
                    url_for("course.recurso", course_code=audio_resource.curso, resource_code=audio_resource.id)
                )

                assert response.status_code == 200
                response_text = response.get_data(as_text=True)

                # Check for enhanced player elements that should be present
                assert "player-container" in response_text
                assert "controls mt-3" in response_text
                assert 'id="playPause"' in response_text
                assert 'id="rewind5"' in response_text
                assert 'id="forward5"' in response_text
                assert 'id="prev"' in response_text
                assert 'id="next"' in response_text

                # Check that the basic HTML audio player is NOT present
                assert "audio-player-wrapper" not in response_text
                assert 'controls style="width: 100%"' not in response_text

                # Check for progress bar and time elements
                assert 'id="progressBar"' in response_text
                assert 'id="currentTime"' in response_text
                assert 'id="duration"' in response_text

    def test_audio_with_subtitles_keeps_enhanced_player(self, full_db_setup, client):
        """Test that audio files with subtitles continue to use the enhanced player UI."""
        with full_db_setup.app_context():
            # Find an audio resource
            audio_resource = database.session.execute(select(CursoRecurso).filter_by(tipo="mp3")).scalar_one_or_none()

            if audio_resource:
                # Add subtitles
                vtt_content = """WEBVTT

1
00:00:00.000 --> 00:00:05.000
Test subtitle line 1

2
00:00:05.000 --> 00:00:10.000
Test subtitle line 2
"""
                audio_resource.subtitle_vtt = vtt_content
                database.session.commit()

                # Test the audio resource page
                response = client.get(
                    url_for("course.recurso", course_code=audio_resource.curso, resource_code=audio_resource.id)
                )

                assert response.status_code == 200
                response_text = response.get_data(as_text=True)

                # Check for enhanced player elements
                assert "player-container" in response_text
                assert "controls mt-3" in response_text
                assert 'id="playPause"' in response_text
                assert 'id="rewind5"' in response_text
                assert 'id="forward5"' in response_text

                # Check for subtitle-specific elements
                assert 'id="lyrics-container"' in response_text
                assert 'track kind="subtitles"' in response_text

    def test_button_functionality_in_javascript(self, full_db_setup, client):
        """Test that the JavaScript contains the correct button functionality."""
        with full_db_setup.app_context():
            # Find an audio resource
            audio_resource = database.session.execute(select(CursoRecurso).filter_by(tipo="mp3")).scalar_one_or_none()

            if audio_resource:
                # Test without subtitles
                audio_resource.subtitle_vtt = None
                database.session.commit()

                response = client.get(
                    url_for("course.recurso", course_code=audio_resource.curso, resource_code=audio_resource.id)
                )

                assert response.status_code == 200
                response_text = response.get_data(as_text=True)

                # Check for new button handlers (5-second skip)
                assert 'getElementById("rewind5")' in response_text
                assert 'getElementById("forward5")' in response_text
                assert "currentTime - 5" in response_text
                assert "currentTime + 5" in response_text

                # Check that old dummy handlers are NOT present
                assert '"Repeat clicked"' not in response_text
                assert '"Shuffle clicked"' not in response_text

                # Check that existing 10-second handlers are still present
                assert "currentTime - 10" in response_text
                assert "currentTime + 10" in response_text

    def test_button_icons_and_titles(self, full_db_setup, client):
        """Test that buttons have appropriate icons and titles."""
        with full_db_setup.app_context():
            # Find an audio resource
            audio_resource = database.session.execute(select(CursoRecurso).filter_by(tipo="mp3")).scalar_one_or_none()

            if audio_resource:
                audio_resource.subtitle_vtt = None
                database.session.commit()

                response = client.get(
                    url_for("course.recurso", course_code=audio_resource.curso, resource_code=audio_resource.id)
                )

                assert response.status_code == 200
                response_text = response.get_data(as_text=True)

                # Check for appropriate button icons and titles
                assert 'id="rewind5"' in response_text
                assert 'title="Retroceder 5 segundos"' in response_text
                assert "bi-rewind" in response_text

                assert 'id="forward5"' in response_text
                assert 'title="Avanzar 5 segundos"' in response_text
                assert "bi-fast-forward" in response_text

                # Check that old icons are not present
                assert "bi-arrow-repeat" not in response_text
                assert "bi-shuffle" not in response_text

    def test_playback_speed_controls_present(self, full_db_setup, client):
        """Test that playback speed controls are present."""
        with full_db_setup.app_context():
            # Find an audio resource
            audio_resource = database.session.execute(select(CursoRecurso).filter_by(tipo="mp3")).scalar_one_or_none()

            if audio_resource:
                audio_resource.subtitle_vtt = None
                database.session.commit()

                response = client.get(
                    url_for("course.recurso", course_code=audio_resource.curso, resource_code=audio_resource.id)
                )

                assert response.status_code == 200
                response_text = response.get_data(as_text=True)

                # Check for playback speed control elements
                assert "Velocidad:" in response_text
                assert 'data-speed="0.5"' in response_text
                assert 'data-speed="0.75"' in response_text
                assert 'data-speed="1"' in response_text
                assert 'data-speed="1.5"' in response_text
                assert 'data-speed="2"' in response_text
                assert "0.5x" in response_text
                assert "0.75x" in response_text
                assert "1.5x" in response_text
                assert "2x" in response_text

                # Check for playback speed JavaScript
                assert "audio.playbackRate" in response_text
                assert ".speed-btn" in response_text

    def test_zoom_controls_present_with_subtitles(self, full_db_setup, client):
        """Test that zoom controls are present when subtitles are available."""
        with full_db_setup.app_context():
            # Find an audio resource
            audio_resource = database.session.execute(select(CursoRecurso).filter_by(tipo="mp3")).scalar_one_or_none()

            if audio_resource:
                # Add subtitles
                vtt_content = """WEBVTT

1
00:00:00.000 --> 00:00:05.000
Test subtitle line 1
"""
                audio_resource.subtitle_vtt = vtt_content
                database.session.commit()

                response = client.get(
                    url_for("course.recurso", course_code=audio_resource.curso, resource_code=audio_resource.id)
                )

                assert response.status_code == 200
                response_text = response.get_data(as_text=True)

                # Check for text size control elements
                assert "Tamaño texto:" in response_text
                assert 'id="zoomIn"' in response_text
                assert 'id="zoomOut"' in response_text
                assert 'title="Aumentar tamaño de texto"' in response_text
                assert 'title="Reducir tamaño de texto"' in response_text
                assert "bi-zoom-in" in response_text
                assert "bi-zoom-out" in response_text

                # Check for zoom JavaScript
                assert "currentFontSizeMultiplier" in response_text
                assert "updateLyricsFontSize" in response_text

    def test_zoom_controls_not_present_without_subtitles(self, full_db_setup, client):
        """Test that zoom controls are NOT present when subtitles are unavailable."""
        with full_db_setup.app_context():
            # Find an audio resource
            audio_resource = database.session.execute(select(CursoRecurso).filter_by(tipo="mp3")).scalar_one_or_none()

            if audio_resource:
                # Ensure no subtitles
                audio_resource.subtitle_vtt = None
                audio_resource.subtitle_vtt_secondary = None
                database.session.commit()

                response = client.get(
                    url_for("course.recurso", course_code=audio_resource.curso, resource_code=audio_resource.id)
                )

                assert response.status_code == 200
                response_text = response.get_data(as_text=True)

                # Check that text size control elements are NOT present
                assert "Tamaño texto:" not in response_text
                assert 'id="zoomIn"' not in response_text
                assert 'id="zoomOut"' not in response_text
