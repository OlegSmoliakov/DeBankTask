from dataclasses import dataclass

import pandas as pd


@dataclass(slots=True)
class UserProtocolList:
    data: pd.DataFrame
    timestamp: int


def parse_token(token: dict):
    """Parses token data."""
    token_total_price = token["price"] * token["amount"]

    record = {
        "token_name": token["name"],
        "token_symbol": token["symbol"],
        "chain": token["chain"],
        "quantity": token["amount"],
        "price_usd": token["price"],
        "total_value_usd": token_total_price,
    }

    return record


def get_token_lists(portfolio_item: dict):
    """Returns the token lists and unlock_at date for the given portfolio item."""

    detail: dict[str, dict] = portfolio_item["detail"]
    detail_type = portfolio_item["detail_types"][0]
    unlock_at = 0

    match detail_type:
        case "common" | "lending" | "locked":
            token_lists = {k: v for k, v in detail.items() if k.endswith("_token_list")}
            unlock_at = detail.get("unlock_at", 0)
        case "vesting":
            token_lists = {"supply_token_list": [detail["token"]]}
            unlock_at = detail.get("end_at", 0)
        case _:
            msg = f"Unknown detail type: {detail_type}"
            raise ValueError(msg)

    return token_lists, unlock_at


def parse_portfolio_item(portfolio_item: dict):
    """Parses the portfolio item data and return list of tokens."""

    if all(v == 0 for v in portfolio_item["stats"].values()):
        return []

    token_lists, unlock_at = get_token_lists(portfolio_item)

    tokens = []

    for token_list_name, token_list in token_lists.items():
        token_type = token_list_name.replace("_token_list", "")

        for token in token_list:
            if token := parse_token(token):
                token["token_type"] = token_type
                token["unlock_at"] = unlock_at
                tokens.append(token)

    return tokens


def parse_protocol(protocol: dict):
    """Parses the protocol data and return list of tokens."""

    parsed_protocol = []

    for portfolio_item in protocol["portfolio_item_list"]:
        position_type = portfolio_item["name"]

        portfolio_tokens = parse_portfolio_item(portfolio_item)

        for token in portfolio_tokens:
            token["position_type"] = position_type

        parsed_protocol.extend(portfolio_tokens)

    return parsed_protocol


def parse_protocol_list(data: list[dict]):
    """
    Parses user complex protocol list on all supported chains. From DeBank API.

    Returns:
        pd.DataFrame:

        With columns:
            token_name: str
            token_symbol: str
            protocol_name: str
            chain: str
            position_type: str (e.g. "lending", "locked", "vesting")
            token_type: str (e.g. "supply", "borrow", "reward")
            quantity: float
            price_usd: float
            total_value_usd: float
            unlock_at: int (timestamp)
    """

    parsed_assets = []

    for protocol in data:
        protocol_name = protocol["name"]

        parsed_protocol = parse_protocol(protocol)

        for token in parsed_protocol:
            token["protocol_name"] = protocol_name

        parsed_assets.extend(parsed_protocol)

    parsed_assets = pd.DataFrame(parsed_assets)
    desired_order = [
        "token_name",
        "token_symbol",
        "protocol_name",
        "chain",
        "position_type",
        "token_type",
        "quantity",
        "price_usd",
        "total_value_usd",
        "unlock_at",
    ]
    parsed_assets = parsed_assets[desired_order]

    return parsed_assets


def aggregate_parsed_protocols(data: pd.DataFrame):
    """
    Aggregates and clean parsed protocol list.

    Combine token's with the same pools and position type, remove zero total value tokens.
    """

    data = data[data["total_value_usd"] != 0]

    columns_to_consider = [
        "token_name",
        "token_symbol",
        "protocol_name",
        "chain",
        "position_type",
        "token_type",
        "unlock_at",
    ]
    non_duplicates = data.drop_duplicates(subset=columns_to_consider, keep=False)

    duplicates = data[data.duplicated(subset=columns_to_consider, keep=False)]
    aggregated_duplicates = duplicates.groupby(columns_to_consider, as_index=False).agg(
        {
            "quantity": "sum",
            "price_usd": "first",
            "total_value_usd": "sum",
        }
    )

    combined = pd.concat([non_duplicates, aggregated_duplicates], ignore_index=True)

    return combined


def get_protocols_total_balance(data: pd.DataFrame):
    """
    Format user portfolio to readable format.

    Returns:
        pd.DataFrame:

        With columns:
            Reward Balance: float
            Debt Balance: float
            Collateral Balance: float
            Net Balance: float
            Total Balance USD: float
    """

    data["Protocol (chain)"] = data["protocol_name"] + " (" + data["chain"] + ")"
    grouped = data.groupby("Protocol (chain)")

    reward_balance = grouped.apply(
        lambda x: x[x["token_type"] == "reward"]["total_value_usd"].sum()
    )
    debt_balance = grouped.apply(lambda x: x[x["token_type"] == "borrow"]["total_value_usd"].sum())
    collateral_balance = grouped.apply(
        lambda x: x[x["token_type"] == "supply"]["total_value_usd"].sum()
    )

    net_balance = collateral_balance - debt_balance
    total_balance = net_balance + reward_balance

    result = pd.DataFrame(
        {
            "Reward Balance": reward_balance,
            "Debt Balance": debt_balance,
            "Collateral Balance": collateral_balance,
            "Net Balance": net_balance,
            "Total Balance USD": total_balance,
        }
    )

    return result
