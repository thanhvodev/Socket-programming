import sys
from time import time
HEADER_SIZE = 12


def getbit(numberofbit, decimal):
    bit = bin(decimal)
    bit = bit[2:]
    lenoldbit = len(bit)
    if lenoldbit == numberofbit:
        return bit
    else:
        newbit = ''
        for i in range(numberofbit - lenoldbit):
            newbit += '0'
            i = i
        newbit += bit
        return newbit


class RtpPacket:
    header = bytearray(HEADER_SIZE)

    def __init__(self):
        pass

    def encode(self, version, padding, extension, cc, seqnum, marker, pt, ssrc, payload):
        """Encode the RTP packet with header fields and payload."""

        timestamp = int(time())
        headerc = bytearray(HEADER_SIZE)
        headerc[0] = headerc[0] | 1 << 7
        headerc[1] = pt
        headerc[2] = (seqnum >> 8) & 0xFF
        headerc[3] = seqnum & 0xFF
        s_timestamp = getbit(32, timestamp)
        headerc[4] = int(s_timestamp[0:8], 2)
        headerc[5] = int(s_timestamp[8:16], 2)
        headerc[6] = int(s_timestamp[16:24], 2)
        headerc[7] = int(s_timestamp[24:32], 2)
        headerc[8] = headerc[9] = headerc[10] = headerc[11] = 0

        self.header = headerc

        # Get the payload from the argument
        self.payload = payload

    def decode(self, byteStream):
        """Decode the RTP packet."""

        self.header = bytearray(byteStream[:HEADER_SIZE])
        self.payload = byteStream[HEADER_SIZE:]

    def version(self):
        """Return RTP version."""
        return int(self.header[0] >> 6)

    def seqNum(self):
        """Return sequence (frame) number."""
        seqNum = self.header[2] << 8 | self.header[3]
        return int(seqNum)

    def timestamp(self):
        """Return timestamp."""
        timestamp = self.header[4] << 24 | self.header[5] << 16 | self.header[6] << 8 | self.header[7]
        return int(timestamp)

    def payloadType(self):
        """Return payload type."""
        pt = self.header[1] & 127
        return int(pt)

    def getPayload(self):
        """Return payload."""
        return self.payload

    def getPacket(self):
        """Return RTP packet."""
        return self.header + self.payload
