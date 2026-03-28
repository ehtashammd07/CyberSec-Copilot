"""
/analyze endpoint — log & code security analysis.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.schemas import AnalyzeRequest, AnalyzeResponse, SeverityLevel
from app.services.analyzer import AnalyzerService, get_analyzer_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analyze", tags=["Analyze"])


@router.post(
    "",
    response_model=AnalyzeResponse,
    summary="Analyse logs or source code for security threats",
    description=(
        "Paste raw log lines or source code. The analyzer will detect attack patterns, "
        "classify severity, and return structured threat details with mitigations."
    ),
)
async def analyze(
    request: AnalyzeRequest,
    analyzer: AnalyzerService = Depends(get_analyzer_service),
) -> AnalyzeResponse:
    logger.info(
        "Analyze request — type=%s, content_len=%d",
        request.type.value,
        len(request.content),
    )

    try:
        result = await analyzer.analyze(request.content, request.type)
    except ConnectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except Exception as exc:
        logger.exception("Analysis failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis error: {exc}",
        )

    # Re-hydrate enum values from strings coming out of .model_dump()
    from app.models.schemas import ThreatDetail
    threats = [ThreatDetail(**t) for t in result["threats"]]

    return AnalyzeResponse(
        input_type=result["input_type"],
        threats=threats,
        overall_severity=SeverityLevel(result["overall_severity"]),
        summary=result["summary"],
        raw_llm_analysis=result["raw_llm_analysis"],
    )
