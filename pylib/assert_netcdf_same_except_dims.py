#!/usr/bin/env python3
"""
Assert that two NetCDF files are identical except for allowed dimension renames.

Default allowed renames:

    lon -> longitude
    lat -> latitude

This checker compares, recursively through groups:

  - NetCDF data model / format
  - group names
  - dimension names, lengths, unlimited status
  - variable names
  - variable dimensions, after applying allowed dimension-name mapping
  - variable shapes
  - variable dtypes / datatypes
  - variable attributes, including absence/presence of _FillValue
  - global/group attributes
  - raw variable data, with mask/scale/string decoding disabled
  - compression filters
  - chunking
  - endian-ness
  - user-defined type definitions, where exposed by netCDF4

It exits with:
  0 if files match under the allowed dimension mapping
  1 if differences are found
  2 on usage/runtime error

Requires:
  pip install netCDF4 numpy
"""

from __future__ import annotations

import argparse
import math
import sys

from dataclasses import dataclass
from functools import reduce
from operator import mul
from pathlib import Path
from typing import Any

import numpy as np

from netCDF4 import Dataset


DEFAULT_DIM_MAP = {
    "lon": "longitude",
    "lat": "latitude",
}


@dataclass
class Difference:
    path: str
    message: str


class DifferenceCollector:
    def __init__(self, max_errors: int) -> None:
        self.max_errors = max_errors
        self.items: list[Difference] = []
        self.stopped = False

    def add(self, path: str, message: str) -> None:
        if self.stopped:
            return

        self.items.append(Difference(path, message))

        if len(self.items) >= self.max_errors:
            self.stopped = True

    def ok(self) -> bool:
        return not self.items


def parse_dim_map(values: list[str]) -> dict[str, str]:
    dim_map: dict[str, str] = {}

    for value in values:
        if "=" not in value:
            raise ValueError(f"Invalid mapping {value!r}. Use OLD=NEW, for example lon=longitude.")

        old, new = value.split("=", 1)
        old = old.strip()
        new = new.strip()

        if not old or not new:
            raise ValueError(f"Invalid mapping {value!r}.")

        dim_map[old] = new

    return dim_map


def mapped_dim_name(name: str, dim_map: dict[str, str]) -> str:
    return dim_map.get(name, name)


def mapped_dim_tuple(dimensions: tuple[str, ...], dim_map: dict[str, str]) -> tuple[str, ...]:
    return tuple(mapped_dim_name(name, dim_map) for name in dimensions)


def product(values: tuple[int, ...]) -> int:
    if not values:
        return 1
    return reduce(mul, values, 1)


def stable_repr(value: Any) -> str:
    if isinstance(value, np.dtype):
        return value.str

    if isinstance(value, np.ndarray):
        return f"ndarray(dtype={value.dtype.str}, shape={value.shape}, data={value.tolist()!r})"

    return repr(value)


def dtype_signature(value: Any) -> str:
    try:
        return str(np.asarray(value).dtype)
    except Exception:
        return type(value).__name__


def scalar_equal(a: Any, b: Any) -> bool:
    if isinstance(a, np.ndarray) or isinstance(b, np.ndarray):
        return arrays_equal(a, b)

    if isinstance(a, np.generic):
        a = a.item()

    if isinstance(b, np.generic):
        b = b.item()

    if isinstance(a, float) and isinstance(b, float):
        if math.isnan(a) and math.isnan(b):
            return True

    return a == b


def arrays_equal(a: Any, b: Any) -> bool:
    aa = np.asarray(a)
    bb = np.asarray(b)

    if aa.shape != bb.shape:
        return False

    if aa.dtype != bb.dtype:
        return False

    if aa.dtype.kind == "O" or bb.dtype.kind == "O":
        for idx in np.ndindex(aa.shape):
            if not scalar_equal(aa[idx], bb[idx]):
                return False
        return True

    if aa.dtype.kind in {"f", "c"}:
        return np.array_equal(aa, bb, equal_nan=True)

    return np.array_equal(aa, bb)


