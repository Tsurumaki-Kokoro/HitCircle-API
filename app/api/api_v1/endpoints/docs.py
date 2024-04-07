from fastapi import APIRouter
from fastapi.responses import HTMLResponse

docs_router = APIRouter()


@docs_router.get("/sldocs", include_in_schema=False)
async def custom_swagger_ui_html():
    return HTMLResponse(
        """
        <!doctype html>
        <html lang="en">
          <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
            <link rel="icon" href="https://fastapi.tiangolo.com/img/favicon.png" type="image/png">
            <title>HitCircle API docs</title>
          
            <script src="static/web-components.min.js"></script>
            <link rel="stylesheet" href="static/styles.min.css">
          </head>
          <body>
            <div style="height: 100vh">
                <elements-api
                  apiDescriptionUrl="http://127.0.0.1:8900/openapi.json"
                  logo="https://fastapi.tiangolo.com/img/favicon.png"
                  router="hash"
                />
            </div>
          </body>
        </html>
        """
    )
