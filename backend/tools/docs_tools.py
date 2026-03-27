"""
Docs Tools — Google Docs + Drive API.
MCP tools for the WriterAgent.
"""

from backend.tools.google_auth import get_docs_service, get_drive_service


def create_document(title: str, content: str) -> dict:
    """Create a new Google Doc with the given title and content.
    
    Args:
        title: The title of the Google Doc.
        content: The text content to populate the document with. Use newlines for formatting.
    
    Returns:
        A dict with the document ID and a shareable link.
    """
    try:
        docs_service = get_docs_service()
        drive_service = get_drive_service()

        # Step 1: Create blank document
        doc = docs_service.documents().create(body={"title": title}).execute()
        doc_id = doc.get("documentId")

        # Step 2: Insert content
        if content:
            requests_body = [
                {
                    "insertText": {
                        "location": {"index": 1},
                        "text": content,
                    }
                }
            ]
            docs_service.documents().batchUpdate(
                documentId=doc_id,
                body={"requests": requests_body},
            ).execute()

        # Step 3: Make it accessible via link
        drive_service.permissions().create(
            fileId=doc_id,
            body={"type": "anyone", "role": "reader"},
        ).execute()

        doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"

        return {
            "status": "success",
            "message": f"Document '{title}' created successfully!",
            "document_id": doc_id,
            "url": doc_url,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def list_recent_documents(max_results: int = 5) -> dict:
    """List recently created/modified Google Docs.
    
    Args:
        max_results: Maximum number of documents to return.
    
    Returns:
        A dict with a list of recent documents with title and URL.
    """
    try:
        drive_service = get_drive_service()
        results = (
            drive_service.files()
            .list(
                q="mimeType='application/vnd.google-apps.document'",
                pageSize=max_results,
                fields="files(id, name, modifiedTime, webViewLink)",
                orderBy="modifiedTime desc",
            )
            .execute()
        )

        docs = []
        for f in results.get("files", []):
            docs.append({
                "title": f.get("name", ""),
                "url": f.get("webViewLink", ""),
                "modified": f.get("modifiedTime", ""),
            })

        return {"status": "success", "documents": docs, "count": len(docs)}
    except Exception as e:
        return {"status": "error", "message": str(e)}