def compare_values(
    diffs: DifferenceCollector,
    path: str,
    left: Any,
    right: Any,
    *,
    check_dtype: bool = True,
) -> None:
    if diffs.stopped:
        return

    if isinstance(left, str) or isinstance(right, str):
        if left != right:
            diffs.add(path, f"value differs: {left!r} != {right!r}")
        return

    if check_dtype and dtype_signature(left) != dtype_signature(right):
        diffs.add(
            path,
            f"dtype differs: {dtype_signature(left)!r} != {dtype_signature(right)!r}",
        )
        return

    try:
        equal = arrays_equal(left, right)
    except Exception:
        equal = left == right

    if not equal:
        diffs.add(path, f"value differs: {stable_repr(left)} != {stable_repr(right)}")


def ordered_keys(mapping: Any) -> list[str]:
    return list(mapping.keys())


def compare_key_lists(
    diffs: DifferenceCollector,
    path: str,
    left_keys: list[str],
    right_keys: list[str],
    *,
    ignore_order: bool,
) -> None:
    if diffs.stopped:
        return

    if ignore_order:
        left_set = set(left_keys)
        right_set = set(right_keys)

        missing = sorted(left_set - right_set)
        extra = sorted(right_set - left_set)

        if missing:
            diffs.add(path, f"missing names in new file: {missing!r}")

        if extra:
            diffs.add(path, f"extra names in new file: {extra!r}")

    else:
        if left_keys != right_keys:
            diffs.add(
                path,
                f"name/order differs:\n  original: {left_keys!r}\n  new:      {right_keys!r}",
            )


def compare_attrs(
    diffs: DifferenceCollector,
    path: str,
    left_obj: Any,
    right_obj: Any,
    *,
    ignore_order: bool,
) -> None:
    if diffs.stopped:
        return

    left_attrs = list(left_obj.ncattrs())
    right_attrs = list(right_obj.ncattrs())

    compare_key_lists(
        diffs,
        f"{path}/attrs",
        left_attrs,
        right_attrs,
        ignore_order=ignore_order,
    )

    common = sorted(set(left_attrs) & set(right_attrs))

    for attr_name in common:
        if diffs.stopped:
            return

        left_value = left_obj.getncattr(attr_name)
        right_value = right_obj.getncattr(attr_name)

        compare_values(
            diffs,
            f"{path}/attrs/{attr_name}",
            left_value,
            right_value,
        )


def disable_auto_decoding(group: Any) -> None:
    for var in group.variables.values():
        try:
            var.set_auto_maskandscale(False)
        except Exception:
            pass

        try:
            var.set_auto_chartostring(False)
        except Exception:
            pass

    for child in group.groups.values():
        disable_auto_decoding(child)


def variable_datatype_signature(var: Any) -> str:
    pieces = {
        "dtype": getattr(var, "dtype", None),
        "datatype": getattr(var, "datatype", None),
    }

    return stable_repr({key: stable_repr(value) for key, value in pieces.items()})


def safe_call(obj: Any, method_name: str) -> Any:
    method = getattr(obj, method_name, None)

    if method is None:
        return "<method unavailable>"

    try:
        return method()
    except Exception as exc:
        return f"<error calling {method_name}: {type(exc).__name__}: {exc}>"


def variable_storage_signature(var: Any) -> dict[str, Any]:
    signature = {
        "chunking": safe_call(var, "chunking"),
        "endian": safe_call(var, "endian"),
        "filters": safe_call(var, "filters"),
    }

    # Present in newer netCDF4 versions for quantized variables.
    if hasattr(var, "quantization"):
        signature["quantization"] = safe_call(var, "quantization")

    return signature


def compare_storage(
    diffs: DifferenceCollector,
    path: str,
    left_var: Any,
    right_var: Any,
) -> None:
    left_sig = variable_storage_signature(left_var)
    right_sig = variable_storage_signature(right_var)

    if left_sig != right_sig:
        diffs.add(
            path,
            f"storage differs:\n  original: {left_sig!r}\n  new:      {right_sig!r}",
        )


