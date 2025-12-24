import os
import subprocess
import logging
from typing import List

logger = logging.getLogger(__name__)

class AudioMixer:
    def mix_episode(self, segments: List[str], output_path: str) -> str:
        """
        Concatenates audio segments and normalizes loudness to -16 LUFS.
        Returns the path to the final output file.
        """
        if not segments:
            raise ValueError("No segments provided for mixing.")

        # Create a temporary file list for ffmpeg concat demuxer
        list_file_path = "input_list.txt"
        try:
            with open(list_file_path, "w") as f:
                for segment in segments:
                    # ffmpeg requires absolute paths or relative paths safe for the demuxer
                    # escape backslashes for Windows
                    safe_path = segment.replace("\\", "/")
                    f.write(f"file '{safe_path}'\n")

            # 1. Concatenate
            # We use the concat demuxer (-f concat) which is safer than protocol
            # Then we pipe to loudnorm filter for normalization
            
            cmd = [
                "ffmpeg",
                "-y", # Overwrite output
                "-f", "concat",
                "-safe", "0",
                "-i", list_file_path,
                "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", # EBU R128 normalization
                "-c:a", "libmp3lame",
                "-q:a", "2", # High quality VBR
                output_path
            ]

            logger.info(f"Running ffmpeg mix command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if result.returncode != 0:
                logger.error(f"FFmpeg mixing failed: {result.stderr}")
                raise RuntimeError(f"FFmpeg failed: {result.stderr}")
            
            logger.info(f"Successfully mixed episode to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error during mixing: {e}")
            raise e
        finally:
            # Cleanup temp list file
            if os.path.exists(list_file_path):
                os.remove(list_file_path)
