"""Bounded, local workout parsers. Missing measurements stay missing."""

import io
from pathlib import Path
from typing import BinaryIO

import numpy as np
import pandas as pd
from defusedxml import ElementTree as ET

MAX_BYTES = 100 * 1024 * 1024


def read_bytes(source: str | Path | BinaryIO) -> bytes:
    """Read a bounded local file or in-memory upload without expanding archives."""
    data = Path(source).read_bytes() if isinstance(source, (str, Path)) else source.read()
    if len(data) > MAX_BYTES:
        raise ValueError("Workout file exceeds the 100 MB limit. Export a smaller selection.")
    return data


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Validate units and timestamps, sort samples, and preserve unknown values."""
    df = df.copy()
    if "timestamp" not in df and "elapsed_s" not in df:
        raise ValueError("Provide timestamp (ISO 8601) or elapsed_s.")
    if "timestamp" in df:
        df["timestamp"] = pd.to_datetime(df.timestamp, utc=True, errors="coerce")
        df = df.dropna(subset=["timestamp"]).sort_values("timestamp")
        if df.empty:
            raise ValueError("No valid timestamps.")
        df["elapsed_s"] = (df.timestamp - df.timestamp.iloc[0]).dt.total_seconds()
    df["elapsed_s"] = pd.to_numeric(df.elapsed_s, errors="coerce")
    df = df.dropna(subset=["elapsed_s"]).sort_values("elapsed_s")
    df = df.drop_duplicates("elapsed_s").reset_index(drop=True)
    if df.empty:
        raise ValueError("No valid workout samples.")
    for col in ["speed_mps", "heart_rate_bpm", "latitude", "longitude", "altitude_m"]:
        if col not in df:
            df[col] = np.nan
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df.loc[~np.isfinite(df[col]), col] = np.nan
    df.loc[(df.speed_mps < 0) | (df.speed_mps > 20), "speed_mps"] = np.nan
    df.loc[(df.heart_rate_bpm < 25) | (df.heart_rate_bpm > 250), "heart_rate_bpm"] = np.nan
    df.loc[~df.latitude.between(-90, 90), "latitude"] = np.nan
    df.loc[~df.longitude.between(-180, 180), "longitude"] = np.nan
    return df


def load_csv(source: str | Path | BinaryIO) -> pd.DataFrame:
    """Read canonical workout CSV; see DATA_GUIDE for required columns."""
    return normalize(pd.read_csv(io.BytesIO(read_bytes(source))))


def load_gpx(source: str | Path | BinaryIO) -> pd.DataFrame:
    """Read GPX track points and derive speed only across short valid intervals."""
    root = ET.fromstring(read_bytes(source))
    rows = []
    for trk in root.iter():
        if trk.tag.split("}")[-1] != "trkpt":
            continue
        row = {"latitude": trk.attrib.get("lat"), "longitude": trk.attrib.get("lon")}
        for child in trk.iter():
            key = child.tag.split("}")[-1]
            if key in {"time", "ele", "hr", "speed"}:
                row[
                    {
                        "time": "timestamp",
                        "ele": "altitude_m",
                        "hr": "heart_rate_bpm",
                        "speed": "speed_mps",
                    }[key]
                ] = child.text
        rows.append(row)
    if not rows:
        raise ValueError("No GPX track points.")
    df = normalize(pd.DataFrame(rows))
    # Derived GPS speed is explicitly identified and gap-limited.
    lat, lon = np.radians(df.latitude), np.radians(df.longitude)
    a = (
        np.sin(lat.diff() / 2) ** 2
        + np.cos(lat) * np.cos(lat.shift()) * np.sin(lon.diff() / 2) ** 2
    )
    dist = 6371000 * 2 * np.arctan2(np.sqrt(a.clip(0, 1)), np.sqrt((1 - a).clip(0, 1)))
    dt = df.elapsed_s.diff()
    derived = (dist / dt).where((dt > 0) & (dt <= 10))
    df["speed_source"] = np.where(df.speed_mps.notna(), "recorded", "derived_from_gps")
    df["speed_mps"] = df.speed_mps.fillna(derived.where(derived <= 20))
    return df


def load_health_xml(
    source: str | Path | BinaryIO, start: str | None = None, end: str | None = None
) -> pd.DataFrame:
    """Extract supported Health records inside an optional absolute time window."""
    root = ET.fromstring(read_bytes(source))
    mapping = {
        "HKQuantityTypeIdentifierHeartRate": "heart_rate_bpm",
        "HKQuantityTypeIdentifierRunningSpeed": "speed_mps",
    }
    rows = []
    for item in root.iter("Record"):
        a = item.attrib
        if a.get("type") not in mapping:
            continue
        when = pd.to_datetime(a.get("startDate"), utc=True, errors="coerce")
        if pd.isna(when):
            continue
        if start is not None and when < pd.to_datetime(start, utc=True):
            continue
        if end is not None and when > pd.to_datetime(end, utc=True):
            continue
        try:
            value = float(a["value"])
        except (ValueError, KeyError):
            continue
        field = mapping[a["type"]]
        unit = a.get("unit", "")
        if field == "speed_mps":
            if unit == "km/hr":
                value /= 3.6
            elif unit == "mi/hr":
                value *= 0.44704
            elif unit != "m/s":
                continue
        elif unit not in {"count/min", "bpm"}:
            continue
        rows.append({"timestamp": when, field: value})
    if not rows:
        raise ValueError("No supported heart-rate or running-speed samples in that time range.")
    return normalize(
        pd.DataFrame(rows).groupby("timestamp", as_index=False).mean(numeric_only=True)
    )


def merge_health_route(
    route: pd.DataFrame, health: pd.DataFrame, tolerance_s: float = 3
) -> pd.DataFrame:
    """Join Health measurements to route timestamps within a bounded tolerance."""
    if "timestamp" not in route or "timestamp" not in health:
        raise ValueError("Merging requires absolute timestamps in both files.")
    output = route.copy()
    for col in ["heart_rate_bpm", "speed_mps"]:
        samples = health[["timestamp", col]].dropna().sort_values("timestamp")
        if samples.empty:
            continue
        joined = pd.merge_asof(
            output[["timestamp"]].sort_values("timestamp"),
            samples,
            on="timestamp",
            direction="nearest",
            tolerance=pd.Timedelta(seconds=tolerance_s),
        )
        output[col] = output[col].fillna(joined[col].to_numpy())
    return normalize(output)
