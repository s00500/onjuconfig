#!/usr/bin/env python3
"""Receive the Onju mic debug stream (onjuconfig/nabu_micdebug.yml) and write WAV files.

    python3 tools/nabu_mic_rx.py [--port 41234] [--out DIR] [--seconds N]

Prints one line per second and stream: RMS and peak in dBFS and DC offset per channel,
plus lost packets. Writes <out>/<stream>_<timestamp>.wav (raw: 48 kHz 32 bit stereo,
16k: 16 kHz 16 bit mono). Ctrl-C stops and closes the files cleanly.
Stdlib only.
"""

import argparse
import math
import os
import socket
import struct
import sys
import time
import wave

HEADER = struct.Struct("<2sBBB3xII")
NAMES = {0: "raw", 1: "16k"}


class Stream:
    def __init__(self, sid, bits, channels, rate, outdir, stamp):
        self.name = NAMES.get(sid, f"s{sid}")
        self.bits, self.channels, self.rate = bits, channels, rate
        self.width = bits // 8
        self.fmt = {16: "h", 32: "i"}[bits]
        self.full = float(2 ** (bits - 1))
        path = os.path.join(outdir, f"{self.name}_{stamp}.wav")
        self.wav = wave.open(path, "wb")
        self.wav.setnchannels(channels)
        self.wav.setsampwidth(self.width)
        self.wav.setframerate(rate)
        self.path = path
        self.next_seq = None
        self.lost = 0
        self.packets = 0
        self.frames = 0
        self.reset_stats()

    def reset_stats(self):
        self.sq = [0.0] * self.channels
        self.sum = [0.0] * self.channels
        self.peak = [0] * self.channels
        self.n = 0

    def feed(self, seq, pcm):
        if self.next_seq is not None and seq != self.next_seq:
            gap = (seq - self.next_seq) & 0xFFFFFFFF
            if gap < 0x80000000:
                self.lost += gap
        self.next_seq = (seq + 1) & 0xFFFFFFFF
        self.packets += 1
        frame_bytes = self.width * self.channels
        pcm = pcm[: len(pcm) - len(pcm) % frame_bytes]
        self.wav.writeframesraw(pcm)
        count = len(pcm) // self.width
        samples = struct.unpack(f"<{count}{self.fmt}", pcm)
        for c in range(self.channels):
            ch = samples[c :: self.channels]
            self.sq[c] += sum(s * s for s in ch)
            self.sum[c] += sum(ch)
            self.peak[c] = max(self.peak[c], max((abs(s) for s in ch), default=0))
        self.n += count // self.channels
        self.frames += count // self.channels

    def report(self):
        if not self.n:
            return f"{self.name}: no data"
        parts = []
        for c in range(self.channels):
            rms = math.sqrt(self.sq[c] / self.n) / self.full
            dc = self.sum[c] / self.n / self.full
            pk = self.peak[c] / self.full
            parts.append(f"ch{c} rms {db(rms):6.1f} pk {db(pk):6.1f} dc {dc:+.5f}")
        line = f"{self.name}: " + " | ".join(parts) + f" | lost {self.lost}"
        self.reset_stats()
        return line

    def close(self):
        self.wav.close()
        return f"{self.path}: {self.frames / self.rate:.1f}s, {self.packets} packets, {self.lost} lost"


def db(x):
    return 20 * math.log10(x) if x > 0 else -999.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=41234)
    ap.add_argument("--out", default=".scratchpad/micdebug")
    ap.add_argument("--seconds", type=float, default=0, help="stop after N seconds (0 = until Ctrl-C)")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)
    sock.bind(("0.0.0.0", args.port))
    sock.settimeout(0.2)
    print(f"listening on udp/{args.port}, writing to {args.out}", file=sys.stderr)

    streams = {}
    start = time.monotonic()
    last = start
    try:
        while True:
            now = time.monotonic()
            if args.seconds and now - start >= args.seconds:
                break
            try:
                data, addr = sock.recvfrom(65535)
            except socket.timeout:
                data = None
            if data and len(data) > HEADER.size:
                magic, sid, bits, ch, rate, seq = HEADER.unpack_from(data)
                if magic == b"NB":
                    st = streams.get(sid)
                    if st is None:
                        st = streams[sid] = Stream(sid, bits, ch, rate, args.out, stamp)
                        print(f"{st.name}: {rate} Hz {bits} bit {ch} ch from {addr[0]}", file=sys.stderr)
                    st.feed(seq, data[HEADER.size :])
            if now - last >= 1.0:
                last = now
                for st in streams.values():
                    print(st.report(), flush=True)
    except KeyboardInterrupt:
        pass
    for st in streams.values():
        print(st.close(), file=sys.stderr)


if __name__ == "__main__":
    main()
