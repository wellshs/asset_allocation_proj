"""Command-line interface for account operations."""

import argparse
import sys
from pathlib import Path

from src.account.service import AccountService
from src.account.exceptions import AccountException


def display_holdings(holdings, show_details=True):
    """
    Display holdings in formatted output.

    Args:
        holdings: AccountHoldings to display
        show_details: Whether to show detailed position info
    """
    print(f"\n{'='*60}")
    print(f"Account: {holdings.account_id}")
    print(f"Timestamp: {holdings.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    # Show currency breakdown if available
    if holdings.krw_cash_balance is not None and holdings.usd_cash_balance is not None:
        print(f"Cash Balance (KRW): ₩{int(holdings.krw_cash_balance):,}")
        if holdings.usd_cash_balance > 0:
            usd_in_krw = holdings.usd_cash_balance * (holdings.exchange_rate or 0)
            print(
                f"Cash Balance (USD): ${float(holdings.usd_cash_balance):,.2f} (₩{int(usd_in_krw):,} @ ₩{float(holdings.exchange_rate):,.2f})"
            )
        print(f"Total Cash:         ₩{int(holdings.cash_balance):,}")
    else:
        print(f"Cash Balance:       ₩{int(holdings.cash_balance):,}")

    print(f"Total Value:        ₩{int(holdings.total_value):,}")
    print(f"Holdings:           {len(holdings.positions)} securities")
    print(f"{'='*60}")

    if show_details and holdings.positions:
        print("\nHoldings Details:")
        for pos in holdings.positions:
            warning = " ⚠️" if pos.has_warning else ""
            print(f"\n  • {pos.name} ({pos.symbol}){warning}")
            print(f"    Quantity: {pos.quantity} shares")
            print(f"    Current Price: ₩{pos.current_price:,}")
            print(f"    Value: ₩{pos.current_value:,}")
            if pos.profit_loss:
                pl_sign = "+" if pos.profit_loss > 0 else ""
                print(f"    P/L: {pl_sign}₩{pos.profit_loss:,}")


def cmd_fetch(args):
    """Fetch holdings for an account."""
    config_path = args.config or "config/config.yaml"

    if not Path(config_path).exists():
        print(f"Error: Configuration file not found: {config_path}")
        return 1

    try:
        service = AccountService(config_path)

        if args.mock:
            print("Using mock data...")
            from tests.fixtures.mock_portfolios import (
                create_mock_holdings_with_positions,
            )

            holdings = create_mock_holdings_with_positions()
            display_holdings(holdings)
        elif args.all:
            all_holdings = service.get_all_holdings()
            if args.consolidated:
                consolidated = service.consolidate_holdings(all_holdings)
                display_holdings(consolidated)
            else:
                for name, holdings in all_holdings.items():
                    display_holdings(holdings)
        else:
            if not args.account:
                print("Error: --account is required unless --all is used")
                return 1
            holdings = service.get_holdings(args.account)
            display_holdings(holdings)

        return 0

    except AccountException as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


def cmd_status(args):
    """Show account status."""
    config_path = args.config or "config/config.yaml"

    if not Path(config_path).exists():
        print(f"Error: Configuration file not found: {config_path}")
        return 1

    try:
        from src.account.config import load_config

        config = load_config(config_path)

        print(f"\n{'='*60}")
        print("Account Configuration Status")
        print(f"{'='*60}")

        for account in config.accounts:
            status = "✓ Enabled" if account.enabled else "✗ Disabled"
            print(f"\n{account.name}")
            print(f"  Provider: {account.provider}")
            print(f"  Status: {status}")

        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Account Integration CLI")
    parser.add_argument("--config", "-c", help="Path to configuration file")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Fetch command
    fetch_parser = subparsers.add_parser("fetch", help="Fetch account holdings")
    fetch_parser.add_argument("--account", "-a", help="Account name")
    fetch_parser.add_argument("--all", action="store_true", help="Fetch all accounts")
    fetch_parser.add_argument(
        "--consolidated", action="store_true", help="Show consolidated view"
    )
    fetch_parser.add_argument("--mock", action="store_true", help="Use mock data")
    fetch_parser.set_defaults(func=cmd_fetch)

    # Status command
    status_parser = subparsers.add_parser("status", help="Show account status")
    status_parser.set_defaults(func=cmd_status)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
