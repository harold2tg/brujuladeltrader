"""Deterministic insight generator for reports.

Generates template-based insights without AI dependency.
Supports es/en languages.
"""

from typing import Any


class InsightGenerator:
    """Generates deterministic insights from trading metrics."""

    @staticmethod
    def monthly_insights(metrics: dict, language: str = "es") -> list[dict]:
        """Generate insights for a monthly report.

        Args:
            metrics: Global metrics from AnalyticsService
            language: 'es' or 'en'

        Returns:
            List of insight dicts with type, title, text, severity
        """
        insights = []
        win_rate = metrics.get("win_rate", 0)
        profit_factor = metrics.get("profit_factor")
        net_pnl = metrics.get("net_pnl", 0)
        total_trades = metrics.get("total_trades", 0)
        rr_ratio = metrics.get("rr_ratio")

        # Win rate insights
        if win_rate >= 0.6:
            insights.append(InsightGenerator._make_insight(
                "success",
                "win_rate_high",
                language,
                {"rate": f"{win_rate * 100:.1f}%"},
                "low"
            ))
        elif win_rate < 0.4:
            insights.append(InsightGenerator._make_insight(
                "warning",
                "win_rate_low",
                language,
                {"rate": f"{win_rate * 100:.1f}%"},
                "high"
            ))

        # Profit factor insights
        if profit_factor is not None:
            if profit_factor >= 2.0:
                insights.append(InsightGenerator._make_insight(
                    "success",
                    "profit_factor_strong",
                    language,
                    {"factor": f"{profit_factor:.2f}"},
                    "low"
                ))
            elif profit_factor < 1.0:
                insights.append(InsightGenerator._make_insight(
                    "critical",
                    "profit_factor_negative",
                    language,
                    {"factor": f"{profit_factor:.2f}"},
                    "high"
                ))

        # PnL insights
        if net_pnl > 0:
            insights.append(InsightGenerator._make_insight(
                "success",
                "profitable_month",
                language,
                {"amount": f"${net_pnl:,.2f}"},
                "low"
            ))
        elif net_pnl < 0:
            insights.append(InsightGenerator._make_insight(
                "warning",
                "losing_month",
                language,
                {"amount": f"${abs(net_pnl):,.2f}"},
                "medium"
            ))

        # R:R ratio insights
        if rr_ratio is not None and rr_ratio > 0:
            if rr_ratio >= 2.0:
                insights.append(InsightGenerator._make_insight(
                    "success",
                    "rr_excellent",
                    language,
                    {"ratio": f"{rr_ratio:.2f}"},
                    "low"
                ))
            elif rr_ratio < 1.0:
                insights.append(InsightGenerator._make_insight(
                    "warning",
                    "rr_below_one",
                    language,
                    {"ratio": f"{rr_ratio:.2f}"},
                    "medium"
                ))

        # Trade volume insight
        if total_trades < 10:
            insights.append(InsightGenerator._make_insight(
                "info",
                "low_volume",
                language,
                {"count": str(total_trades)},
                "low"
            ))

        return insights

    @staticmethod
    def annual_insights(metrics: dict, language: str = "es") -> list[dict]:
        """Generate insights for an annual report.

        Args:
            metrics: Aggregated annual metrics
            language: 'es' or 'en'

        Returns:
            List of insight dicts
        """
        insights = []
        win_rate = metrics.get("win_rate", 0)
        total_return_pct = metrics.get("total_return_pct", 0)
        profit_factor = metrics.get("profit_factor")

        # Annual performance
        if total_return_pct > 0:
            insights.append(InsightGenerator._make_insight(
                "success",
                "annual_profit",
                language,
                {"return": f"{total_return_pct:.1f}%"},
                "low"
            ))
        elif total_return_pct < -10:
            insights.append(InsightGenerator._make_insight(
                "critical",
                "annual_loss_major",
                language,
                {"return": f"{total_return_pct:.1f}%"},
                "high"
            ))
        elif total_return_pct < 0:
            insights.append(InsightGenerator._make_insight(
                "warning",
                "annual_loss",
                language,
                {"return": f"{total_return_pct:.1f}%"},
                "medium"
            ))

        # Consistency
        if win_rate >= 0.55:
            insights.append(InsightGenerator._make_insight(
                "success",
                "consistent_trader",
                language,
                {"rate": f"{win_rate * 100:.1f}%"},
                "low"
            ))

        # Profit factor
        if profit_factor is not None and profit_factor >= 2.0:
            insights.append(InsightGenerator._make_insight(
                "success",
                "strong_edge",
                language,
                {"factor": f"{profit_factor:.2f}"},
                "low"
            ))

        return insights

    @staticmethod
    def _make_insight(
        insight_type: str,
        rule: str,
        language: str,
        vars_dict: dict[str, Any],
        severity: str
    ) -> dict:
        """Create an insight from a rule template."""
        templates = InsightGenerator._get_templates(language)
        template = templates.get(rule, {"title": rule, "text": rule})

        title = template["title"]
        text = template["text"]

        # Replace variables
        for key, value in vars_dict.items():
            title = title.replace(f"{{{key}}}", value)
            text = text.replace(f"{{{key}}}", value)

        return {
            "type": insight_type,
            "title": title,
            "text": text,
            "severity": severity
        }

    @staticmethod
    def _get_templates(language: str) -> dict:
        """Get insight templates for the specified language."""
        if language == "es":
            return {
                "win_rate_high": {
                    "title": "Win Rate Sólido",
                    "text": "Tu win rate de {rate} está por encima del promedio. Mantén la disciplina."
                },
                "win_rate_low": {
                    "title": "Win Rate Bajo",
                    "text": "Tu win rate de {rate} está por debajo del 40%. Revisa tu selección de entradas."
                },
                "profit_factor_strong": {
                    "title": "Profit Factor Fuerte",
                    "text": "Un profit factor de {factor} indica una ventaja clara en el mercado."
                },
                "profit_factor_negative": {
                    "title": "Profit Factor Negativo",
                    "text": "Un profit factor de {factor} significa que estás perdiendo más de lo que ganas."
                },
                "profitable_month": {
                    "title": "Mes Rentable",
                    "text": "Ganaste {amount} este mes. Buen trabajo."
                },
                "losing_month": {
                    "title": "Mes con Pérdidas",
                    "text": "Perdiste {amount} este mes. Analiza qué salió mal."
                },
                "rr_excellent": {
                    "title": "Ratio R:R Excelente",
                    "text": "Tu ratio R:R de {ratio} es excelente. Sigue así."
                },
                "rr_below_one": {
                    "title": "Ratio R:R Bajo",
                    "text": "Tu ratio R:R de {ratio} es menor a 1. Tus pérdidas promedio son mayores que tus ganancias."
                },
                "low_volume": {
                    "title": "Volumen Bajo",
                    "text": "Solo tienes {count} trades este mes. Necesitas más datos para un análisis confiable."
                },
                "annual_profit": {
                    "title": "Año Rentable",
                    "text": "Obtuviste un retorno de {return} este año."
                },
                "annual_loss_major": {
                    "title": "Año con Pérdidas Significativas",
                    "text": "Perdiste {return} este año. Es momento de revisar tu estrategia."
                },
                "annual_loss": {
                    "title": "Año con Pérdidas",
                    "text": "Tuviste un retorno de {return} este año."
                },
                "consistent_trader": {
                    "title": "Trader Consistente",
                    "text": "Un win rate de {rate} anual muestra consistencia."
                },
                "strong_edge": {
                    "title": "Ventaja Sólida",
                    "text": "Un profit factor de {factor} anual confirma tu ventaja en el mercado."
                }
            }
        else:  # English
            return {
                "win_rate_high": {
                    "title": "Solid Win Rate",
                    "text": "Your win rate of {rate} is above average. Keep the discipline."
                },
                "win_rate_low": {
                    "title": "Low Win Rate",
                    "text": "Your win rate of {rate} is below 40%. Review your entry selection."
                },
                "profit_factor_strong": {
                    "title": "Strong Profit Factor",
                    "text": "A profit factor of {factor} indicates a clear edge in the market."
                },
                "profit_factor_negative": {
                    "title": "Negative Profit Factor",
                    "text": "A profit factor of {factor} means you're losing more than you're winning."
                },
                "profitable_month": {
                    "title": "Profitable Month",
                    "text": "You earned {amount} this month. Good job."
                },
                "losing_month": {
                    "title": "Losing Month",
                    "text": "You lost {amount} this month. Analyze what went wrong."
                },
                "rr_excellent": {
                    "title": "Excellent R:R Ratio",
                    "text": "Your R:R ratio of {ratio} is excellent. Keep it up."
                },
                "rr_below_one": {
                    "title": "Low R:R Ratio",
                    "text": "Your R:R ratio of {ratio} is below 1. Your average losses exceed your average wins."
                },
                "low_volume": {
                    "title": "Low Volume",
                    "text": "Only {count} trades this month. You need more data for reliable analysis."
                },
                "annual_profit": {
                    "title": "Profitable Year",
                    "text": "You achieved a {return} return this year."
                },
                "annual_loss_major": {
                    "title": "Major Annual Loss",
                    "text": "You lost {return} this year. It's time to review your strategy."
                },
                "annual_loss": {
                    "title": "Losing Year",
                    "text": "You had a {return} return this year."
                },
                "consistent_trader": {
                    "title": "Consistent Trader",
                    "text": "A {rate} annual win rate shows consistency."
                },
                "strong_edge": {
                    "title": "Strong Edge",
                    "text": "A {factor} annual profit factor confirms your market edge."
                }
            }
