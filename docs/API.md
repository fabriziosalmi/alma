# API Reference

Complete REST API documentation for AI-CDN.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Currently no authentication required (development mode).
Production will use API keys or OAuth2.

## Endpoints

### Blueprints

#### List Blueprints
```http
GET /blueprints/
Query Parameters:
  - skip: int (default: 0)
  - limit: int (default: 100)
```

#### Create Blueprint
```http
POST /blueprints/
Body: SystemBlueprintCreate
```

#### Get Blueprint
```http
GET /blueprints/{id}
```

#### Update Blueprint
```http
PUT /blueprints/{id}
Body: SystemBlueprintUpdate
```

#### Delete Blueprint
```http
DELETE /blueprints/{id}
```

#### Deploy Blueprint
```http
POST /blueprints/{id}/deploy
Body: {
  "blueprint_id": int,
  "dry_run": bool,
  "engine": string (optional)
}
```

### Conversation (AI)

#### Chat
```http
POST /conversation/chat
Body: {
  "message": string,
  "context": object (optional)
}
```

#### Generate Blueprint
```http
POST /conversation/generate-blueprint
Body: {
  "description": string
}
```

#### Describe Blueprint
```http
POST /conversation/describe-blueprint
Body: {
  "blueprint": object
}
```

#### Suggest Improvements
```http
POST /conversation/suggest-improvements
Body: {
  "blueprint": object
}
```

#### Resource Sizing
```http
POST /conversation/resource-sizing
Body: {
  "workload": string,
  "expected_load": string
}
```

#### Security Audit
```http
POST /conversation/security-audit
Body: {
  "blueprint": object
}
```

### Infrastructure Pull Requests (IPR)

#### Create IPR
```http
POST /ipr/
Body: {
  "title": string,
  "description": string,
  "blueprint_id": int,
  "created_by": string
}
```

#### List IPRs
```http
GET /ipr/
Query Parameters:
  - status_filter: string (optional)
  - skip: int
  - limit: int
```

#### Get IPR
```http
GET /ipr/{id}
```

#### Update IPR
```http
PUT /ipr/{id}
```

#### Review IPR
```http
POST /ipr/{id}/review
Body: {
  "approved": bool,
  "reviewed_by": string,
  "review_comments": string (optional)
}
```

#### Deploy IPR
```http
POST /ipr/{id}/deploy
```

#### Cancel IPR
```http
DELETE /ipr/{id}
```

## Interactive Documentation

Visit `/docs` for interactive Swagger UI documentation.
Visit `/redoc` for ReDoc documentation.

---

For detailed examples, see [Examples](../examples/).
