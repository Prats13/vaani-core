"""
Download LiveKit turn detector model weights from Hugging Face Hub

This script manually downloads the Qwen2.5-0.5B-Instruct turn detector model
used by livekit-plugins-turn-detector.

Usage:
    python download_turn_detector.py
"""

from huggingface_hub import hf_hub_download
import os
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    print("=" * 60)
    print("LiveKit Turn Detector Model Download")
    print("=" * 60)
    print("\nModel: livekit/turn-detector")
    print("Revision: v0.4.1-intl (Multilingual)")
    print("Size: ~400 MB (ONNX quantized model)")
    print("\nThis will download model files to Hugging Face cache.\n")

    repo_id = "livekit/turn-detector"
    revision = "v0.4.1-intl"  # Multilingual version

    # The plugin expects model_q8.onnx from the onnx/ subdirectory
    # and uses AutoTokenizer.from_pretrained() which needs all tokenizer files
    files_to_download = [
        "onnx/model_q8.onnx",
        "tokenizer.json",
        "tokenizer_config.json",
        "config.json",
        "ort_config.json",
        "generation_config.json",
        "special_tokens_map.json",
        "vocab.json",
        "merges.txt",
        "added_tokens.json",
        "languages.json"
    ]

    downloaded_files = {}

    try:
        for filename in files_to_download:
            print(f"Downloading {filename}...")
            print(f"  Repo: {repo_id}")

            file_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                revision=revision,
                cache_dir=None  # Use default HF cache location
            )

            downloaded_files[filename] = file_path

            # Get file size
            size_bytes = os.path.getsize(file_path)
            size_mb = size_bytes / (1024 * 1024)

            print(f"  ✓ Downloaded: {file_path}")
            print(f"  ✓ Size: {size_mb:.2f} MB\n")

        print("=" * 60)
        print("✅ SUCCESS! All model files downloaded.")
        print("=" * 60)
        print(f"\nFiles downloaded to Hugging Face cache (revision: {revision})")
        print("\nYou can now run your agent:")
        print("  python inbound_worker.py\n")

        return 0

    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ ERROR during download")
        print("=" * 60)
        print(f"\nError: {e}\n")
        print("Troubleshooting:")
        print("  1. Check internet connection")
        print("  2. Verify access to huggingface.co")
        print("  3. Install/upgrade huggingface-hub: pip install -U huggingface-hub")
        print("  4. Check disk space")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
