# backend/verticals/analyst/agent.py
"""
Data Analyst Vertical Agent.
SQL queries + pandas analysis + Plotly charts + downloadable reports.
"""
import time
import json
import logging
from typing import Any

from backend.verticals.base                             import BaseVerticalAgent, VerticalResult
from backend.verticals.analyst.tools.sql_tool           import run_sql_query, list_tables
from backend.verticals.analyst.tools.pandas_tool        import run_pandas_analysis
from backend.verticals.analyst.tools.chart_tool         import (
    generate_chart, generate_chart_from_sql_result
)
from backend.utils.text                                  import strip_code_fence

logger = logging.getLogger(__name__)

SQL_PLANNER_PROMPT = """You are a data analyst. Given the user's question and available database tables,
write a SQL SELECT query to answer it.

Available tables: {tables}

User question: {question}

Rules:
- Only SELECT queries
- Include relevant aggregations (SUM, COUNT, AVG, GROUP BY)
- Add meaningful column aliases
- Keep it simple and focused on the question
- If question is about trends: include date/time column

Return ONLY the SQL query, no explanation."""

CHART_PLANNER_PROMPT = """Given this SQL result and user question, decide what chart to make.

Question: {question}
Columns: {columns}
Sample data: {sample}

Choose:
- chart_type: bar | line | scatter | pie | histogram
- x_column: column for x-axis
- y_column: column for y-axis
- title: descriptive chart title

Return ONLY valid JSON:
{{"chart_type": "...", "x_column": "...", "y_column": "...", "title": "..."}}"""


class DataAnalystAgent(BaseVerticalAgent):
    vertical_name = "analyst"
    description   = (
        "Expert data analyst. Queries databases, runs pandas analysis, "
        "generates Plotly charts, and produces insights reports."
    )

    @property
    def system_prompt(self) -> str:
        return """You are a Senior Data Analyst AI assistant.

Your capabilities:
- SQL queries against the production database (read-only)
- Pandas data analysis and transformations
- Plotly chart generation (bar, line, scatter, pie, histogram)
- Statistical analysis and anomaly detection

Response format:
1. **Key Insight** — one-sentence takeaway
2. **Analysis** — what the data shows
3. **Notable Findings** — specific numbers and trends
4. **Recommendations** — actionable next steps based on data

Always be specific with numbers. Avoid vague statements.
When you spot anomalies, flag them prominently."""

    async def run(
        self,
        query:          str,
        context:        dict[str, Any],
        memory_context: str = "",
    ) -> VerticalResult:
        start  = time.monotonic()
        charts = []

        # ── Step 1: Get available tables ───────────────────────────────────
        tables = await list_tables()
        tables_str = ", ".join(tables) if tables else "no tables found"

        # ── Step 2: Generate SQL query ─────────────────────────────────────
        sql_query_raw = await self._call_llm(
            user_content=SQL_PLANNER_PROMPT.format(
                tables=tables_str,
                question=query,
            ),
            temperature=0,
            max_tokens=400,
        )
        sql_query = strip_code_fence(sql_query_raw).strip()

        sql_result: dict = {}
        chart_b64: str | None = None

        if sql_query.upper().startswith("SELECT"):
            # ── Step 3: Execute SQL ────────────────────────────────────────
            sql_result = await run_sql_query(sql_query)

            if sql_result.get("error"):
                logger.warning(f"SQL failed: {sql_result['error']}")
            elif sql_result.get("rows"):
                rows    = sql_result["rows"]
                columns = sql_result["columns"]

                # ── Step 4: Decide chart type ──────────────────────────────
                sample_str = json.dumps(rows[:3], default=str)
                chart_plan_raw = await self._call_llm(
                    user_content=CHART_PLANNER_PROMPT.format(
                        question=query,
                        columns=columns,
                        sample=sample_str,
                    ),
                    temperature=0,
                    max_tokens=150,
                )
                try:
                    chart_plan = json.loads(strip_code_fence(chart_plan_raw))
                    chart_b64  = await generate_chart_from_sql_result(
                        sql_result=sql_result,
                        chart_type=chart_plan.get("chart_type", "bar"),
                        x_column=chart_plan.get("x_column", columns[0]),
                        y_column=chart_plan.get("y_column", columns[1] if len(columns) > 1 else columns[0]),
                        title=chart_plan.get("title", query[:50]),
                    )
                    if chart_b64:
                        charts.append(chart_b64)
                except (json.JSONDecodeError, Exception) as e:
                    logger.warning(f"Chart planning failed: {e}")

        # ── Step 5: Check for uploaded data ───────────────────────────────
        pandas_result = {}
        uploaded_data = context.get("uploaded_csv")
        if uploaded_data:
            pandas_code = f"""
result = df.describe()
print(result.to_string())
print(f"\\nShape: {{df.shape}}")
print(f"Missing values:\\n{{df.isnull().sum()}}")
"""
            pandas_result = await run_pandas_analysis(
                code=pandas_code,
                data_json=uploaded_data,
            )

        # ── Step 6: Synthesise insights ────────────────────────────────────
        data_summary = ""
        if sql_result.get("rows"):
            rows = sql_result["rows"]
            data_summary = (
                f"SQL query returned {len(rows)} rows.\n"
                f"Columns: {', '.join(sql_result.get('columns', []))}\n"
                f"Sample: {json.dumps(rows[:5], default=str)}"
            )

        if pandas_result.get("output"):
            data_summary += f"\n\nPandas analysis:\n{pandas_result['output'][:1000]}"

        system = self.system_prompt + (f"\n{memory_context}" if memory_context else "")
        report = await self._call_llm(
            user_content=(
                f"User question: {query}\n\n"
                f"SQL query used:\n```sql\n{sql_query}\n```\n\n"
                f"Data results:\n{data_summary}\n\n"
                f"Generate a data analysis report following your format."
            ),
            system_content=system,
            temperature=0.2,
            max_tokens=1500,
        )

        return VerticalResult(
            vertical="analyst",
            content=report,
            charts=charts,
            metadata={
                "sql_query":   sql_query,
                "rows_fetched": len(sql_result.get("rows", [])),
                "charts_generated": len(charts),
                "tables_available": tables,
            },
            latency_ms=(time.monotonic() - start) * 1000,
        )