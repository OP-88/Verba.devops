"""
Export API routes for transcription results
Supports multiple formats: JSON, Markdown, PDF, TXT
"""

import logging
from fastapi import APIRouter, HTTPException, Query, Response
from typing import Optional, Dict, Any, List
import json
from datetime import datetime
from backend.services.database_service import DatabaseService
from backend.models.transcription_models import TranscriptionResponse
import io
import tempfile

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize database service
db_service = DatabaseService()

@router.get("/export/{transcription_id}")
async def export_transcription(
    transcription_id: str,
    format: str = Query(default="json", description="Export format: json, markdown, txt, pdf"),
    include_metadata: bool = Query(default=True, description="Include metadata in export"),
    include_speaker_labels: bool = Query(default=True, description="Include speaker diarization labels"),
    include_summary: bool = Query(default=False, description="Include AI summary if available")
):
    """
    Export transcription in specified format
    
    Args:
        transcription_id: ID of transcription to export
        format: Output format (json, markdown, txt, pdf)
        include_metadata: Whether to include metadata
        include_speaker_labels: Whether to include speaker labels
        include_summary: Whether to include summary
    """
    try:
        logger.info(f"📤 Exporting transcription {transcription_id} as {format}")
        
        # Get transcription from database
        transcription_data = await db_service.get_transcription(transcription_id)
        
        if not transcription_data:
            raise HTTPException(status_code=404, detail="Transcription not found")
        
        # Generate export content based on format
        if format.lower() == "json":
            content, media_type, filename = _export_as_json(
                transcription_data, include_metadata, include_speaker_labels, include_summary
            )
        elif format.lower() == "markdown":
            content, media_type, filename = _export_as_markdown(
                transcription_data, include_metadata, include_speaker_labels, include_summary
            )
        elif format.lower() == "txt":
            content, media_type, filename = _export_as_txt(
                transcription_data, include_metadata, include_speaker_labels, include_summary
            )
        elif format.lower() == "pdf":
            content, media_type, filename = _export_as_pdf(
                transcription_data, include_metadata, include_speaker_labels, include_summary
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
        
        logger.info(f"✅ Export completed: {filename}")
        
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": media_type
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Export failed: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


def _export_as_json(data: Dict[str, Any], include_metadata: bool, 
                   include_speaker_labels: bool, include_summary: bool) -> tuple:
    """Export as JSON format"""
    
    export_data = {
        "id": data.get("id"),
        "text": data.get("text", ""),
        "created_at": data.get("created_at"),
    }
    
    if include_metadata:
        export_data["metadata"] = {
            "duration": data.get("duration"),
            "language": data.get("language", "en"),
            "confidence": data.get("confidence"),
            "processing_time": data.get("processing_time"),
            "file_name": data.get("file_name"),
            "file_size": data.get("file_size")
        }
    
    if include_speaker_labels and "segments" in data:
        export_data["segments"] = data["segments"]
        export_data["speaker_stats"] = data.get("speaker_stats", {})
    
    if include_summary and "summary" in data:
        export_data["summary"] = data["summary"]
    
    content = json.dumps(export_data, indent=2, ensure_ascii=False)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"transcription_{data.get('id', 'unknown')}_{timestamp}.json"
    
    return content.encode('utf-8'), "application/json", filename


def _export_as_markdown(data: Dict[str, Any], include_metadata: bool, 
                       include_speaker_labels: bool, include_summary: bool) -> tuple:
    """Export as Markdown format"""
    
    lines = []
    
    # Title
    lines.append(f"# Transcription Export")
    lines.append(f"**ID:** {data.get('id', 'N/A')}")
    lines.append(f"**Date:** {data.get('created_at', 'N/A')}")
    lines.append("")
    
    # Metadata section
    if include_metadata:
        lines.append("## Metadata")
        lines.append(f"- **Duration:** {data.get('duration', 'N/A')} seconds")
        lines.append(f"- **Language:** {data.get('language', 'en')}")
        lines.append(f"- **Confidence:** {data.get('confidence', 'N/A')}")
        lines.append(f"- **Processing Time:** {data.get('processing_time', 'N/A')} seconds")
        if data.get('file_name'):
            lines.append(f"- **Original File:** {data['file_name']}")
        lines.append("")
    
    # Summary section
    if include_summary and data.get('summary'):
        lines.append("## Summary")
        summary_data = data['summary']
        lines.append(summary_data.get('summary', ''))
        lines.append("")
        
        if summary_data.get('key_points'):
            lines.append("### Key Points")
            for point in summary_data['key_points']:
                lines.append(f"- {point}")
            lines.append("")
        
        if summary_data.get('action_items'):
            lines.append("### Action Items")
            for item in summary_data['action_items']:
                lines.append(f"- [ ] {item}")
            lines.append("")
    
    # Transcript section
    lines.append("## Transcript")
    
    if include_speaker_labels and data.get('segments'):
        # Speaker-labeled transcript
        current_speaker = None
        for segment in data['segments']:
            speaker = segment.get('speaker', 'Speaker 1')
            text = segment.get('text', '').strip()
            
            if text:
                if speaker != current_speaker:
                    lines.append(f"\n**{speaker}:**")
                    current_speaker = speaker
                lines.append(text)
    else:
        # Simple transcript
        lines.append(data.get('text', ''))
    
    # Speaker statistics
    if include_speaker_labels and data.get('speaker_stats'):
        lines.append("\n## Speaker Statistics")
        stats = data['speaker_stats']
        if 'speaker_times' in stats:
            for speaker, time in stats['speaker_times'].items():
                lines.append(f"- **{speaker}:** {time:.1f} seconds")
        lines.append("")
    
    content = "\n".join(lines)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"transcription_{data.get('id', 'unknown')}_{timestamp}.md"
    
    return content.encode('utf-8'), "text/markdown", filename


def _export_as_txt(data: Dict[str, Any], include_metadata: bool, 
                  include_speaker_labels: bool, include_summary: bool) -> tuple:
    """Export as plain text format"""
    
    lines = []
    
    # Header
    lines.append("TRANSCRIPTION EXPORT")
    lines.append("=" * 50)
    lines.append(f"ID: {data.get('id', 'N/A')}")
    lines.append(f"Date: {data.get('created_at', 'N/A')}")
    lines.append("")
    
    # Metadata
    if include_metadata:
        lines.append("METADATA")
        lines.append("-" * 20)
        lines.append(f"Duration: {data.get('duration', 'N/A')} seconds")
        lines.append(f"Language: {data.get('language', 'en')}")
        lines.append(f"Confidence: {data.get('confidence', 'N/A')}")
        if data.get('file_name'):
            lines.append(f"Original File: {data['file_name']}")
        lines.append("")
    
    # Summary
    if include_summary and data.get('summary'):
        lines.append("SUMMARY")
        lines.append("-" * 20)
        lines.append(data['summary'].get('summary', ''))
        lines.append("")
    
    # Transcript
    lines.append("TRANSCRIPT")
    lines.append("-" * 20)
    
    if include_speaker_labels and data.get('segments'):
        current_speaker = None
        for segment in data['segments']:
            speaker = segment.get('speaker', 'Speaker 1')
            text = segment.get('text', '').strip()
            
            if text:
                if speaker != current_speaker:
                    lines.append(f"\n{speaker}:")
                    current_speaker = speaker
                lines.append(text)
    else:
        lines.append(data.get('text', ''))
    
    content = "\n".join(lines)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"transcription_{data.get('id', 'unknown')}_{timestamp}.txt"
    
    return content.encode('utf-8'), "text/plain", filename


def _export_as_pdf(data: Dict[str, Any], include_metadata: bool, 
                  include_speaker_labels: bool, include_summary: bool) -> tuple:
    """Export as PDF format using simple text-based PDF generation"""
    
    try:
        # Try to use reportlab for better PDF generation
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=20,
            textColor=colors.darkblue,
            spaceAfter=20
        )
        
        story.append(Paragraph("Transcription Export", title_style))
        story.append(Paragraph(f"ID: {data.get('id', 'N/A')}", styles['Normal']))
        story.append(Paragraph(f"Date: {data.get('created_at', 'N/A')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Metadata section
        if include_metadata:
            story.append(Paragraph("Metadata", styles['Heading2']))
            story.append(Paragraph(f"Duration: {data.get('duration', 'N/A')} seconds", styles['Normal']))
            story.append(Paragraph(f"Language: {data.get('language', 'en')}", styles['Normal']))
            if data.get('file_name'):
                story.append(Paragraph(f"Original File: {data['file_name']}", styles['Normal']))
            story.append(Spacer(1, 15))
        
        # Summary section
        if include_summary and data.get('summary'):
            story.append(Paragraph("Summary", styles['Heading2']))
            story.append(Paragraph(data['summary'].get('summary', ''), styles['Normal']))
            story.append(Spacer(1, 15))
        
        # Transcript section
        story.append(Paragraph("Transcript", styles['Heading2']))
        
        if include_speaker_labels and data.get('segments'):
            speaker_style = ParagraphStyle(
                'Speaker',
                parent=styles['Normal'],
                fontName='Helvetica-Bold',
                fontSize=12,
                textColor=colors.darkblue,
                spaceAfter=5
            )
            
            current_speaker = None
            for segment in data['segments']:
                speaker = segment.get('speaker', 'Speaker 1')
                text = segment.get('text', '').strip()
                
                if text:
                    if speaker != current_speaker:
                        story.append(Paragraph(f"{speaker}:", speaker_style))
                        current_speaker = speaker
                    story.append(Paragraph(text, styles['Normal']))
        else:
            story.append(Paragraph(data.get('text', ''), styles['Normal']))
        
        # Build PDF
        doc.build(story)
        content = buffer.getvalue()
        buffer.close()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"transcription_{data.get('id', 'unknown')}_{timestamp}.pdf"
        
        return content, "application/pdf", filename
        
    except ImportError:
        # Fallback to simple text-based approach
        logger.warning("ReportLab not available, using text-based PDF fallback")
        
        # Create simple text content and return as PDF-like format
        content, _, _ = _export_as_txt(data, include_metadata, include_speaker_labels, include_summary)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"transcription_{data.get('id', 'unknown')}_{timestamp}.txt"
        
        return content, "text/plain", filename


@router.get("/export/{transcription_id}/preview")
async def preview_export(
    transcription_id: str,
    format: str = Query(default="markdown", description="Preview format")
):
    """
    Get a preview of the export without downloading
    """
    try:
        transcription_data = await db_service.get_transcription(transcription_id)
        
        if not transcription_data:
            raise HTTPException(status_code=404, detail="Transcription not found")
        
        # Generate preview (limit content length)
        if format.lower() == "markdown":
            content, _, _ = _export_as_markdown(transcription_data, True, True, True)
            content = content.decode('utf-8')[:2000] + "..." if len(content) > 2000 else content.decode('utf-8')
        elif format.lower() == "txt":
            content, _, _ = _export_as_txt(transcription_data, True, True, True)
            content = content.decode('utf-8')[:2000] + "..." if len(content) > 2000 else content.decode('utf-8')
        else:
            content, _, _ = _export_as_json(transcription_data, True, True, True)
            content = content.decode('utf-8')[:2000] + "..." if len(content) > 2000 else content.decode('utf-8')
        
        return {"preview": content, "format": format}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Preview failed: {e}")
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")