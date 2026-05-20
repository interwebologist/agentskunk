#!/usr/bin/env python3
"""Tools package namespace."""


def check_file_requirements():
    """File tools only require terminal backend availability."""
    return True


__all__ = ["check_file_requirements"]