def iter_slices(shape: tuple[int, ...], max_elements: int):
    if not shape:
        yield Ellipsis
        return

    if 0 in shape:
        yield tuple(slice(0, 0) if size == 0 else slice(None) for size in shape)
        return

    if len(shape) == 1:
        step = max(1, max_elements)
    else:
        trailing_size = product(tuple(shape[1:]))
        step = max(1, max_elements // max(1, trailing_size))

    for start in range(0, shape[0], step):
        stop = min(shape[0], start + step)
        yield (slice(start, stop),) + tuple(slice(None) for _ in shape[1:])


def slice_label(indexer: Any) -> str:
    if indexer is Ellipsis:
        return "[...]"

    parts = []

    for item in indexer:
        if isinstance(item, slice):
            start = "" if item.start is None else item.start
            stop = "" if item.stop is None else item.stop
            step = "" if item.step is None else item.step

            if item.step is None:
                parts.append(f"{start}:{stop}")
            else:
                parts.append(f"{start}:{stop}:{step}")
        else:
            parts.append(str(item))

    return "[" + ", ".join(parts) + "]"


def compare_variable_data(
    diffs: DifferenceCollector,
    path: str,
    left_var: Any,
    right_var: Any,
    *,
    max_elements: int,
    bitwise: bool,
) -> None:
    if diffs.stopped:
        return

    if left_var.shape != right_var.shape:
        diffs.add(path, f"shape differs: {left_var.shape!r} != {right_var.shape!r}")
        return

    for indexer in iter_slices(tuple(left_var.shape), max_elements):
        if diffs.stopped:
            return

        left_data = np.asarray(left_var[indexer])
        right_data = np.asarray(right_var[indexer])

        if left_data.shape != right_data.shape:
            diffs.add(
                f"{path}/data{slice_label(indexer)}",
                f"chunk shape differs: {left_data.shape!r} != {right_data.shape!r}",
            )
            return

        if left_data.dtype != right_data.dtype:
            diffs.add(
                f"{path}/data{slice_label(indexer)}",
                f"chunk dtype differs: {left_data.dtype!r} != {right_data.dtype!r}",
            )
            return

        if bitwise and left_data.dtype.kind not in {"O", "U", "S"}:
            if left_data.tobytes(order="C") != right_data.tobytes(order="C"):
                diffs.add(
                    f"{path}/data{slice_label(indexer)}",
                    "raw bytes differ",
                )
                return
        else:
            if not arrays_equal(left_data, right_data):
                diffs.add(
                    f"{path}/data{slice_label(indexer)}",
                    "data values differ",
                )
                return


def type_signature(type_obj: Any) -> dict[str, str]:
    result: dict[str, str] = {
        "class": type_obj.__class__.__name__,
        "repr": repr(type_obj),
    }

    for attr in [
        "name",
        "dtype",
        "enum_dict",
        "datatype",
        "base_type",
    ]:
        if hasattr(type_obj, attr):
            try:
                result[attr] = stable_repr(getattr(type_obj, attr))
            except Exception as exc:
                result[attr] = f"<error: {type(exc).__name__}: {exc}>"

    return result


def compare_type_dict(
    diffs: DifferenceCollector,
    path: str,
    left_types: dict[str, Any],
    right_types: dict[str, Any],
    *,
    ignore_order: bool,
) -> None:
    left_keys = list(left_types.keys())
    right_keys = list(right_types.keys())

    compare_key_lists(
        diffs,
        path,
        left_keys,
        right_keys,
        ignore_order=ignore_order,
    )

    for name in sorted(set(left_keys) & set(right_keys)):
        if diffs.stopped:
            return

        left_sig = type_signature(left_types[name])
        right_sig = type_signature(right_types[name])

        if left_sig != right_sig:
            diffs.add(
                f"{path}/{name}",
                f"user-defined type differs:\n  original: {left_sig!r}\n  new:      {right_sig!r}",
            )


def compare_user_types(
    diffs: DifferenceCollector,
    path: str,
    left_group: Any,
    right_group: Any,
    *,
    ignore_order: bool,
) -> None:
    for attr_name in ["cmptypes", "vltypes", "enumtypes"]:
        left_types = getattr(left_group, attr_name, {})
        right_types = getattr(right_group, attr_name, {})

        compare_type_dict(
            diffs,
            f"{path}/{attr_name}",
            left_types,
            right_types,
            ignore_order=ignore_order,
        )


def compare_dimensions(
    diffs: DifferenceCollector,
    path: str,
    left_group: Any,
    right_group: Any,
    *,
    dim_map: dict[str, str],
    ignore_order: bool,
) -> None:
    left_dim_names_original = ordered_keys(left_group.dimensions)
    left_dim_names_mapped = [mapped_dim_name(name, dim_map) for name in left_dim_names_original]
    right_dim_names = ordered_keys(right_group.dimensions)

    compare_key_lists(
        diffs,
        f"{path}/dimensions",
        left_dim_names_mapped,
        right_dim_names,
        ignore_order=ignore_order,
    )

    for left_name in left_dim_names_original:
        if diffs.stopped:
            return

        right_name = mapped_dim_name(left_name, dim_map)

        if right_name not in right_group.dimensions:
            continue

        left_dim = left_group.dimensions[left_name]
        right_dim = right_group.dimensions[right_name]

        if len(left_dim) != len(right_dim):
            diffs.add(
                f"{path}/dimensions/{left_name}->{right_name}",
                f"length differs: {len(left_dim)} != {len(right_dim)}",
            )

        if left_dim.isunlimited() != right_dim.isunlimited():
            diffs.add(
                f"{path}/dimensions/{left_name}->{right_name}",
                f"unlimited status differs: {left_dim.isunlimited()} != {right_dim.isunlimited()}",
            )


def compare_variables(
    diffs: DifferenceCollector,
    path: str,
    left_group: Any,
    right_group: Any,
    *,
    dim_map: dict[str, str],
    ignore_order: bool,
    max_elements: int,
    bitwise: bool,
) -> None:
    left_var_names = ordered_keys(left_group.variables)
    right_var_names = ordered_keys(right_group.variables)

    compare_key_lists(
        diffs,
        f"{path}/variables",
        left_var_names,
        right_var_names,
        ignore_order=ignore_order,
    )

    for name in sorted(set(left_var_names) & set(right_var_names)):
        if diffs.stopped:
            return

        left_var = left_group.variables[name]
        right_var = right_group.variables[name]
        var_path = f"{path}/variables/{name}"

        left_dims_mapped = mapped_dim_tuple(left_var.dimensions, dim_map)

        if left_dims_mapped != right_var.dimensions:
            diffs.add(
                f"{var_path}/dimensions",
                f"variable dimensions differ: "
                f"{left_var.dimensions!r} mapped to {left_dims_mapped!r}, "
                f"new has {right_var.dimensions!r}",
            )

        if left_var.shape != right_var.shape:
            diffs.add(
                f"{var_path}/shape",
                f"shape differs: {left_var.shape!r} != {right_var.shape!r}",
            )

        left_dtype_sig = variable_datatype_signature(left_var)
        right_dtype_sig = variable_datatype_signature(right_var)

        if left_dtype_sig != right_dtype_sig:
            diffs.add(
                f"{var_path}/datatype",
                f"datatype differs:\n  original: {left_dtype_sig}\n  new:      {right_dtype_sig}",
            )

        compare_attrs(
            diffs,
            var_path,
            left_var,
            right_var,
            ignore_order=ignore_order,
        )

        compare_storage(
            diffs,
            f"{var_path}/storage",
            left_var,
            right_var,
        )

        compare_variable_data(
            diffs,
            var_path,
            left_var,
            right_var,
            max_elements=max_elements,
            bitwise=bitwise,
        )


def compare_groups(
    diffs: DifferenceCollector,
    path: str,
    left_group: Any,
    right_group: Any,
    *,
    dim_map: dict[str, str],
    ignore_order: bool,
    max_elements: int,
    bitwise: bool,
) -> None:
    if diffs.stopped:
        return

    compare_attrs(
        diffs,
        f"{path}/group",
        left_group,
        right_group,
        ignore_order=ignore_order,
    )

    compare_user_types(
        diffs,
        path,
        left_group,
        right_group,
        ignore_order=ignore_order,
    )

    compare_dimensions(
        diffs,
        path,
        left_group,
        right_group,
        dim_map=dim_map,
        ignore_order=ignore_order,
    )

    compare_variables(
        diffs,
        path,
        left_group,
        right_group,
        dim_map=dim_map,
        ignore_order=ignore_order,
        max_elements=max_elements,
        bitwise=bitwise,
    )

    left_group_names = ordered_keys(left_group.groups)
    right_group_names = ordered_keys(right_group.groups)

    compare_key_lists(
        diffs,
        f"{path}/groups",
        left_group_names,
        right_group_names,
        ignore_order=ignore_order,
    )

    for group_name in sorted(set(left_group_names) & set(right_group_names)):
        child_path = f"{path.rstrip('/')}/{group_name}"

        compare_groups(
            diffs,
            child_path,
            left_group.groups[group_name],
            right_group.groups[group_name],
            dim_map=dim_map,
            ignore_order=ignore_order,
            max_elements=max_elements,
            bitwise=bitwise,
        )


def assert_files_equivalent(
    original_path: Path,
    new_path: Path,
    *,
    dim_map: dict[str, str],
    ignore_order: bool,
    max_elements: int,
    max_errors: int,
    bitwise: bool,
) -> list[Difference]:
    diffs = DifferenceCollector(max_errors=max_errors)

    with Dataset(original_path, mode="r") as left, Dataset(new_path, mode="r") as right:
        disable_auto_decoding(left)
        disable_auto_decoding(right)

        if left.data_model != right.data_model:
            diffs.add(
                "/data_model",
                f"NetCDF data model differs: {left.data_model!r} != {right.data_model!r}",
            )

        compare_groups(
            diffs,
            "/",
            left,
            right,
            dim_map=dim_map,
            ignore_order=ignore_order,
            max_elements=max_elements,
            bitwise=bitwise,
        )

    return diffs.items


def main() -> int:
    parser = argparse.ArgumentParser(
        description=("Check that two NetCDF files are identical except for allowed dimension-name changes.")
    )

    parser.add_argument(
        "original",
        type=Path,
        help="Original NetCDF file.",
    )

    parser.add_argument(
        "new",
        type=Path,
        help="New NetCDF file to validate.",
    )

    parser.add_argument(
        "--map",
        dest="maps",
        action="append",
        default=[],
        metavar="OLD=NEW",
        help=("Allowed dimension rename. Can be passed multiple times. Default: lon=longitude and lat=latitude."),
    )

    parser.add_argument(
        "--ignore-order",
        action="store_true",
        help=(
            "Ignore ordering of dimensions, variables, attributes, groups, and user types. "
            "By default, order is checked strictly."
        ),
    )

    parser.add_argument(
        "--max-elements",
        type=int,
        default=5_000_000,
        help=("Maximum number of array elements to read per data chunk while comparing. Default: 5,000,000."),
    )

    parser.add_argument(
        "--max-errors",
        type=int,
        default=50,
        help="Stop after this many differences. Default: 50.",
    )

    parser.add_argument(
        "--bitwise-data",
        action="store_true",
        help=(
            "Compare numeric data chunks by raw in-memory bytes instead of value equality. "
            "This is stricter, but may fail for harmless NaN payload differences."
        ),
    )

    args = parser.parse_args()

    if not args.original.exists():
        print(f"Error: original file does not exist: {args.original}", file=sys.stderr)
        return 2

    if not args.new.exists():
        print(f"Error: new file does not exist: {args.new}", file=sys.stderr)
        return 2

    try:
        dim_map = parse_dim_map(args.maps) if args.maps else dict(DEFAULT_DIM_MAP)

        diffs = assert_files_equivalent(
            args.original,
            args.new,
            dim_map=dim_map,
            ignore_order=args.ignore_order,
            max_elements=args.max_elements,
            max_errors=args.max_errors,
            bitwise=args.bitwise_data,
        )

    except Exception as exc:
        print(f"Error while comparing files: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    if not diffs:
        print("OK: files are identical except for the allowed dimension rename(s).")
        return 0

    print("FAIL: files differ beyond the allowed dimension rename(s).", file=sys.stderr)
    print("", file=sys.stderr)

    for i, diff in enumerate(diffs, start=1):
        print(f"{i}. {diff.path}", file=sys.stderr)
        print(f"   {diff.message}", file=sys.stderr)

    if len(diffs) >= args.max_errors:
        print("", file=sys.stderr)
        print(f"Stopped after --max-errors={args.max_errors}.", file=sys.stderr)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
