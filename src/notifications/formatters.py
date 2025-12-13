"""Message formatting for notifications."""

from src.account.models import AccountHoldings


class PortfolioFormatter:
    """Format portfolio holdings for notifications."""

    @staticmethod
    def format_detailed(holdings: AccountHoldings) -> dict:
        """
        Format holdings with full details (Block Kit).

        Args:
            holdings: Holdings to format

        Returns:
            dict: Slack message payload
        """
        blocks = []

        # Header
        blocks.append(
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📊 Portfolio Update: {holdings.account_id}",
                },
            }
        )

        # Summary with currency breakdown
        fields = [
            {
                "type": "mrkdwn",
                "text": f"*Total Value:*\n₩{int(holdings.total_value):,}",
            },
        ]

        # Cash balance with USD/KRW breakdown
        if (
            holdings.krw_cash_balance is not None
            and holdings.usd_cash_balance is not None
        ):
            cash_text = "*Cash Balance:*\n"
            cash_text += f"KRW: ₩{int(holdings.krw_cash_balance):,}\n"
            if holdings.usd_cash_balance > 0:
                usd_in_krw = holdings.usd_cash_balance * (holdings.exchange_rate or 0)
                cash_text += f"USD: ${float(holdings.usd_cash_balance):,.2f} (₩{int(usd_in_krw):,})\n"
            cash_text += f"Total: ₩{int(holdings.cash_balance):,}"
            fields.append({"type": "mrkdwn", "text": cash_text})
        else:
            fields.append(
                {
                    "type": "mrkdwn",
                    "text": f"*Cash Balance:*\n₩{int(holdings.cash_balance):,}",
                }
            )

        fields.append(
            {
                "type": "mrkdwn",
                "text": f"*Holdings:*\n{len(holdings.positions)} securities",
            }
        )

        blocks.append({"type": "section", "fields": fields})

        # Divider
        blocks.append({"type": "divider"})

        # Holdings detail
        if holdings.positions:
            blocks.append(
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "*Holdings Details:*"},
                }
            )

            for pos in holdings.positions[:10]:  # Limit to top 10
                warning = " ⚠️" if pos.has_warning else ""
                text = f"• *{pos.name}* ({pos.symbol}){warning}\n"
                text += f"  {pos.quantity} shares @ ₩{pos.current_price:,} = ₩{pos.current_value:,}"

                if pos.profit_loss:
                    pl_sign = "+" if pos.profit_loss > 0 else ""
                    text += f"\n  P/L: {pl_sign}₩{pos.profit_loss:,}"

                blocks.append(
                    {"type": "section", "text": {"type": "mrkdwn", "text": text}}
                )

            if len(holdings.positions) > 10:
                blocks.append(
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"_...and {len(holdings.positions) - 10} more holdings_",
                            }
                        ],
                    }
                )

        # Footer
        blocks.append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"🕒 Updated: {holdings.timestamp.strftime('%Y-%m-%d %H:%M:%S KST')}",
                    }
                ],
            }
        )

        return {"text": f"Portfolio Update: {holdings.account_id}", "blocks": blocks}

    @staticmethod
    def format_summary(holdings: AccountHoldings) -> dict:
        """
        Format holdings summary (top 10 only).

        Args:
            holdings: Holdings to format

        Returns:
            dict: Slack message payload
        """
        blocks = []

        # Header
        blocks.append(
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"📊 {holdings.account_id}"},
            }
        )

        # Summary with currency breakdown
        text = f"*Total:* ₩{int(holdings.total_value):,}\n"

        # Cash with USD/KRW breakdown
        if (
            holdings.krw_cash_balance is not None
            and holdings.usd_cash_balance is not None
        ):
            text += f"*Cash:* ₩{int(holdings.cash_balance):,}\n"
            if holdings.usd_cash_balance > 0:
                text += f"  - KRW: ₩{int(holdings.krw_cash_balance):,}\n"
                text += f"  - USD: ${float(holdings.usd_cash_balance):,.2f}\n"
        else:
            text += f"*Cash:* ₩{int(holdings.cash_balance):,}\n"

        text += f"*Holdings:* {len(holdings.positions)} securities"

        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": text}})

        # Top 10 holdings
        if holdings.positions:
            top_10 = holdings.positions[:10]
            holdings_text = "\n".join(
                [f"• {p.name}: ₩{p.current_value:,}" for p in top_10]
            )

            if len(holdings.positions) > 10:
                holdings_text += f"\n_...and {len(holdings.positions) - 10} more_"

            blocks.append(
                {"type": "section", "text": {"type": "mrkdwn", "text": holdings_text}}
            )

        return {"text": f"Portfolio: {holdings.account_id}", "blocks": blocks}
