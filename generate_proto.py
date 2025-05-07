#!/usr/bin/env python3
import os
import subprocess
import sys


def generate_proto():
    proto_file = "confidence/telemetry.proto"
    output_dir = "confidence"

    # Check if protoc is installed
    try:
        version = subprocess.check_output(["protoc", "--version"]).decode().strip()
        print(f"Found protoc version: {version}")
    except FileNotFoundError:
        print("Error: protoc compiler not found. Please install it first.")
        print("You can install it via:")
        print("  - macOS: brew install protobuf")
        print("  - Linux: apt-get install protobuf-compiler")
        print(
            "  - Windows: Download from "
            "https://github.com/protocolbuffers/protobuf/releases"
        )
        sys.exit(1)

    # Generate Python code
    cmd = [
        "protoc",
        f"--python_out={output_dir}",
        f"--proto_path={os.path.dirname(proto_file)}",
        proto_file,
    ]

    print(f"Generating Python code from {proto_file}...")
    try:
        subprocess.check_call(cmd)
        output_file = os.path.join(
            output_dir, os.path.basename(os.path.splitext(proto_file)[0]) + "_pb2.py"
        )
        print(f"Successfully generated {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error generating proto code: {e}")
        sys.exit(1)


if __name__ == "__main__":
    generate_proto()
