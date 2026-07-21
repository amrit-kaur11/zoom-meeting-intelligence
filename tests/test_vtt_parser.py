import pytest
from parser.vtt_parser import VTTParser, VTTCue


def test_vtt_timestamp_conversion():
    assert VTTParser.timestamp_to_seconds("00:01:23.456") == 83.456
    assert VTTParser.timestamp_to_seconds("02:15.500") == 135.500
    assert VTTParser.seconds_to_timestamp(83.456) == "00:01:23"


def test_vtt_clean_text_voice_tags():
    raw = "<v Alice>We are discussing the backend architecture.</v>"
    speaker, clean = VTTParser.clean_text(raw)
    assert speaker == "Alice"
    assert clean == "We are discussing the backend architecture."


def test_vtt_parse_single_vtt():
    sample_vtt = """WEBVTT

00:00:01.000 --> 00:00:04.000
<v Alice>Hello everyone!

00:00:05.000 --> 00:00:08.000
<v Bob>Hi Alice, glad to be here.
"""
    cues = VTTParser.parse_single_vtt(sample_vtt)
    assert len(cues) == 2
    assert cues[0].speaker == "Alice"
    assert cues[0].text == "Hello everyone!"
    assert cues[1].speaker == "Bob"
    assert cues[1].text == "Hi Alice, glad to be here."


def test_vtt_multi_file_aggregation_and_deduplication():
    # Fragment 1 (Before pause)
    vtt1 = """WEBVTT

00:00:01.000 --> 00:00:05.000
<v Alice>Let's review the API design.

00:00:06.000 --> 00:00:10.000
<v Bob>Sure, I'll take notes.
"""
    # Fragment 2 (After resume - with overlapping timestamps due to pause/restart)
    vtt2 = """WEBVTT

00:00:06.000 --> 00:00:10.000
<v Bob>Sure, I'll take notes.

00:00:12.000 --> 00:00:15.000
<v Charlie>Joined late, sorry!
"""
    clean_transcript = VTTParser.format_to_clean_text([vtt1, vtt2])
    
    # Check deduplication of Bob's cue
    assert "Alice: Let's review the API design." in clean_transcript
    assert "Bob: Sure, I'll take notes." in clean_transcript
    assert "Charlie: Joined late, sorry!" in clean_transcript
    
    # Should only appear once for Bob
    assert clean_transcript.count("Bob: Sure, I'll take notes.") == 1
