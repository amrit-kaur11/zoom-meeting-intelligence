import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class VTTCue:
    start_time_str: str
    end_time_str: str
    start_seconds: float
    end_seconds: float
    speaker: str
    text: str


class VTTParser:
    @staticmethod
    def timestamp_to_seconds(ts: str) -> float:
        """Converts VTT timestamp (HH:MM:SS.mmm or MM:SS.mmm) to total float seconds."""
        parts = ts.strip().split(':')
        if len(parts) == 3:
            h, m, s = float(parts[0]), float(parts[1]), float(parts[2])
            return h * 3600 + m * 60 + s
        elif len(parts) == 2:
            m, s = float(parts[0]), float(parts[1])
            return m * 60 + s
        return 0.0

    @staticmethod
    def seconds_to_timestamp(seconds: float) -> str:
        """Converts float seconds to formatted HH:MM:SS string."""
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"

    @classmethod
    def clean_text(cls, text: str) -> (str, str):
        """
        Strips WebVTT metadata, voice tags <v Speaker Name>, HTML/formatting tags.
        Returns tuple of (speaker_name, clean_text).
        """
        speaker = "Unknown"
        
        # Extract <v Speaker Name> or <v.name Speaker Name>
        v_match = re.search(r'<v(?:\.\w+)?\s+([^>]+)>(.*?)(?:</v>|$)', text, re.IGNORECASE)
        if v_match:
            speaker = v_match.group(1).strip()
            text = v_match.group(2)
        else:
            # Check for Speaker: Text format directly in line
            speaker_match = re.match(r'^([^:\n]+):\s*(.*)$', text)
            if speaker_match:
                possible_speaker = speaker_match.group(1).strip()
                # Ensure it's not a timestamp or cue header
                if not re.match(r'^\d', possible_speaker):
                    speaker = possible_speaker
                    text = speaker_match.group(2)

        # Strip remaining HTML tags <...> </...>
        text = re.sub(r'<[^>]+>', '', text)
        # Strip WebVTT positioning / settings specs (e.g., align:start position:0%)
        text = re.sub(r'\b(align|position|size|line):[^\s]+', '', text)
        # Clean extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return speaker, text

    @classmethod
    def parse_single_vtt(cls, vtt_content: str) -> List[VTTCue]:
        """Parses a single WebVTT file content into a list of VTTCue objects."""
        cues: List[VTTCue] = []
        if not vtt_content:
            return cues

        # Split into blocks separated by double newlines
        blocks = re.split(r'\n\s*\n', vtt_content.strip())
        
        # Regex for timing line: 00:00:01.000 --> 00:00:04.000
        timing_pattern = re.compile(
            r'((?:\d{2}:)?\d{2}:\d{2}[\.,]\d{3})\s*-->\s*((?:\d{2}:)?\d{2}:\d{2}[\.,]\d{3})'
        )

        for block in blocks:
            lines = [line.strip() for line in block.splitlines() if line.strip()]
            if not lines:
                continue

            # Skip header WEBVTT or NOTE blocks
            if lines[0].startswith("WEBVTT") or lines[0].startswith("NOTE"):
                continue

            timing_line_idx = -1
            match = None
            for idx, line in enumerate(lines):
                match = timing_pattern.search(line)
                if match:
                    timing_line_idx = idx
                    break

            if not match or timing_line_idx == -1:
                continue

            start_ts = match.group(1).replace(',', '.')
            end_ts = match.group(2).replace(',', '.')
            start_sec = cls.timestamp_to_seconds(start_ts)
            end_sec = cls.timestamp_to_seconds(end_ts)

            # Combine remaining lines after timing line as transcript payload
            payload_lines = lines[timing_line_idx + 1:]
            raw_payload = " ".join(payload_lines)
            
            speaker, cleaned_payload = cls.clean_text(raw_payload)
            if cleaned_payload:
                cue = VTTCue(
                    start_time_str=start_ts,
                    end_time_str=end_ts,
                    start_seconds=start_sec,
                    end_seconds=end_sec,
                    speaker=speaker,
                    text=cleaned_payload
                )
                cues.append(cue)

        return cues

    @classmethod
    def combine_and_deduplicate(cls, vtt_contents: List[str]) -> List[VTTCue]:
        """
        Combines multiple VTT transcript contents across pause/resumes,
        sorts chronologically, and deduplicates overlapping cue segments.
        """
        all_cues: List[VTTCue] = []
        for content in vtt_contents:
            cues = cls.parse_single_vtt(content)
            all_cues.extend(cues)

        # Sort chronologically by start_seconds
        all_cues.sort(key=lambda c: (c.start_seconds, c.end_seconds))

        deduped_cues: List[VTTCue] = []
        for cue in all_cues:
            if not deduped_cues:
                deduped_cues.append(cue)
                continue

            last = deduped_cues[-1]
            
            # Check for exact or near duplicate (start times within 1 second and same speaker & text)
            if abs(cue.start_seconds - last.start_seconds) <= 1.5 and cue.speaker == last.speaker:
                if cue.text == last.text or cue.text in last.text:
                    continue  # skip duplicate
                elif last.text in cue.text:
                    # Upgrade with longer text
                    deduped_cues[-1] = cue
                    continue

            # Merge consecutive lines from same speaker if within 3 seconds
            if cue.speaker == last.speaker and (cue.start_seconds - last.end_seconds) <= 3.0:
                # Append text if not repeated
                if cue.text not in last.text:
                    last.text += f" {cue.text}"
                    last.end_seconds = max(last.end_seconds, cue.end_seconds)
                    last.end_time_str = cue.end_time_str
                continue

            deduped_cues.append(cue)

        return deduped_cues

    @classmethod
    def format_to_clean_text(cls, vtt_contents: List[str]) -> str:
        """
        Converts multiple VTT string contents into a clean 'Speaker: Text' output with timestamps.
        """
        cues = cls.combine_and_deduplicate(vtt_contents)
        if not cues:
            return "No transcript content available."

        formatted_lines = []
        for cue in cues:
            ts_label = cls.seconds_to_timestamp(cue.start_seconds)
            formatted_lines.append(f"[{ts_label}] {cue.speaker}: {cue.text}")

        return "\n".join(formatted_lines)
