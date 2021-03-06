#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# System libraries
import pandas as pd

# Configurations
DESCENDING_KEY = "returnOnInvestedCapital"
ASCENDING_KEY = "priceToEarnings"


class Strategy:

    def __init__(self):
        pass

    def get_indicators(self, fundamentals, quotations):
        fundamentals, quotations = self._strategy_preprocess(fundamentals, quotations)
        volumes = self._get_volumes(quotations)
        self._update_fundamentals(fundamentals, volumes)
        rank = self._get_rank(fundamentals)
        trends = self._get_trends(rank.index, quotations)
        market_indicator = self._get_market_indicator(quotations)
        indicators = self._to_list(rank, trends, market_indicator)
        return indicators

    @staticmethod
    def _strategy_preprocess(fundamentals, quotations):
        fundamentals = pd.DataFrame(fundamentals)
        fundamentals = fundamentals.set_index("ticker")
        quotations = pd.DataFrame(quotations)
        return fundamentals, quotations

    @staticmethod
    def _get_volumes(quotations):
        volumes = quotations.groupby("ticker")["volume"].rolling(window=40).mean()
        return volumes

    @staticmethod
    def _update_fundamentals(fundamentals, volumes):
        for ticker in set(fundamentals.index):
            volume = 0
            if ticker in volumes:
                volume = volumes[ticker].iloc[-1]
            fundamentals.loc[ticker, "volume"] = volume
        return fundamentals

    def _get_rank(self, fundamentals):
        new_descending_key = f"{DESCENDING_KEY}_rank"
        new_ascending_key = f"{ASCENDING_KEY}_rank"
        rank_list = range(fundamentals.shape[0])

        # Compute rates
        fundamentals = fundamentals.sort_values(DESCENDING_KEY, ascending=False)
        fundamentals[new_descending_key] = rank_list
        fundamentals = fundamentals.sort_values(ASCENDING_KEY)
        fundamentals[new_ascending_key] = rank_list
        fundamentals["rate"] = \
            fundamentals[new_descending_key] + fundamentals[new_ascending_key]

        # Compute ranks
        self._filter(fundamentals)
        fundamentals = fundamentals.sort_values("rate")
        fundamentals["rank"] = rank_list

        return fundamentals["rank"].to_frame()

    @staticmethod
    def _filter(fundamentals):
        maximum_rate = max(fundamentals["rate"])
        fundamentals["rate"] = fundamentals["rate"].where(
            (fundamentals["cagr"] > 0.05) &
            (fundamentals[DESCENDING_KEY] > 0) &
            (fundamentals[ASCENDING_KEY] > 0) &
            (fundamentals["volume"] > 100000),
            fundamentals["rate"] + maximum_rate + 1)

    @staticmethod
    def _get_trends(tickers, quotations):
        WINDOW = 34
        trends = pd.Series(name="trend")
        for ticker in tickers:
            ticker_close = quotations["close"][quotations["ticker"] == ticker]
            if not ticker_close.empty:
                mean = ticker_close.ewm(span=WINDOW, min_periods=WINDOW).mean()
                difference = mean - mean.shift(1)
                new_trend = difference.where(difference >= 0, -1)
                new_trend = new_trend.where(difference < 0, 1)
                trends[ticker] = new_trend.iloc[-1]
        return trends

    @staticmethod
    def _get_market_indicator(quotations):
        MARKET_TICKER = "IBOV"
        WINDOW = 89
        market_quotation = quotations[quotations["ticker"] == MARKET_TICKER]
        market_mean = market_quotation["close"].ewm(span=WINDOW, min_periods=WINDOW).mean()
        difference = market_mean - market_mean.shift(1)
        trend = difference.where(difference < 0, 1)
        trend = trend.where(trend >= 0, -1)
        market_trend = trend.iloc[-1]
        market_indicator = {"ticker": MARKET_TICKER, "rank": None, "trend": market_trend}
        return market_indicator

    @staticmethod
    def _to_list(rank, trends, market_indicator):
        indicators = rank.copy()
        indicators["trend"] = trends
        indicators.index.name = "ticker"
        indicators = indicators.reset_index().to_dict(orient="records")
        indicators = indicators + [market_indicator]
        return indicators
