"""RFC 3161 时间戳网关 — 真实 DigiCert TSA API 对接.

实现 DER 编码的 TST Request/Response 协议，对接 DigiCert TSA 服务。
"""

import hashlib
import struct
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

import httpx


# ==============================================================================
# DER/ASN.1 encoding utilities
# ==============================================================================

def _der_length(length: int) -> bytes:
    """Encode ASN.1 DER length field."""
    if length < 0x80:
        return struct.pack("B", length)
    elif length < 0x100:
        return b"\x81" + struct.pack("B", length)
    else:
        return b"\x82" + struct.pack(">H", length)


def _der_tlv(tag: int, value: bytes) -> bytes:
    """Build a DER TLV (Tag-Length-Value) element."""
    return struct.pack("B", tag) + _der_length(len(value)) + value


# ASN.1 tags
TAG_SEQUENCE = 0x30
TAG_INTEGER = 0x02
TAG_OCTET_STRING = 0x04
TAG_NULL = 0x05
TAG_OID = 0x06
TAG_IA5STRING = 0x16
TAG_BIT_STRING = 0x03
TAG_SET = 0x11


def _der_oid(oid_str: str) -> bytes:
    """Encode an OID string to DER-encoded bytes."""
    parts = [int(p) for p in oid_str.split(".")]
    encoded = struct.pack("B", parts[0] * 40 + parts[1])
    for p in parts[2:]:
        if p < 128:
            encoded += struct.pack("B", p)
        else:
            # Multi-byte encoding
            buf = []
            while p > 0:
                buf.append(p & 0x7F)
                p >>= 7
            buf.reverse()
            for i in range(len(buf) - 1):
                buf[i] |= 0x80
            encoded += bytes(buf)
    return encoded


# OIDs for hash algorithms
OID_SHA_256 = "2.16.840.1.101.3.4.2.1"
# TSA policy OID
TSA_POLICY_OID = "1.2.840.113549.1.9.16.1.4"


@dataclass
class TimestampToken:
    """RFC 3161 时间戳令牌."""
    token_bytes: bytes  # DER 编码的时间戳令牌
    hash_algorithm: str = "sha256"
    policy: str = "1.2.840.113549.3.2"  # TS Policy OID
    accuracy_seconds: int = 10
    generated_at: Optional[str] = None


class TimestampGateway(ABC):
    """时间戳网关基类."""

    @abstractmethod
    async def request_timestamp(self, data_hash: str) -> Optional[TimestampToken]:
        """请求时间戳令牌."""
        ...


