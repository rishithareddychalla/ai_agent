"""
Report Generator – Creates PDF, CSV, and JSON reports from task results
"""

import csv
import json
import io
import os
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from loguru import logger

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    Image as RLImage,
    PageBreak,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

from app.core.config import settings


class ReportGenerator:
    """
    Generates downloadable reports in PDF, CSV, and JSON formats.
    
    Each report includes:
    - Task prompt and AI understanding
    - Execution plan with step results
    - Websites visited timeline
    - Extracted data
    - Final recommendation
    - Screenshots (PDF only)
    - Metrics (execution time, success rate)
    """

    def __init__(self, reports_dir: str = None):
        self.reports_dir = reports_dir or settings.REPORTS_DIR
        os.makedirs(self.reports_dir, exist_ok=True)

    async def generate_pdf(
        self,
        task_id: int,
        prompt: str,
        plan: dict,
        results: List[dict],
        extracted_data: dict,
        summary: str,
        recommendation: str,
        metrics: dict,
        screenshots: Optional[List[str]] = None,
    ) -> str:
        """
        Generate a PDF report.
        
        Returns:
            Absolute path to the generated PDF file
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"webpilot_report_{task_id}_{timestamp}.pdf"
        filepath = os.path.join(self.reports_dir, filename)
        
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=1 * inch,
            bottomMargin=1 * inch,
        )
        
        styles = getSampleStyleSheet()
        story = []
        
        # ─── Title Page ──────────────────────────────────────
        title_style = ParagraphStyle(
            "WebPilotTitle",
            parent=styles["Title"],
            fontSize=28,
            spaceAfter=6,
            textColor=colors.HexColor("#6366f1"),
            fontName="Helvetica-Bold",
        )
        subtitle_style = ParagraphStyle(
            "WebPilotSubtitle",
            parent=styles["Normal"],
            fontSize=12,
            textColor=colors.HexColor("#64748b"),
            spaceAfter=30,
        )
        heading_style = ParagraphStyle(
            "WebPilotHeading",
            parent=styles["Heading1"],
            fontSize=16,
            textColor=colors.HexColor("#1e293b"),
            fontName="Helvetica-Bold",
            spaceBefore=20,
            spaceAfter=8,
            borderPad=4,
        )
        body_style = ParagraphStyle(
            "WebPilotBody",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#374151"),
            spaceAfter=6,
            leading=14,
        )
        
        story.append(Paragraph("🤖 WebPilot AI", title_style))
        story.append(Paragraph("Autonomous Browser Agent – Task Report", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#6366f1")))
        story.append(Spacer(1, 20))
        
        # ─── Task Information ────────────────────────────────
        story.append(Paragraph("Task Overview", heading_style))
        
        info_data = [
            ["Task ID", str(task_id)],
            ["Generated", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")],
            ["Execution Time", f"{metrics.get('execution_time_ms', 0) / 1000:.1f}s"],
            ["Success Rate", f"{metrics.get('success_rate', 0) * 100:.0f}%"],
            ["Steps Completed", f"{metrics.get('steps_completed', 0)} / {metrics.get('total_steps', 0)}"],
            ["Websites Visited", str(metrics.get('websites_count', 0))],
        ]
        
        info_table = Table(info_data, colWidths=[2 * inch, 4 * inch])
        info_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#475569")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 15))
        
        # ─── User Prompt ────────────────────────────────────
        story.append(Paragraph("User Request", heading_style))
        story.append(Paragraph(f'<i>"{prompt}"</i>', ParagraphStyle(
            "Quote",
            parent=styles["Normal"],
            fontSize=12,
            textColor=colors.HexColor("#4f46e5"),
            leftIndent=20,
            rightIndent=20,
            backColor=colors.HexColor("#eef2ff"),
            borderPad=10,
            spaceAfter=10,
        )))
        
        # ─── AI Understanding ────────────────────────────────
        if plan.get("task_understanding"):
            story.append(Paragraph("AI Understanding", heading_style))
            story.append(Paragraph(plan["task_understanding"], body_style))
        
        # ─── Execution Plan ──────────────────────────────────
        story.append(Paragraph("Execution Steps", heading_style))
        
        steps = plan.get("steps", [])
        for i, step in enumerate(steps):
            step_result = results[i] if i < len(results) else {}
            status_icon = "✅" if step_result.get("success") else "❌"
            duration = f"{step_result.get('duration_ms', 0):.0f}ms"
            
            step_text = f"{status_icon} <b>Step {i + 1}:</b> {step.get('description', '')} <i>({duration})</i>"
            story.append(Paragraph(step_text, body_style))
        
        story.append(Spacer(1, 10))
        
        # ─── Summary ────────────────────────────────────────
        story.append(Paragraph("Summary", heading_style))
        story.append(Paragraph(summary or "Task completed.", body_style))
        
        # ─── Recommendation ─────────────────────────────────
        if recommendation:
            story.append(Paragraph("AI Recommendation", heading_style))
            rec_style = ParagraphStyle(
                "Recommendation",
                parent=styles["Normal"],
                fontSize=11,
                textColor=colors.HexColor("#166534"),
                backColor=colors.HexColor("#f0fdf4"),
                borderPad=12,
                leftIndent=10,
                spaceAfter=10,
            )
            story.append(Paragraph(recommendation, rec_style))
        
        # ─── Extracted Data ──────────────────────────────────
        if extracted_data:
            story.append(PageBreak())
            story.append(Paragraph("Extracted Data", heading_style))
            
            for key, value in extracted_data.items():
                if isinstance(value, list) and value:
                    story.append(Paragraph(f"<b>{key}:</b>", body_style))
                    for item in value[:10]:
                        if isinstance(item, dict):
                            item_str = " | ".join(f"{k}: {v}" for k, v in item.items())
                        else:
                            item_str = str(item)
                        story.append(Paragraph(f"  • {item_str[:200]}", body_style))
                elif value:
                    story.append(Paragraph(f"<b>{key}:</b> {str(value)[:300]}", body_style))
        
        # ─── Footer ─────────────────────────────────────────
        story.append(Spacer(1, 30))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0")))
        story.append(Paragraph(
            f"Generated by WebPilot AI · {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#94a3b8"), alignment=TA_CENTER),
        ))
        
        doc.build(story)
        logger.info(f"PDF report generated: {filepath}")
        return filepath

    async def generate_csv(
        self,
        task_id: int,
        prompt: str,
        results: List[dict],
        extracted_data: dict,
    ) -> str:
        """Generate a CSV report."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"webpilot_report_{task_id}_{timestamp}.csv"
        filepath = os.path.join(self.reports_dir, filename)
        
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow(["WebPilot AI Report"])
            writer.writerow(["Task ID", task_id])
            writer.writerow(["Prompt", prompt])
            writer.writerow(["Generated", datetime.now(timezone.utc).isoformat()])
            writer.writerow([])
            
            # Execution steps
            writer.writerow(["Step", "Action", "Description", "Success", "Duration (ms)", "URL", "Error"])
            for r in results:
                writer.writerow([
                    r.get("step_index", ""),
                    r.get("action", ""),
                    r.get("description", ""),
                    r.get("success", ""),
                    f"{r.get('duration_ms', 0):.0f}",
                    r.get("url", ""),
                    r.get("error", ""),
                ])
            
            writer.writerow([])
            writer.writerow(["Extracted Data"])
            
            # Extracted data
            for key, value in extracted_data.items():
                if isinstance(value, list):
                    writer.writerow([key, f"{len(value)} items"])
                    for item in value[:20]:
                        writer.writerow(["", str(item)[:500]])
                else:
                    writer.writerow([key, str(value)[:500]])
        
        logger.info(f"CSV report generated: {filepath}")
        return filepath

    async def generate_json(
        self,
        task_id: int,
        prompt: str,
        plan: dict,
        results: List[dict],
        extracted_data: dict,
        summary: str,
        recommendation: str,
        metrics: dict,
    ) -> str:
        """Generate a JSON report."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"webpilot_report_{task_id}_{timestamp}.json"
        filepath = os.path.join(self.reports_dir, filename)
        
        report_data = {
            "webpilot_version": "1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "task": {
                "id": task_id,
                "prompt": prompt,
                "ai_understanding": plan.get("task_understanding", ""),
                "goal": plan.get("goal", ""),
                "approach": plan.get("approach", ""),
            },
            "metrics": metrics,
            "execution_plan": plan.get("steps", []),
            "step_results": results,
            "extracted_data": extracted_data,
            "summary": summary,
            "recommendation": recommendation,
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, default=str)
        
        logger.info(f"JSON report generated: {filepath}")
        return filepath
