import pytest

from rotkehlchen.accounting.ledger_actions import LedgerAction, LedgerActionType
from rotkehlchen.accounting.mixins.event import AccountingEventType
from rotkehlchen.accounting.pnl import PNL, PnlTotals
from rotkehlchen.constants import ONE, ZERO
from rotkehlchen.constants.assets import A_ETH, A_EUR, A_KFEE, A_USDT
from rotkehlchen.exchanges.data_structures import Trade
from rotkehlchen.fval import FVal
from rotkehlchen.tests.utils.accounting import accounting_history_process, check_pnls_and_csv
from rotkehlchen.tests.utils.history import prices
from rotkehlchen.tests.utils.messages import no_message_errors
from rotkehlchen.types import Location, Timestamp, TradeType


@pytest.mark.parametrize('mocked_price_queries', [prices])
@pytest.mark.parametrize('dont_mock_price_for', [[A_KFEE]])
def test_kfee_price_in_accounting(accountant, google_service):
    """
    Test that KFEEs are correctly handled during accounting

    KFEE price is fixed at $0.01
    """
    history = [
        LedgerAction(
            identifier=0,
            timestamp=Timestamp(1539713238),  # 178.615 EUR/ETH
            action_type=LedgerActionType.INCOME,
            location=Location.KRAKEN,
            amount=ONE,
            asset=A_ETH,
            rate=None,
            rate_asset=None,
            link=None,
            notes='',
        ), LedgerAction(
            identifier=0,
            timestamp=Timestamp(1539713238),  # 0.8612 USD/EUR. 1 KFEE = $0.01 so 8.612 EUR
            action_type=LedgerActionType.INCOME,
            location=Location.KRAKEN,
            amount=FVal(1000),
            asset=A_KFEE,
            rate=None,
            rate_asset=None,
            link=None,
            notes='',
        ), Trade(
            timestamp=1609537953,
            location=Location.KRAKEN,  # 0.89 USDT/EUR -> PNL: 20 * 0.89 - 0.02*178.615 ->  14.2277
            base_asset=A_ETH,
            quote_asset=A_USDT,
            trade_type=TradeType.SELL,
            amount=FVal('0.02'),
            rate=FVal(1000),
            fee=FVal(30),  # KFEE should not be taken into account
            fee_currency=A_KFEE,
            link=None,
        ),
    ]
    accounting_history_process(
        accountant,
        start_ts=1539713238,
        end_ts=1624395187,
        history_list=history,
    )
    no_message_errors(accountant.msg_aggregator)
    expected_pnls = PnlTotals({
        AccountingEventType.TRADE: PNL(taxable=ZERO, free=FVal('14.2277')),
        AccountingEventType.LEDGER_ACTION: PNL(taxable=FVal('187.227'), free=ZERO),
    })
    check_pnls_and_csv(accountant, expected_pnls, google_service)


@pytest.mark.parametrize('mocked_price_queries', [prices])
def test_fees_count_in_cost_basis(accountant, google_service):
    """Make sure that asset amounts used in fees are reduced."""
    history = [
        Trade(
            timestamp=1609537953,
            location=Location.KRAKEN,
            base_asset=A_ETH,
            quote_asset=A_EUR,
            trade_type=TradeType.BUY,
            amount=ONE,
            rate=FVal('598.26'),
            fee=ONE,
            fee_currency=A_EUR,
            link=None,
        ), Trade(
            # PNL: 0.5 * 1862.06 - 0.5 * 599.26 -> 631.4
            # fee: -0.5 * 1862.06 + 0.5 * 1862.06 - 0.5 * 599.26 -> -299.63
            timestamp=1624395186,
            location=Location.KRAKEN,
            base_asset=A_ETH,
            quote_asset=A_EUR,
            trade_type=TradeType.SELL,
            amount=FVal('0.5'),
            rate=FVal('1862.06'),
            fee=FVal('0.5'),
            fee_currency=A_ETH,
            link=None,
        ), Trade(
            timestamp=1625001464,
            location=Location.KRAKEN,
            base_asset=A_ETH,
            quote_asset=A_EUR,
            trade_type=TradeType.SELL,
            amount=FVal('0.5'),
            rate=FVal('1837.31'),
            fee=None,
            fee_currency=None,
            link=None,
        ),
    ]
    accounting_history_process(
        accountant=accountant,
        start_ts=1436979735,
        end_ts=1625001466,
        history_list=history,
    )

    expected_pnls = PnlTotals({
        AccountingEventType.TRADE: PNL(taxable=FVal('1550.055'), free=ZERO),
        AccountingEventType.FEE: PNL(taxable=FVal('-300.630'), free=ZERO),
    })
    assert accountant.pots[0].cost_basis.get_calculated_asset_amount(A_ETH) is None
    warnings = accountant.msg_aggregator.consume_warnings()
    assert len(warnings) == 0
    check_pnls_and_csv(accountant, expected_pnls, google_service)


@pytest.mark.parametrize('mocked_price_queries', [prices])
def test_fees_in_received_asset(accountant, google_service):
    """
    Test the sell trade where the fee is nominated in the asset received. We had a bug
    where the PnL report said that there was no documented acquisition.
    """
    history = [
        LedgerAction(
            identifier=0,
            timestamp=Timestamp(1539713238),  # 178.615 EUR/ETH
            action_type=LedgerActionType.INCOME,
            location=Location.BINANCE,
            amount=ONE,
            asset=A_ETH,
            rate=None,
            rate_asset=None,
            link=None,
            notes='',
        ),
        Trade(
            # Sell 0.02 ETH for USDT with rate 1000 USDT/ETH and 0.10 USDT fee
            # So acquired 20 USDT for 0.02 ETH + 0.10 USDT
            # So acquired 20 USDT for 0.02 * 598.26 + 0.10 * 0.89 -> 12.0542 EUR
            # So paid 12.0542/20 -> 0.60271 EUR/USDT
            timestamp=1609537953,  # 0.89 EUR/USDT
            location=Location.BINANCE,
            base_asset=A_ETH,  # 598.26 EUR/ETH
            quote_asset=A_USDT,
            trade_type=TradeType.SELL,
            amount=FVal('0.02'),
            rate=FVal(1000),
            fee=FVal('0.10'),
            fee_currency=A_USDT,
            link=None,
        ),
    ]

    accounting_history_process(
        accountant,
        start_ts=1539713238,
        end_ts=1624395187,
        history_list=history,
    )
    no_message_errors(accountant.msg_aggregator)
    assert accountant.pots[0].cost_basis.get_calculated_asset_amount(A_USDT.identifier).is_close('19.90')  # noqa: E501
    expected_pnls = PnlTotals({
        AccountingEventType.TRADE: PNL(taxable=ZERO, free=FVal('14.2277')),
        AccountingEventType.FEE: PNL(taxable=FVal('-0.060271'), free=ZERO),
        AccountingEventType.LEDGER_ACTION: PNL(taxable=FVal('178.615'), free=ZERO),
    })
    check_pnls_and_csv(accountant, expected_pnls, google_service)