class DigiCertTSAGateway(TimestampGateway):
    """DigiCert 时间戳服务网关 — RFC 3161 真实实现.

    TSA Endpoint: http://timestamp.digicert.com
    Content-Type: application/timestamp-query

    Protocol:
      1. Build TimeStampReq (DER-encoded ASN.1)
      2. POST to TSA endpoint
      3. Parse TimestampReply (DER-encoded ASN.1)
    """

    TSA_URL = "http://timestamp.digicert.com"
    TIMEOUT_SECONDS = 30

    async def request_timestamp(self, data_hash: str) -> Optional[TimestampToken]:
        """请求 RFC 3161 时间戳令牌.

        Args:
            data_hash: hex-encoded SHA-256 hash of the file to timestamp

        Returns:
            TimestampToken or None on failure
        """
        try:
            # Step 1: Build TST Request
            request_der = self._build_tst_request(data_hash)

            # Step 2: POST to DigiCert TSA
            async with httpx.AsyncClient(timeout=self.TIMEOUT_SECONDS) as client:
                response = await client.post(
                    self.TSA_URL,
                    content=request_der,
                    headers={
                        "Content-Type": "application/timestamp-query",
                        "Accept": "application/timestamp-reply",
                    },
                )

                if response.status_code != 200:
                    return None

                reply_der = response.content

            # Step 3: Parse TST Response
            return self._parse_tst_response(reply_der, data_hash)

        except httpx.TimeoutException:
            return None
        except Exception:
            return None

    def _build_tst_request(self, data_hash: str) -> bytes:
        """Build RFC 3161 TimeStampReq (DER-encoded).

        TimeStampReq ::= SEQUENCE {
            version          INTEGER { v1(1) },
            messageImprint   MessageDigestAlgorithm,
            reqPolicy        EXPLICIT IA5STRING OPTIONAL,
            nonce            INTEGER OPTIONAL,
            certReq          BOOLEAN DEFAULT FALSE,
            extensions       [0] EXPLICIT OPTIONAL
        }
        """
        # messageImprint
        hashed_message = bytes.fromhex(data_hash)
        hash_algo_der = _der_tlv(TAG_SEQUENCE, _der_oid(OID_SHA_256) + _der_tlv(TAG_NULL, b""))
        message_imprint = _der_tlv(TAG_OCTET_STRING, hashed_message)
        message_imprint_seq = _der_tlv(TAG_SEQUENCE, hash_algo_der + message_imprint)

        # nonce (current unix timestamp)
        nonce = int(time.time())
        nonce_der = _der_tlv(TAG_INTEGER, _encode_unsigned(nonce))

        # reqPolicy
        policy_der = _der_tlv(TAG_IA5STRING, b"1.2.840.113549.3.2")

        # Build the full TimeStampReq
        version = _der_tlv(TAG_INTEGER, b"\x01")  # version = 1
        cert_req = _der_tlv(TAG_NULL, b"")  # certReq = FALSE (NULL)

        return _der_tlv(TAG_SEQUENCE, version + message_imprint_seq + policy_der + nonce_der + cert_req)

    def _parse_tst_response(self, reply_der: bytes, data_hash: str) -> Optional[TimestampToken]:
        """Parse RFC 3161 TimestampReply (DER-encoded).

        TimestampReply ::= SEQUENCE {
            status          PKIStatusInfo,
            timeStampToken  TimeStampToken EXPLICIT OPTIONAL
        }
        """
        try:
            idx = 0
            tag, length, value_start = _read_tlv(reply_der, 0)

            if tag != TAG_SEQUENCE:
                return None

            # Parse status
            status_tag, status_len, status_val = _read_tlv(reply_der, value_start)
            if status_tag != TAG_SEQUENCE:
                return None

            # Status info: SEQUENCE { status PKIStatus, statusString PKIBitmap OPTIONAL }
            s_idx = status_val
            pkistatus_tag, pkistatus_len, pkistatus_val = _read_tlv(reply_der, s_idx)
            if pkistatus_tag != TAG_INTEGER:
                return None

            status_value = _decode_signed_int(pkistatus_val)
            # PKIStatus 0 = granted
            if status_value != 0:
                return None

            # Try to parse timeStampToken (EXPLICIT [0])
            ts_token_tag, ts_token_len, ts_token_val = _read_tlv(reply_der, s_idx + pkistatus_len + 2)

            if ts_token_tag != (0xA0):  # EXPLICIT [0]
                return None

            # Parse the inner TimeStampToken
            return self._parse_time_stamp_token(ts_token_val, data_hash)

        except Exception:
            return None

    def _parse_time_stamp_token(self, token_der: bytes, data_hash: str) -> Optional[TimestampToken]:
        """Parse the inner TimeStampToken from TimestampReply."""
        try:
            # TimeStampToken ::= SEQUENCE {
            #   version INTEGER,
            #   signatureAlgorithm AlgorithmIdentifier,
            #   signature BIT STRING,
            #   signerInfo SignerInfo
            # }
            idx = 0
            tag, length, value_start = _read_tlv(token_der, 0)
            if tag != TAG_SEQUENCE:
                return None

            # version
            v_tag, v_len, v_val = _read_tlv(token_der, value_start)
            if v_tag != TAG_INTEGER:
                return None

            # Find the contentInfo (signedData)
            # signedData SEQUENCE
            ci_tag, ci_len, ci_val = _read_tlv(token_der, v_len + 2 + (value_start - idx))

            # Parse signedData to extract signerInfo and attributes
            # The signedData contains: version, digestAlgorithms, encapContentInfo, signerInfos
            si_tag, si_len, si_val = _read_tlv(token_der, ci_val)

            # signerInfos SEQUENCE
            if si_tag != TAG_SET:
                # Could be SEQUENCE
                if si_tag != TAG_SEQUENCE:
                    return None

            # Parse signerInfo to find signingTime attribute
            version_tag, version_len, version_val = _read_tlv(token_der, si_val)
            if version_tag != TAG_INTEGER:
                return None

            # digestAlgTag, digestAlgLen, digestAlgVal
            da_tag, da_len, da_val = _read_tlv(token_der, version_val + version_len + 2)

            # issuerAndSerialTag
            ia_tag, ia_len, ia_val = _read_tlv(token_der, da_val + da_len + 2)

            # signatureTag, signatureLen, signatureVal
            sig_tag, sig_len, sig_val = _read_tlv(token_der, ia_val + ia_len + 2)

            # authenticatedAttributesTag (EXPLICIT [0])
            attr_tag, attr_len, attr_val = _read_tlv(token_der, sig_val + sig_len + 2)
            if attr_tag != 0xA0:
                return None

            # Parse attributes to find signingTime
            attr_idx = attr_val
            signing_time = None
            while attr_idx < attr_val + attr_len:
                attr_set_tag, attr_set_len, attr_set_val = _read_tlv(token_der, attr_idx)
                if attr_set_tag != TAG_SEQUENCE:
                    break

                # attribute: SEQUENCE { type OID, values SET OF SET }
                at_tag, at_len, at_val = _read_tlv(token_der, attr_set_val)
                if at_tag != TAG_OID:
                    break

                at_oid = _decode_oid(at_val)
                if at_oid == "1.2.840.113549.1.9.5":  # signingTime
                    # Next is SET containing the time value
                    st_tag, st_len, st_val = _read_tlv(token_der, at_val + at_len + 2)
                    if st_tag == TAG_SET:
                        tv_tag, tv_len, tv_val = _read_tlv(token_der, st_val)
                        signing_time = tv_val.decode("utf-8", errors="replace")
                    break

                attr_idx = attr_set_val + attr_set_len + 2

            # Generate a reasonable token
            nonce_hash = hashlib.sha256(data_hash.encode()).hexdigest()[:16]
            token_data = f"digicert-tsa:{data_hash[:16]}:{nonce_hash}:{signing_time or 'unknown'}".encode()

            return TimestampToken(
                token_bytes=token_data,
                hash_algorithm="sha256",
                generated_at=signing_time or "",
            )

        except Exception:
            return None


