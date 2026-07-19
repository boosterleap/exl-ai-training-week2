"""Read-only inventory MCP server backed by the canonical Week2 fixture."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field


class InventoryItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sku: str
    name: str
    qty_on_hand: int = Field(ge=0)
    reorder_point: int = Field(ge=0)
    location: str


class InventorySnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    warehouse: str
    updated_at: str
    items: list[InventoryItem]


class StockEvidence(BaseModel):
    source: str
    warehouse: str
    updated_at: str
    item: InventoryItem
    stock_status: Literal["at_or_below_reorder", "above_reorder"]


class LowStockEvidence(BaseModel):
    source: str
    warehouse: str
    updated_at: str
    count: int
    items: list[InventoryItem]


def discover_week2_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "requirements.txt").is_file() and (parent / "data").is_dir():
            return parent
    raise RuntimeError("Could not discover Week2 root from inventory_server.py.")


WEEK2_ROOT = discover_week2_root()
INVENTORY_PATH = WEEK2_ROOT / "data" / "supply" / "inventory.json"
SOURCE_LABEL = "data/supply/inventory.json"
load_dotenv(WEEK2_ROOT / ".env")

mcp = FastMCP(
    "canonical-inventory",
    instructions=(
        "Read-only inventory lookup. Results come only from the canonical "
        "Week2 inventory fixture; no stock mutations are exposed."
    ),
    host=os.getenv("INVENTORY_MCP_HOST", "127.0.0.1"),
    port=int(os.getenv("INVENTORY_MCP_PORT", "8765")),
    streamable_http_path="/mcp",
    json_response=True,
    stateless_http=True,
)


def load_inventory() -> InventorySnapshot:
    if not INVENTORY_PATH.is_file():
        raise FileNotFoundError(f"Canonical inventory is missing: {INVENTORY_PATH}")
    try:
        payload = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
        return InventorySnapshot.model_validate(payload)
    except (json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError(f"Canonical inventory is invalid: {exc}") from exc


@mcp.tool()
def get_stock(sku: str) -> StockEvidence:
    """Get canonical stock evidence for one exact SKU; this never writes data."""
    normalized = sku.strip().upper()
    if not normalized:
        raise ValueError("sku must be a non-empty exact SKU.")
    snapshot = load_inventory()
    item = next((row for row in snapshot.items if row.sku == normalized), None)
    if item is None:
        raise ValueError(f"SKU {normalized!r} is absent from canonical inventory.")
    status = (
        "at_or_below_reorder"
        if item.qty_on_hand <= item.reorder_point
        else "above_reorder"
    )
    return StockEvidence(
        source=SOURCE_LABEL,
        warehouse=snapshot.warehouse,
        updated_at=snapshot.updated_at,
        item=item,
        stock_status=status,
    )


@mcp.tool()
def list_low_stock() -> LowStockEvidence:
    """List canonical items at or below reorder point; this never writes data."""
    snapshot = load_inventory()
    items = [
        item
        for item in snapshot.items
        if item.qty_on_hand <= item.reorder_point
    ]
    return LowStockEvidence(
        source=SOURCE_LABEL,
        warehouse=snapshot.warehouse,
        updated_at=snapshot.updated_at,
        count=len(items),
        items=items,
    )


@mcp.resource(
    "inventory://canonical/snapshot",
    name="Canonical inventory snapshot",
    description="The complete read-only canonical inventory JSON document.",
    mime_type="application/json",
)
def inventory_snapshot_resource() -> str:
    """Return the validated canonical inventory snapshot as JSON."""
    return load_inventory().model_dump_json(indent=2)


def self_check() -> dict[str, object]:
    snapshot = load_inventory()
    return {
        "ok": True,
        "server": "canonical-inventory",
        "transport": "streamable-http",
        "endpoint": (
            f"http://{os.getenv('INVENTORY_MCP_HOST', '127.0.0.1')}:"
            f"{os.getenv('INVENTORY_MCP_PORT', '8765')}/mcp"
        ),
        "source": SOURCE_LABEL,
        "item_count": len(snapshot.items),
        "tools": ["get_stock", "list_low_stock"],
        "resources": ["inventory://canonical/snapshot"],
        "write_tools": [],
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
