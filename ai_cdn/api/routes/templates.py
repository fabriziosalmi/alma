"""API routes for blueprint templates."""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ai_cdn.core.templates import BlueprintTemplates, TemplateCategory

router = APIRouter(prefix="/templates", tags=["templates"])


class TemplateListResponse(BaseModel):
    """Response containing list of templates."""

    templates: List[Dict[str, Any]]
    count: int


class TemplateResponse(BaseModel):
    """Response containing a single template blueprint."""

    template_id: str
    blueprint: Dict[str, Any]


@router.get("/", response_model=TemplateListResponse)
async def list_templates(
    category: TemplateCategory | None = None,
    complexity: str | None = None
) -> TemplateListResponse:
    """
    Get list of all available blueprint templates.
    
    Args:
        category: Filter by category (optional)
        complexity: Filter by complexity level (optional)

    Returns:
        List of template metadata
    """
    templates = BlueprintTemplates.get_all_templates()
    
    # Apply filters
    if category:
        templates = [t for t in templates if t["category"] == category]
    
    if complexity:
        templates = [t for t in templates if t["complexity"] == complexity]
    
    return TemplateListResponse(
        templates=templates,
        count=len(templates)
    )


@router.get("/categories")
async def list_categories() -> Dict[str, List[str]]:
    """
    Get list of template categories.

    Returns:
        Available categories
    """
    return {
        "categories": [cat.value for cat in TemplateCategory]
    }


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(template_id: str) -> TemplateResponse:
    """
    Get a specific blueprint template.
    
    Args:
        template_id: Template identifier

    Returns:
        Complete blueprint template
        
    Raises:
        HTTPException: If template not found
    """
    try:
        blueprint = BlueprintTemplates.get_template(template_id)
        return TemplateResponse(
            template_id=template_id,
            blueprint=blueprint
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{template_id}/customize")
async def customize_template(
    template_id: str,
    customizations: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Customize a template with user-specific parameters.
    
    Args:
        template_id: Template to customize
        customizations: Custom parameters to apply

    Returns:
        Customized blueprint
    """
    try:
        blueprint = BlueprintTemplates.get_template(template_id)
        
        # Apply customizations
        if "name" in customizations:
            blueprint["name"] = customizations["name"]
        
        if "description" in customizations:
            blueprint["description"] = customizations["description"]
        
        # Scale resources if requested
        if "scale_factor" in customizations:
            scale = customizations["scale_factor"]
            for resource in blueprint.get("resources", []):
                if "specs" in resource:
                    specs = resource["specs"]
                    if "cpu" in specs and isinstance(specs["cpu"], (int, float)):
                        specs["cpu"] = int(specs["cpu"] * scale)
                    if "memory" in specs and isinstance(specs["memory"], str):
                        # Simple memory scaling (e.g., "4GB" -> "8GB")
                        try:
                            mem_val = int(specs["memory"].replace("GB", ""))
                            specs["memory"] = f"{int(mem_val * scale)}GB"
                        except:
                            pass
        
        # Update metadata
        blueprint.setdefault("metadata", {})
        blueprint["metadata"]["customized"] = True
        blueprint["metadata"]["base_template"] = template_id
        
        return blueprint
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/search/")
async def search_templates(
    query: str,
    limit: int = 10
) -> TemplateListResponse:
    """
    Search templates by keyword.
    
    Args:
        query: Search query
        limit: Maximum results to return

    Returns:
        Matching templates
    """
    all_templates = BlueprintTemplates.get_all_templates()
    query_lower = query.lower()
    
    # Search in name and description
    matching = [
        t for t in all_templates
        if query_lower in t["name"].lower() or query_lower in t["description"].lower()
    ]
    
    return TemplateListResponse(
        templates=matching[:limit],
        count=len(matching)
    )
