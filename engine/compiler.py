import subprocess
import os
from engine.timeline_model import TimelineProject, MediaClip, Transition
from ffmpeg.wrapper import detect_gpu_encoders, build_encoder_params

class FFmpegCompiler:
    def __init__(self, project: TimelineProject):
        self.project = project
        # Detect GPU once
        self.gpu_encoders = detect_gpu_encoders()
        self.encoder = self._pick_encoder()

    def _pick_encoder(self):
        if "nvenc" in self.gpu_encoders:
            return "nvenc"
        elif "qsv" in self.gpu_encoders:
            return "qsv"
        elif "amf" in self.gpu_encoders:
            return "amf"
        return "cpu"

    def compile(self, output_path: str, mode: str = "advanced"):
        """
        mode: 'fast' (stream copy, no filters) or 'advanced' (re-encode with filters)
        Returns ffmpeg command as list.
        """
        project = self.project
        fps = project.fps
        width, height = project.width, project.height

        # Collect unique source files and assign indices
        sources = {}
        for track in project.video_tracks:
            for clip in track.clips:
                if clip.source not in sources:
                    sources[clip.source] = []
                sources[clip.source].append(clip)
        for track in project.audio_tracks:
            for clip in track.clips:
                if clip.source not in sources:
                    sources[clip.source] = []
                sources[clip.source].append(clip)

        if mode == "fast":
            # Fast mode: stream copy, only works if no transitions, no effects, single track, no speed changes
            # Simplified: use concat demuxer for a single video track
            if len(project.video_tracks[0].clips) == 0:
                return None
            concat_file = "concat_list.txt"
            with open(concat_file, "w") as f:
                for clip in project.video_tracks[0].clips:
                    f.write(f"file '{clip.source}'\n")
                    f.write(f"inpoint {clip.start_time}\n")
                    f.write(f"outpoint {clip.end_time}\n")
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0", "-i", concat_file,
                "-c", "copy", output_path
            ]
            return cmd

        # Advanced mode: Build filter_complex
        inputs = []
        filter_lines = []
        # Map source file -> index
        file_index = {}  # path -> index
        for idx, src in enumerate(sources.keys()):
            inputs.extend(["-i", src])
            file_index[src] = idx

        # Process each video track -> one labeled output per track
        track_outputs = []
        for track_idx, track in enumerate(project.video_tracks):
            if not track.clips:
                continue
            # Build trimmed and concatenated segments for this track
            segments = []
            for clip in track.clips:
                src_idx = file_index[clip.source]
                # Trim input: [src_idx:v]trim=start=duration, setpts=PTS-STARTPTS
                start = clip.start_time
                duration = clip.end_time - clip.start_time
                # Account for speed
                if clip.speed != 1.0:
                    # We'll apply setpts later
                    pass
                segments.append(f"[{src_idx}:v]trim=start={start}:duration={duration},setpts=PTS-STARTPTS[vt{track_idx}s{clip.id[:4]}]")
            # Concatenate segments
            concat_inputs = " ".join([f"[vt{track_idx}s{c.id[:4]}]" for c in track.clips])
            filter_lines.append(
                f"{concat_inputs}concat=n={len(track.clips)}:v=1:a=0[trackv{track_idx}]"
            )
            track_outputs.append(f"[trackv{track_idx}]")

        # Apply transitions between clips on the same track (simplified: only first track for now)
        # TODO: Real transition handling with xfade overlap
        final_video = track_outputs[0] if track_outputs else None

        # If multiple video tracks, overlay them (higher index on top)
        # TODO: implement proper layering with opacity keyframes
        if len(track_outputs) > 1:
            base = track_outputs[0]
            for i in range(1, len(track_outputs)):
                # overlay with potential opacity
                filter_lines.append(
                    f"{base}{track_outputs[i]}overlay[overlay{i}]"
                )
                base = f"[overlay{i}]"
            final_video = base

        # Audio processing: per track mixdown
        audio_mix_outputs = []
        for track_idx, track in enumerate(project.audio_tracks):
            if not track.clips:
                continue
            segments = []
            for clip in track.clips:
                src_idx = file_index[clip.source]
                segments.append(f"[{src_idx}:a]atrim=start={clip.start_time}:duration={clip.end_time - clip.start_time},asetpts=PTS-STARTPTS[at{track_idx}s{clip.id[:4]}]")
            concat_inputs = " ".join([f"[at{track_idx}s{c.id[:4]}]" for c in track.clips])
            filter_lines.append(
                f"{concat_inputs}concat=n={len(track.clips)}:v=0:a=1[tracka{track_idx}]"
            )
            audio_mix_outputs.append(f"[tracka{track_idx}]")

        # Mix all audio tracks
        if len(audio_mix_outputs) > 1:
            filter_lines.append(
                f"{' '.join(audio_mix_outputs)}amix=inputs={len(audio_mix_outputs)}[outa]"
            )
            final_audio = "[outa]"
        elif len(audio_mix_outputs) == 1:
            final_audio = audio_mix_outputs[0]
        else:
            final_audio = None

        # Map outputs
        map_args = []
        if final_video:
            map_args.extend(["-map", final_video])
        if final_audio:
            map_args.extend(["-map", final_audio])

        # Encoder options
        enc_params = build_encoder_params(self.encoder)
        cmd = ["ffmpeg", "-y"] + inputs + ["-filter_complex", ";".join(filter_lines)] + map_args + enc_params + [output_path]
        return cmd