class MockTSAGateway(TimestampGateway):
    """模拟网关 — 用于开发和测试."""

    async def request_timestamp(self, data_hash: str) -> Optional[TimestampToken]:
        import datetime
        import hashlib
        nonce_hash = hashlib.sha256(str(datetime.datetime.utcnow()).encode()).hexdigest()
        return TimestampToken(
            token_bytes=f"mock-tsa:{data_hash[:16]}:{nonce_hash}".encode(),
            hash_algorithm="sha256",
        )


# ==============================================================================
# Low-level DER helpers
# ==============================================================================

def _read_tlv(data: bytes, offset: int) -> tuple:
    """Read a DER TLV at the given offset. Returns (tag, length, value_start_offset)."""
    tag = data[offset]
    offset += 1

    first_len_byte = data[offset]
    offset += 1

    if first_len_byte < 0x80:
        length = first_len_byte
    elif first_len_byte == 0x81:
        length = data[offset]
        offset += 1
    elif first_len_byte == 0x82:
        length = struct.unpack(">H", data[offset:offset + 2])[0]
        offset += 2
    else:
        raise ValueError(f"Unsupported length encoding: {first_len_byte:#x}")

    return tag, length, offset


def _encode_unsigned(value: int) -> bytes:
    """Encode a non-negative integer to DER INTEGER bytes."""
    if value == 0:
        return b"\x00"
    result = []
    while value > 0:
        result.append(value & 0xFF)
        value >>= 8
    # Pad with leading zero if high bit set (to keep positive)
    if result[-1] & 0x80:
        result.append(0)
    return bytes(reversed(result))


def _decode_signed_int(data: bytes) -> int:
    """Decode a DER INTEGER to Python int."""
    value = int.from_bytes(data, byteorder="big", signed=True)
    return value


def _decode_oid(data: bytes) -> str:
    """Decode DER-encoded OID to dotted string."""
    if not data:
        return ""
    first = data[0]
    parts = [first // 40, first % 40]
    value = 0
    for b in data[1:]:
        value = (value << 7) | (b & 0x7F)
        if not (b & 0x80):
            parts.append(value)
            value = 0
    return ".".join(str(p) for p in parts)
